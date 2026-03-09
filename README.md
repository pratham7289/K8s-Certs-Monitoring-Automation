# 🛡️ Kubernetes Certificate Expiry Monitor

> **Automated, Zero-Footprint Certificate Monitoring & Alerting for Multi-Distribution K8s Clusters**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Multi--Distribution-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?style=for-the-badge&logo=jenkins&logoColor=white)](https://www.jenkins.io/)
[![Google Chat](https://img.shields.io/badge/Google%20Chat-Alerts-00AC47?style=for-the-badge&logo=googlechat&logoColor=white)](https://chat.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

---

## 📋 Overview

**Cert Monitor** is a lightweight, agentless Python automation tool that daily audits the health of X.509 security certificates across your entire Kubernetes fleet — covering **kubeadm**, **K3s**, and **MicroK8s** distributions.

When any certificate is within the configured expiry window, the system **automatically fires a formatted alert directly to your Google Chat room** — with full context, so your team can act before any outage occurs.

> No agents deployed. No dashboards to check. No manual SSH sessions. Just automated, daily peace of mind.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔍 **Multi-Distribution** | Supports `kubeadm`, `K3s`, and `MicroK8s` clusters natively |
| 🚫 **Agentless** | Zero software installed on cluster nodes — pure SSH + native commands |
| 🏢 **Centralized** | Monitor 1 to 100+ clusters from a single Jenkins pipeline |
| ⚡ **Early Alerts** | Notifies your team days before expiry — not after the outage |
| 💬 **ChatOps** | Sends rich, actionable alerts directly to Google Chat |
| 🔒 **Secure** | Uses Ed25519 SSH keys — no passwords, no plaintext secrets |
| ⚙️ **Configurable** | Threshold, webhook, and cluster inventory are all externally configurable |
| 🤖 **Fully Automated** | Runs daily via Jenkins CRON — completely unattended |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   GitHub Repository          Jenkins Pipeline (Daily CRON)     │
│   ─────────────────   ─────►  ───────────────────────────────  │
│   cert_monitor.py             Agent: SlaveNode01               │
│   clusters.json               Trigger: H 9 * * *              │
│   requirements.txt                        │                    │
│                                           │ SSH (Ed25519)      │
│              ┌────────────────────────────┤                    │
│              │                            │                    │
│   ┌──────────▼──────┐  ┌────────────────▼──┐  ┌────────────┐ │
│   │  Getpay-Dev-Qa  │  │    NCHL-UAT        │  │  MBL-UAT  │ │
│   │  (kubeadm)      │  │    (MicroK8s)      │  │  (K3s)    │ │
│   └─────────────────┘  └───────────────────┘  └────────────┘ │
│              │                            │           │        │
│         kubeadm certs             microk8s        k3s cert     │
│         check-expiration          refresh-certs   / openssl    │
│              └────────────────────────────┴───────────┘        │
│                                           │                    │
│                                   Parse → Evaluate             │
│                                           │                    │
│                            days_left ≤ ALERT_THRESHOLD_DAYS?   │
│                                           │ YES                │
│                                    HTTP POST ──► Google Chat   │
│                                               DevOps Room      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
📦 Cluster-Cert-Alerting/
├── 📄 cert_monitor.py       # Core monitoring and alerting script
├── 📄 clusters.json         # Cluster inventory & connection config
├── 📄 requirements.txt      # Python dependencies
├── 📄 Jenkinsfile           # Declarative Jenkins pipeline
└── 📄 README.md             # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- SSH access to each cluster's master node (key-based, no password)
- A Google Chat space with a configured Webhook

### 1. Clone the Repository

```bash
git clone https://github.com/city-tech/Cluster-Cert-Alerting.git
cd Cluster-Cert-Alerting
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Your Clusters

Edit `clusters.json` to define your cluster inventory:

```json
[
  {
    "name": "Production-Cluster",
    "type": "kubernetes",
    "ip": "10.0.0.50",
    "ssh_user": "admin",
    "ssh_key_path": "/home/user/.ssh/id_ed25519_certmonitor",
    "env": "PROD"
  },
  {
    "name": "UAT-MicroK8s",
    "type": "microk8s",
    "ip": "10.0.3.200",
    "ssh_user": "mms_test",
    "ssh_key_path": "/home/user/.ssh/id_ed25519_certmonitor",
    "env": "UAT"
  },
  {
    "name": "Banking-K3s",
    "type": "k3s",
    "ip": "10.43.34.95",
    "ssh_user": "finpos",
    "ssh_key_path": "/home/user/.ssh/id_ed25519_certmonitor",
    "env": "UAT"
  }
]
```

> ⚠️ **Important:** JSON must be strictly valid — no comments (`//`), no trailing commas.

### 4. Set Your Google Chat Webhook

Set it as an environment variable (recommended):

```bash
export CERT_MONITOR_WEBHOOK="https://chat.googleapis.com/v1/spaces/YOUR_SPACE/messages?key=..."
```

Or edit directly in `cert_monitor.py`:

```python
GOOGLE_CHAT_WEBHOOK_URL = "https://chat.googleapis.com/..."
```

### 5. Run the Monitor

```bash
python3 cert_monitor.py
```

---

## ⚙️ Configuration Reference

| Variable | Description | Default |
|---|---|---|
| `ALERT_THRESHOLD_DAYS` | Alert threshold in days before expiry | `7` |
| `CERT_MONITOR_CONFIG` | Path to the cluster inventory JSON file | `clusters.json` |
| `CERT_MONITOR_WEBHOOK` | Google Chat Webhook URL for alerts | *(required)* |

All three can be overridden at runtime via **environment variables** — no code changes needed.

---

## 📊 How It Works

The script follows a strict 6-step cycle for every cluster on each run:

```
1. LOAD      →  Read clusters.json inventory
2. CONNECT   →  Establish SSH tunnel (Ed25519 key, no password)
3. INSPECT   →  Run native cert check command for cluster type
4. PARSE     →  Extract cert name, expiry date, days remaining
5. EVALUATE  →  Compare days_left against ALERT_THRESHOLD_DAYS
6. ALERT     →  POST formatted message to Google Chat (if urgent)
```

### Supported Commands Per Distribution

| Distribution | Command Executed |
|---|---|
| `kubernetes` / `kubeadm` | `sudo kubeadm certs check-expiration` |
| `microk8s` | `sudo microk8s refresh-certs --check` |
| `k3s` | `sudo k3s certificate check` *(falls back to `openssl` if unavailable)* |

### Certificate Status Levels

| Status | Condition | Action |
|---|---|---|
| ✅ **OK** | `days > 30` | Logged to console only |
| ⚠️ **WARNING** | `5 < days ≤ 30` | Logged to console only |
| 🚨 **URGENT** | `days ≤ threshold` | Alert sent to Google Chat |

> Root CAs (long-lived, 10+ year certs) are automatically **excluded** from alerts to prevent noise.

---

## 💬 Sample Alert (Google Chat)

```
🚨 CERTIFICATE EXPIRY ALERT: Getpay-Dev-Qa 🚨

• Environment:   getpay-dev-qa
• Server:        10.20.30.141
• Certificates:  `apiserver`, `front-proxy-client`
• Expires In:    3 days (2026-02-01)

Please plan for renewal soon to avoid disruption.
```

---

## 🔐 SSH Key Setup

Generate a dedicated Ed25519 key for this automation:

```bash
# Generate the key (Linux/macOS)
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_certmonitor -N ""

# Authorize it on each cluster master
ssh-copy-id -i ~/.ssh/id_ed25519_certmonitor.pub user@<cluster-ip>

# Verify passwordless access
ssh -i ~/.ssh/id_ed25519_certmonitor user@<cluster-ip> whoami
```

```powershell
# Generate the key (Windows PowerShell)
ssh-keygen -t ed25519 -f "$HOME\.ssh\id_ed25519_certmonitor" -N '""'
```

> 🔒 Set correct permissions: `chmod 600 ~/.ssh/id_ed25519_certmonitor`

---

## 🤖 Jenkins Automation

The included `Jenkinsfile` runs this monitor as a daily scheduled job:

```groovy
triggers {
    cron('H 9 * * *')   // Runs daily around 9 AM
}
```

**Pipeline Stages:**
1. `Checkout Repo` — Pulls latest code from GitHub (`main` branch)
2. `Install Dependencies` — Runs `pip install -r requirements.txt`
3. `Run Certificate Check` — Executes `python3 cert_monitor.py`

**Required Jenkins Credentials:**

| ID | Type | Purpose |
|---|---|---|
| `github-hardened-token` | Username + Token | GitHub repo checkout |
| `mbl-uat-ssh-password` | Username + Password | SSH password cluster (MBL-UAT) |

---

## 🧪 Testing the Alerts

To force-trigger a Google Chat alert during testing (without waiting for real expiry):

```bash
# Temporarily raise the threshold to catch all certificates
export CERT_MONITOR_THRESHOLD=330
python3 cert_monitor.py
```

Restore to production value afterward:

```bash
export CERT_MONITOR_THRESHOLD=7
```

---

## 📈 Console Output Example

```
CERTIFICATE EXPIRY CHECK - 2026-01-28

2 cluster(s) loaded

Getpay-Dev-Qa (getpay-dev-qa) @ 10.20.30.141 -- kubernetes
......................................................................................
Certificates:
  • apiserver               OK                 expires 2027-01-15
  • apiserver-kubelet-client OK                expires 2027-01-15
  • front-proxy-client      WARNING (25d)      expires 2026-02-22
  • admin.conf              URGENT (3d)        expires 2026-02-01
......................................................................................
-> Alert sent for Getpay-Dev-Qa
```

---

## 🗺️ Roadmap

- [x] Multi-distribution support (kubeadm, MicroK8s, K3s)
- [x] Google Chat alerting via Webhook
- [x] Jenkins CRON pipeline
- [x] Ed25519 SSH key authentication
- [ ] Migrate SSH keys to Jenkins `sshagent` plugin
- [ ] Add email/Slack fallback notifications
- [ ] Add retry logic and connection timeout handling
- [ ] Restore NCHL-UAT cluster (pending network/firewall fix)
- [ ] Expand to all 15 clusters

---

## 📝 FAQ

**Q: Does this install anything on my clusters?**  
A: No. All checks are performed passively over SSH using native OS commands.

**Q: What Kubernetes distributions are supported?**  
A: Standard Kubernetes (kubeadm), MicroK8s, and K3s — all in the same run.

**Q: Where do the alerts go?**  
A: Directly to your configured Google Chat space via Webhook.

**Q: Does it alert on root CA certificates?**  
A: No. Root CAs (10+ year certs) are automatically filtered out to suppress noise.

**Q: Can I monitor clusters on different subnets/VPNs?**  
A: Yes — as long as the Jenkins agent has SSH connectivity to the cluster master nodes.

---

## 👥 Authors & Credits

| Name | Role |
|---|---|
| **Pratham Sharma** | Author & DevOps Engineer |
| **Citytech System Team** | Infrastructure & Operations |

---

> Built with ❤️ by **Citytech System Team** — Powered by **Antigravity AI**
