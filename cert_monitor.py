# cert_monitor.py
"""
Kubernetes / K3s / MicroK8s Certificate Expiry Monitor
This script checks various Kubernetes clusters to see if their security certificates are about to expire.
If any certificate is close to expiring (within 5 days), it can send an alert to a Google Chat room.
"""

import json
import paramiko
import subprocess
from datetime import datetime, timedelta
import re
import os
import requests
from typing import List, Dict, Any

# CONFIGURATION
# This is the file that contains the list of clusters/servers to check.
CONFIG_FILE = os.getenv("CERT_MONITOR_CONFIG", "clusters.json")

# We will send an alert if a certificate expires in these many days or less.
# Alert 7 days before expiry (e.g., expires on 20th → notify on 13th)
ALERT_THRESHOLD_DAYS = int(os.getenv("CERT_MONITOR_THRESHOLD", 7))

# Your Google Chat Webhook URL goes here. 
# To get this: Go to Google Chat -> Room Name -> Apps & Widgets -> Webhooks
GOOGLE_CHAT_WEBHOOK_URL = os.getenv("CERT_MONITOR_WEBHOOK", "ADD YOUR URL") 

# A simple separator line used for printing to the console.
DOT_LINE = "." * 86


def load_clusters() -> List[Dict[str, Any]]:
    """
    This function reads the 'clusters.json' file.
    Think of it as opening a list of all the servers we need to keep an eye on.
    """
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The configuration file '{CONFIG_FILE}' was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: The configuration file '{CONFIG_FILE}' contains invalid JSON.")
        return []


def run_local_command(cmd: str) -> str:
    """
    This function runs a command on your OWN computer (the one running this script).
    It's like typing a command into your own terminal and getting the result back.
    """
    try:
        # We run the command and wait for it to finish (up to 30 seconds).
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        # We return both the normal output and any error messages.
        return result.stdout + result.stderr
    except Exception as e:
        return f"[LOCAL ERROR] {str(e)}"


def run_ssh_command(client: paramiko.SSHClient, cmd: str) -> str:
    """
    This function runs a command on a REMOTE server using a secure connection (SSH).
    It's like sending a remote control command to another computer across the network.
    """
    try:
        # We send the command and read the response.
        stdin, stdout, stderr = client.exec_command(cmd)
        return stdout.read().decode("utf-8", errors="replace") + stderr.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"[REMOTE ERROR] Failed to run command: {str(e)}"


def create_ssh_client(ip: str, user: str, key_path: str) -> paramiko.SSHClient:
    """
    This function sets up a "tunnel" (SSH connection) to a remote server.
    It uses a security key (ssh_key_path) to prove who we are so the server lets us in.
    """
    client = paramiko.SSHClient()
    # This line tells the computer to trust the server even if we haven't talked to it before.
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Check if the security key file actually exists on your computer.
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"SSH Key not found at: {key_path}")

    # Force using Ed25519Key explicitly and pass password=None
    try:
        key = paramiko.Ed25519Key.from_private_key_file(key_path, password=None)
        # Connect to the server using the IP address, username, and key.
        client.connect(hostname=ip, username=user, pkey=key, timeout=15,
                       allow_agent=False, look_for_keys=False)
        return client
    except paramiko.AuthenticationException:
        # The server said "No, I don't recognize this key for this user".
        raise ConnectionError(f"SSH AUTH FAILURE: The server {ip} rejected the public key for user '{user}'.")
    except paramiko.ssh_exception.NoValidConnectionsError:
        # We couldn't even find the server on the network.
        raise ConnectionError(f"SSH NETWORK FAILURE: Could not connect to {ip}. Check firewall/VPN.")
    except Exception as e:
        raise ConnectionError(f"SSH FAILURE: Unable to connect to {ip}: {str(e)}")


