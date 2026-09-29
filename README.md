# 🚀 VPS Dual Tunnel & Proxy Deployer (HTTP/HTTPS + SOCKS5)

A comprehensive, zero-friction toolset to deploy and manage a high-performance **HTTP/HTTPS Proxy** and **SOCKS5 Proxy** simultaneously on any Linux VPS with a single command. Features automatic firewall rule configuration, public IP detection, `.env` configuration support, and permanent background `systemd` service setup.

---

## 📚 Documentation Index

For deep-dive technical references and specifications, consult the `docs/` hierarchy:
- [Repository Identity & Mission Contract](docs/repository-identity.md)
- [Architecture & System Topology](docs/architecture.md)
- [Configuration & Environment Variables](docs/configuration.md)
- [API & Protocol Reference (HTTP CONNECT & SOCKS5)](docs/api-reference.md)
- [Workflows & Service Management](docs/workflows.md)
- [Project Physical Structure](docs/project-structure.md)
- [Documentation Drift & Audit Report](docs/reports/documentation-drift-report.md)

---

## ⚙️ Environment Configuration (`.env`)

You can define your server and proxy settings in a `.env` file (a template `.env.example` is included).

```ini
# --- VPS SSH Credentials ---
VPS_HOST=
SSH_PORT=22
SSH_USER=root
SSH_PASS=

# --- Proxy Credentials & Ports ---
# If left blank, random secure username/password will be generated automatically
PROXY_USER=
PROXY_PASS=

# Ports
HTTP_PORT=8443
SOCKS5_PORT=1080

# Enable HTTPS TLS for HTTP Proxy (true / false)
ENABLE_HTTPS=false
```

> **Note:** If `PROXY_USER` or `PROXY_PASS` is left empty in `.env`, a secure random username and password will be generated automatically on each deployment.

---

## 🐳 Run via Docker (Recommended)

Run the deployer in an ephemeral Docker container. It reads credentials from `.env` automatically.

### 1. Using Docker Compose:
```bash
docker compose run --rm tunnel-deployer
```

### 2. Override options via CLI arguments:
```bash
docker compose run --rm tunnel-deployer --host <VPS_IP> --ssh-pass "<SSH_PASSWORD>" --proxy-user admin --proxy-pass secret123
```

---

## 💻 Run via Local Python (`deploy_tunnel.py`)

Run directly from your local machine (Windows / Linux / macOS):

```bash
python deploy_tunnel.py
```
*(If `.env` is present, it will automatically use the values; otherwise it will prompt interactively).*

---

## 🖥️ Direct VPS Execution (`vps_tunnel.py`)

If you are inside the VPS terminal directly:

```bash
# Install and run both HTTP and SOCKS5 proxies as a permanent service:
sudo python3 vps_tunnel.py --http-port 8443 --socks5-port 1080 --user admin --pass mypass123 --install-service
```

### Manage the Service on VPS:
- **Check Status:** `systemctl status vps-tunnel`
- **Restart Service:** `systemctl restart vps-tunnel`
- **Stop Service:** `systemctl stop vps-tunnel`

---

## 🔗 Supported Connection Formats

Once deployed, you receive connection formats for all clients:

### 1. HTTP(S) Proxy:
- **Standard format:** `IP:HTTP_PORT:USER:PASS`
- **URL format:** `http://USER:PASS@IP:HTTP_PORT`
- **cURL test:**
  ```bash
  curl -x http://USER:PASS@IP:8443 https://api.ipify.org
  ```

### 2. SOCKS5 Proxy:
- **Standard format:** `IP:SOCKS5_PORT:USER:PASS`
- **URL format:** `socks5://USER:PASS@IP:SOCKS5_PORT`
- **cURL test:**
  ```bash
  curl --socks5-hostname IP:1080 --proxy-user USER:PASS https://api.ipify.org
  ```

---

## 🛡️ Key Features

1. **Dual Protocol Support:** Runs both HTTP/HTTPS (CONNECT) and SOCKS5 (RFC 1928 / RFC 1929 authenticated) simultaneously.
2. **Auto Firewall Rules:** Detects and configures `ufw`, `iptables`, and `firewalld` for both ports automatically.
3. **Permanent Background Execution:** Installs a `systemd` service (`vps-tunnel.service`) to ensure proxies stay alive after reboot.
4. **Clean Overwrite:** Redeploying cleanly restarts and updates the service without port conflicts.
