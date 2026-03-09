<div align="center">

# 🛡️ Kubernetes Certificate Expiry Monitor

### Automated · Agentless · Multi-Distribution · ChatOps-Ready

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Multi--Distribution-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?style=for-the-badge&logo=jenkins&logoColor=white)](https://www.jenkins.io/)
[![Google Chat](https://img.shields.io/badge/Google%20Chat-Alerts-00AC47?style=for-the-badge&logo=googlechat&logoColor=white)](https://chat.google.com/)
[![SSH](https://img.shields.io/badge/SSH-Ed25519-black?style=for-the-badge&logo=openssh&logoColor=white)](https://www.openssh.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-F7DF1E?style=for-the-badge)](LICENSE)

<br/>

**Stop discovering expired certificates after the outage.**  
**Start getting alerts days before it ever happens.**

</div>

---

## 💡 The Problem

In a multi-cluster Kubernetes environment, every control-plane certificate — `apiserver`, `kubelet-client`, `front-proxy-client`, `admin.conf` — has a **~1 year lifespan**. Across 10–15 clusters spanning `kubeadm`, `MicroK8s`, and `K3s`, manually tracking expiry means:

- ❌ Logging into each cluster individually — every day
- ❌ Certificates expiring silently with **zero warning**
- ❌ API servers rejecting calls, worker nodes disconnecting, **clusters going dark**
- ❌ Emergency midnight renewals instead of planned maintenance

**This tool eliminates all of that.**

---

## ✅ The Solution

A single Python script, triggered daily by Jenkins, that:

1. SSH-es into every cluster master — **no agents, no sidecars**
2. Runs the native certificate check command for that distribution
3. Parses and evaluates every certificate's remaining validity
4. **Fires an alert to Google Chat** the moment any cert crosses the threshold

> One script. One job. Total coverage. Zero surprises.

---

## ✨ Features at a Glance

| | Feature | Detail |
|---|---|---|
| 🔍 | **Multi-Distribution** | Native support for `kubeadm`, `K3s`, and `MicroK8s` |
| 📡 | **Agentless** | Pure SSH — nothing installed on cluster nodes |
| 🏢 | **Centralized** | One pipeline covers your entire fleet |
| ⚡ | **Early Warning** | Configurable threshold — alert days before expiry |
| 💬 | **ChatOps** | Rich, per-cluster alerts sent directly to Google Chat |
| 🔒 | **Secure by Default** | Ed25519 SSH keys, no passwords, secrets via Jenkins Credentials |
| 🤖 | **Fully Automated** | Daily Jenkins CRON — zero human intervention needed |
| 🔇 | **Noise-Free** | Root CAs (10+ year certs) are automatically excluded |

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌─────────────────┐      daily checkout       ┌──────────────────────┐   │
│   │   GitHub Repo   │ ────────────────────────► │   Jenkins Pipeline   │   │
│   │                 │                            │   CRON: H 9 * * *   │   │
│   │ cert_monitor.py │                            │   Agent: SlaveNode01 │   │
│   │ clusters.json   │                            └──────────┬───────────┘   │
│   │ Jenkinsfile     │                                       │               │
│   └─────────────────┘                           pip install + python3 run   │
│                                                             │               │
│                              ┌──────────────────────────────┤               │
│                              │    SSH (Ed25519, no password) │               │
│                              ▼                              │               │
│          ┌───────────┐  ┌────────────┐  ┌──────────────────▼───────┐       │
│          │    UAT    │  │   Dev-Qa   │  │        Staging            │       │
│          │ MicroK8s  │  │ Kubernetes │  │         K3s               │       │
│          │10.10.10.xx│  │10.20.30.xx │  │      10.49.31.xx          │       │
│          └─────┬─────┘  └─────┬──────┘  └────────────┬─────────────┘       │
│                │              │                       │                     │
│          microk8s        kubeadm certs           k3s certificate            │
│          refresh-certs   check-expiration        check / openssl            │
│                │              │                       │                     │
│                └──────────────┴───────────────────────┘                     │
│                                       │                                     │
│                              Parse → Evaluate                                │
│                                       │                                     │
│                       days_left ≤ ALERT_THRESHOLD_DAYS ?                    │
│                                       │ YES                                 │
│                               HTTP POST (JSON)                              │
│                                       │                                     │
│                           ┌───────────▼──────────┐                         │
│                           │   Google Chat Space   │                         │
│                           │    DevOps Room 🔔     │                         │
│                           └──────────────────────┘                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
📦 Cluster-Cert-Alerting/
│
├── 🐍 cert_monitor.py       # Core engine — SSH, parse, evaluate, alert
├── 📋 clusters.json         # Cluster inventory & connection config
├── 📦 requirements.txt      # Python dependencies (paramiko, requests)
├── 🔧 Jenkinsfile           # Declarative Jenkins pipeline definition
└── 📖 README.md             # You are here
```

---

## 🚀 Quick Start

### Prerequisites

- Python `3.8+`
- SSH access to each cluster master node *(Ed25519 key, no password)*
- A Google Chat space with an incoming Webhook configured

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/city-tech/Cluster-Cert-Alerting.git
cd Cluster-Cert-Alerting
```

---

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 3 — Configure Your Clusters

Edit `clusters.json` to define your cluster fleet:

```json
[
  {
    "name": "UAT",
    "type": "microk8s",
    "ip": "10.10.10.200",
    "ssh_user": "user1",
    "ssh_key_path": "/home/user1/.ssh/id_ed25519_certmonitor",
    "env": "UAT"
  },
  {
    "name": "Dev-Qa",
    "type": "kubernetes",
    "ip": "10.20.30.60",
    "ssh_user": "user2",
    "ssh_key_path": "/home/user2/.ssh/id_ed25519_certmonitor",
    "env": "getpay-dev-qa"
  },
  {
    "name": "Staging",
    "type": "k3s",
    "ip": "10.49.31.25",
    "ssh_user": "user3",
    "ssh_key_path": "/home/user3/.ssh/id_ed25519_certmonitor",
    "env": "Staging"
  }
]
```

> ⚠️ **Strict JSON only** — no `//` comments, no trailing commas. Python's `json.load()` will reject them.

**Supported `type` values:**

| Value | Distribution |
|---|---|
| `kubernetes` | Standard Kubernetes (kubeadm) |
| `microk8s` | Canonical MicroK8s |
| `k3s` | Lightweight K3s |

---

### Step 4 — Configure Your Google Chat Webhook

**Option A — Environment Variable** *(recommended)*

```bash
export CERT_MONITOR_WEBHOOK="https://chat.googleapis.com/v1/spaces/YOUR_SPACE_ID/messages?key=..."
```

**Option B — Edit the script directly**

```python
# cert_monitor.py
GOOGLE_CHAT_WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/..."
```

> 💡 To get your webhook: Open Google Chat → Space → **Apps & Integrations** → **Add Webhook** → Copy URL

---

### Step 5 — Run the Monitor

```bash
python3 cert_monitor.py
```

---

## ⚙️ Configuration Reference

| Variable | Description | Default |
|---|---|---|
| `CERT_MONITOR_THRESHOLD` | Days before expiry to trigger an alert | `7` |
| `CERT_MONITOR_CONFIG` | Path to the cluster inventory JSON | `clusters.json` |
| `CERT_MONITOR_WEBHOOK` | Google Chat Webhook URL for sending alerts | *(required)* |

All values are overridable via **environment variables** at runtime — no code changes required.

---

## ⚙️ How It Works

Every run follows a strict, deterministic 6-step cycle:

```
┌─────┐   ┌──────────┐   ┌─────────┐   ┌───────┐   ┌──────────┐   ┌──────────┐
│  1  │──►│  LOAD    │──►│ CONNECT │──►│INSPECT│──►│  PARSE   │──►│ EVALUATE │
│     │   │clusters  │   │ SSH     │   │native │   │ Regex    │   │days_left │
│     │   │  .json   │   │tunnel   │   │command│   │ parser   │   │vs thresh │
└─────┘   └──────────┘   └─────────┘   └───────┘   └──────────┘   └────┬─────┘
                                                                         │
                                                                         ▼
                                                                    ┌──────────┐
                                                                    │  ALERT   │
                                                                    │ Google   │
                                                                    │  Chat    │
                                                                    └──────────┘
```

### Certificate Commands by Distribution

| Distribution | Command |
|---|---|
| `kubernetes` / `kubeadm` | `sudo kubeadm certs check-expiration` |
| `microk8s` | `sudo microk8s refresh-certs --check` |
| `k3s` | `sudo k3s certificate check` → fallback: `openssl x509` scan |

### Status Levels

| Badge | Condition | Action Taken |
|---|---|---|
| ✅ **OK** | `days > 30` | Logged to Jenkins console |
| ⚠️ **WARNING** | `5 < days ≤ 30` | Logged to Jenkins console |
| 🚨 **URGENT** | `days ≤ threshold` | Alert fired to Google Chat |

> 🔇 **Root Certificate Authorities** (containing `CA` in name) are always excluded — no false alerts from 10-year certs.

---

## 📊 Live Console Output Example

```
CERTIFICATE EXPIRY CHECK - 2026-01-28
3 cluster(s) loaded

UAT (UAT) @ 10.10.10.200 -- microk8s
......................................................................................
Certificates:
  • server                   OK                 expires 2026-11-01
  • front-proxy-client       WARNING (22d)      expires 2026-02-19
......................................................................................

Dev-Qa (getpay-dev-qa) @ 10.20.30.60 -- kubernetes
......................................................................................
Certificates:
  • apiserver                OK                 expires 2026-12-15
  • admin.conf               URGENT (3d)        expires 2026-02-01
......................................................................................
-> Alert sent for Dev-Qa

Staging (Staging) @ 10.49.31.25 -- k3s
......................................................................................
Certificates:
  • server-ca                OK                 expires 2027-03-01
......................................................................................

All other clusters: OK
```

---

## 💬 Sample Google Chat Alert

```
🚨 CERTIFICATE EXPIRY ALERT: Dev-Qa 🚨

• Environment:   getpay-dev-qa
• Server:        10.20.30.60
• Certificates:  `admin.conf`, `front-proxy-client`
• Expires In:    3 days  (2026-02-01)

Please plan for renewal soon to avoid disruption.
```

---

## 🔐 SSH Key Setup

Generate a **dedicated** Ed25519 keypair for this automation job:

**Linux / macOS**
```bash
# Generate key
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_certmonitor -N ""

# Authorize on each cluster master
ssh-copy-id -i ~/.ssh/id_ed25519_certmonitor.pub user1@10.10.10.200
ssh-copy-id -i ~/.ssh/id_ed25519_certmonitor.pub user2@10.20.30.60
ssh-copy-id -i ~/.ssh/id_ed25519_certmonitor.pub user3@10.49.31.25

# Verify passwordless access
ssh -i ~/.ssh/id_ed25519_certmonitor user1@10.10.10.200 whoami
```

**Windows PowerShell**
```powershell
# Generate key
ssh-keygen -t ed25519 -f "$HOME\.ssh\id_ed25519_certmonitor" -N '""'

# Authorize on a cluster master
type "$HOME\.ssh\id_ed25519_certmonitor.pub" | ssh user1@10.10.10.200 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

> 🔒 **Permissions:** `chmod 600 ~/.ssh/id_ed25519_certmonitor` and `chmod 700 ~/.ssh/`

---

## 🤖 Jenkins Pipeline

The included `Jenkinsfile` automates everything on a daily schedule:

```groovy
triggers {
    cron('H 9 * * *')   // Fires daily around 9 AM
}
```

**Pipeline Stages:**

| Stage | Action |
|---|---|
| `Checkout Repo` | Pulls latest from `main` branch via authenticated GitSCM |
| `Install sshpass` | Ensures sshpass is available on the agent |
| `Install Dependencies` | `pip install -r requirements.txt` |
| `Run Certificate Check` | `python3 cert_monitor.py` with injected credentials |

**Required Jenkins Credentials:**

| Credential ID | Type | Used For |
|---|---|---|
| `github-hardened-token` | Username + Token | Authenticated GitHub checkout |
| `mbl-uat-ssh-password` | Username + Password | SSH password-based cluster access |

---

## 🧪 Testing Without Real Expiry

Force-trigger alerts during testing by temporarily raising the threshold:

```bash
# Trigger alerts for any cert expiring within 330 days
export CERT_MONITOR_THRESHOLD=330
python3 cert_monitor.py

# Verify alert arrived in Google Chat, then reset
export CERT_MONITOR_THRESHOLD=7
```

---

## 🗺️ Roadmap

- [x] Multi-distribution support — `kubeadm`, `MicroK8s`, `K3s`
- [x] Google Chat alerting via Webhook
- [x] Jenkins CRON pipeline with credential injection
- [x] Ed25519 SSH key authentication (agentless)
- [x] Per-cluster alert grouping (no alert spam)
- [ ] Migrate SSH keys to Jenkins `sshagent` plugin *(in progress)*
- [ ] Add retry logic & connection timeout handling
- [ ] Email / Slack fallback notifications
- [ ] Prometheus metrics endpoint exposure
- [ ] Expand coverage to full 15-cluster fleet

---

## ❓ FAQ

<details>
<summary><b>Does this install anything on my clusters?</b></summary>

No. All checks are performed passively over SSH using native OS-level commands. Zero software is installed on target nodes.
</details>

<details>
<summary><b>What Kubernetes distributions are supported?</b></summary>

Standard Kubernetes (kubeadm), MicroK8s, and K3s — all handled within a single run.
</details>

<details>
<summary><b>Does it alert on root CA certificates?</b></summary>

No. Root CAs (typically valid for 10+ years) are automatically excluded by checking for `CA` in the certificate name. This prevents false alerts.
</details>

<details>
<summary><b>Can it monitor clusters on different subnets or behind a VPN?</b></summary>

Yes — as long as the Jenkins agent node has SSH network connectivity to each cluster's master node.
</details>

<details>
<summary><b>What happens if a cluster is unreachable?</b></summary>

The script logs a detailed error for that cluster and continues checking the remaining clusters. One offline node does not stop the full run.
</details>

---

## 👥 Authors & Credits

| Name | Role |
|---|---|
| **Pratham Sharma** | Author · DevOps Engineer |
| **Citytech System Team** | Infrastructure & Operations |

---

<div align="center">

Built with ❤️ by **Citytech System Team**

*Powered by Antigravity AI*

</div>