def parse_microk8s_cert_check(output: str) -> List[Dict[str, Any]]:
    """
    This function reads text from a MicroK8s server and looks for certificate expiry dates.
    It uses "Regular Expressions" (re) to hunt for specific phrases like "expire in X days".
    """
    certs = []
    for line in output.splitlines():
        # We look for a pattern like "The [name] certificate will expire in [number] days."
        match = re.search(r"The (.+?)(?: certificate|CA) will expire in (\d+) days?\.", line.strip())
        if match:
            cert_type = match.group(1).strip()
            days_left = int(match.group(2))
            # Calculate the actual date based on today's date + days remaining.
            expiry_date = (datetime.now().date() + timedelta(days=days_left)).isoformat()
            certs.append({"type": cert_type, "days_left": days_left, "expiry": expiry_date})
    return certs


def parse_kubeadm_cert_expiration(output: str) -> List[Dict[str, Any]]:
    """
    This function reads text from a standard Kubernetes (kubeadm) server.
    It looks for a table in the output that lists certificates and their expiration dates.
    """
    certs = []
    parsing = False
    for line in output.splitlines():
        line = line.strip()
        # We wait until we see the header "CERTIFICATE" and "EXPIRES".
        if "CERTIFICATE" in line and "EXPIRES" in line:
            parsing = True
            continue
        # If we are in the table, we pull out the name and the date from each line.
        if parsing and line and not line.startswith(("---", "[")):
            parts = re.split(r'\s{2,}', line) # Split by 2 or more spaces.
            if len(parts) >= 3:
                cert_name = parts[0]
                expiry_str = parts[1]
                try:
                    # Convert the date text (like "Jan 01, 2025") into a computer-readable date.
                    expiry = datetime.strptime(expiry_str, "%b %d, %Y %H:%M %Z")
                    days_left = (expiry - datetime.now()).days
                    certs.append({
                        "type": cert_name,
                        "days_left": days_left,
                        "expiry": expiry.date().isoformat()
                    })
                except ValueError:
                    pass
    return certs


def parse_k3s_cert_output(output: str) -> List[Dict[str, Any]]:
    """
    This function reads text from a K3s server.
    It looks for 'File:' markers and 'notAfter=' dates which show when a certificate file expires.
    """
    certs = []
    current_file = None
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("File: "):
            current_file = line.replace("File: ", "").strip()
            # Get the filename to use as the name of the certificate.
            cert_type = current_file.split("/")[-1].replace(".crt", "") if current_file else "unknown"
            continue
        if "notAfter=" in line:
            try:
                # Extract the date part after 'notAfter='.
                expiry_str = line.split("notAfter=")[1].strip()
                expiry = datetime.strptime(expiry_str, "%b %d %H:%M:%S %Y %Z")
                days_left = (expiry - datetime.now()).days
                certs.append({
                    "type": cert_type,
                    "days_left": days_left,
                    "expiry": expiry.date().isoformat()
                })
            except ValueError:
                pass
    return certs


def send_to_google_chat(text: str) -> bool:
    """
    This function behaves like a postman. It takes a message and delivers it to your Google Chat room.
    If the delivery fails, it tells us why (e.g., wrong URL or network issue).
    """
    if not GOOGLE_CHAT_WEBHOOK_URL:
        print("Webhook URL not set → message not sent")
        return False

    payload = {"text": text}
    # These headers tell Google Chat we are sending JSON data in UTF-8 format.
    headers = {"Content-Type": "application/json; charset=UTF-8"}

    try:
        # We 'POST' the message to the URL.
        response = requests.post(GOOGLE_CHAT_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        if response.status_code in (200, 201):
            print("-> Message sent to Google Chat")
            return True
        else:
            print(f"Failed: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"Exception sending to Chat: {e}")
        return False


def check_cluster(cluster: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    This is the main logic for checking a SINGLE cluster.
    It connects to the server, runs the right command for its type, and collects the results.
    """
    name = cluster["name"]
    ip = cluster["ip"]
    user = cluster.get("ssh_user", "")
    key_path = cluster["ssh_key_path"]
    cluster_type = cluster["type"]
    env = cluster.get("env", "unknown")

    print(f"\n{name} ({env}) @ {ip} -- {cluster_type}")
    print(DOT_LINE)

    results = []

    try:
        # Decide if we run locally (on this PC) or remotely (via SSH).
        if ip in ("localhost", "127.0.0.1", "::1"):
            runner = run_local_command
        else:
            client = create_ssh_client(ip, user, key_path)
            runner = lambda c: run_ssh_command(client, c)

        # Run the command based on what type of cluster it is (MicroK8s, K3s, or standard K8s).
        if cluster_type == "microk8s":
            output = runner("sudo microk8s refresh-certs --check")
            parsed = parse_microk8s_cert_check(output)

        elif cluster_type in ("kubernetes", "kubeadm"):
            output = runner("sudo kubeadm certs check-expiration")
            parsed = parse_kubeadm_cert_expiration(output)

        elif cluster_type == "k3s":
            output = runner("sudo k3s certificate check")
            # If the k3s command doesn't exist, we try to find the files manually.
            if "command not found" in output.lower() or "unknown" in output.lower():
                output = runner("sudo find /var/lib/rancher/k3s/server/tls -name '*.crt' -exec openssl x509 -in {} -noout -dates \\; -exec echo 'File: {}' \\;")
            parsed = parse_k3s_cert_output(output)

        else:
            parsed = []

        # If we found certificates, print them to the screen and save them for the report.
        if parsed:
            print("Certificates:")
            for cert in parsed:
                days = cert["days_left"]
                # Give a different label based on how close it is to expiring.
                status = "OK" if days > 30 else f"WARNING ({days}d)" if days > 5 else f"URGENT ({days}d)"
                print(f"  • {cert['type']:<24} {status:<18} expires {cert['expiry']}")
                results.append({
                    "cluster": name,
                    "env": env,
                    "ip": ip,
                    "type": cluster_type,
                    "cert": cert["type"],
                    "days": days,
                    "expiry": cert["expiry"]
                })
        else:
            print("  No certificate information parsed")

        print(DOT_LINE)

        # Always close the SSH connection when we are done.
        if 'client' in locals():
            client.close()

    except Exception as e:
        print(f"  ERROR: {str(e)}")
        print(DOT_LINE)

    return results


def main():
    """
    This is the starting point of the script.
    It loads the list of clusters, checks each one, and sends ONE summarized alert.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"CERTIFICATE EXPIRY CHECK - {today}\n")

    # 1. Load the clusters from the file.
    clusters = load_clusters()
    if not clusters:
        print("No clusters to check. Exiting.")
        return

    print(f"{len(clusters)} cluster(s) loaded\n")

    all_certs = []

    # 2. Check each cluster one by one.
    for cluster in clusters:
        cluster_certs = check_cluster(cluster)
        all_certs.extend(cluster_certs)

    # 3. Filter for certificates that are NOT long-term CAs and are within our threshold.
    # We filter out 'CA' to specifically show 'server' and 'front proxy client' as requested.
    urgent = [c for c in all_certs if c["days"] <= ALERT_THRESHOLD_DAYS and "CA" not in c["cert"].upper()]

    # 4. If we found issues, send separate messages for each cluster.
    if urgent:
        print(f"\nURGENT ALERTS FOUND ({len(urgent)}) - preparing individual alerts for Google Chat")

        # Group certificates by cluster
        clusters_found = {}
        for cert in urgent:
            c_name = cert['cluster']
            if c_name not in clusters_found:
                clusters_found[c_name] = []
            clusters_found[c_name].append(cert)

        # Send a separate message for EACH cluster
        for cluster_name, certs in clusters_found.items():
            # Create a list like "`server`, `front proxy client`"
            cert_names = ", ".join([f"`{c['cert']}`" for c in certs])
            env = certs[0]['env']
            ip = certs[0]['ip']
            
            # Use the earliest expiry date found for this cluster in the header
            expiry_date = certs[0]['expiry']
            days_left = certs[0]['days']

            cluster_msg = (
                f"🚨 *CERTIFICATE EXPIRY ALERT: {cluster_name}* 🚨\n\n"
                f"• *Environment:* {env}\n"
                f"• *Server:* {ip}\n"
                f"• *Certificates:* {cert_names}\n"
                f"• *Expires In:* `{days_left} days` ({expiry_date})\n\n"
                f"Please plan for renewal soon to avoid disruption."
            )

            # Send the message for this specific cluster
            send_to_google_chat(cluster_msg)
            print(f"-> Alert sent for {cluster_name}")
        
    else:
        print(f"All relevant certificates are OK.")


if __name__ == "__main__":
    main()
