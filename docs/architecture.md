# Architectural Specification: Dual VPS Tunnel & Proxy System

## 1. System Topology & Overview

The system delivers an automated, zero-dependency dual-protocol proxy tunnel server (`vps_tunnel.py`) and a remote orchestration client (`deploy_tunnel.py`).

```text
               +-------------------------------------------------------------+
               |                       Local Machine                         |
               |                                                             |
               |  [ .env / CLI Args ] ──► [ deploy_tunnel.py ]               |
               |                                 │ (Docker / Native)         |
               +─────────────────────────────────┼───────────────────────────+
                                                 │ SSH Port 22 (Askpass Auth)
                                                 │ Base64 Payload Injection
                                                 ▼
               +-------------------------------------------------------------+
               |                     Remote Linux VPS                        |
               |                                                             |
               |  [ vps_tunnel.py ] ◄── Installed to /root/vps_tunnel.py     |
               |  [ systemd ]       ◄── /etc/systemd/system/vps-tunnel.service
               |  [ Firewall ]      ◄── ufw / iptables / firewalld open      |
               |                                                             |
               |      ┌────────────────────────┬────────────────────────┐    |
               |      │  HttpProxyServer       │  Socks5ProxyServer     │    |
               |      │  Port: 8443 (HTTP/TLS) │  Port: 1080 (TCP)      │    |
               |      │  Auth: RFC 7617 Basic  │  Auth: RFC 1929 U/P    │    |
               |      └───────────┬────────────┴───────────┬────────────┘    |
               +──────────────────┼────────────────────────┼─────────────────+
                                  │                        │
                                  ▼                        ▼
                          [ Remote Web / Destination Endpoints ]
```

---

## 2. Component Decomposition

### 2.1 `deploy_tunnel.py` (Local Client & Orchestrator)
- **Role**: Reads configuration from environment variables (`.env` file or process environment) and CLI arguments.
- **SSH Transport**: Automates OpenSSH execution via a temporary non-interactive `SSH_ASKPASS` credential handler (compatible across Windows PowerShell / CMD and Linux/macOS POSIX shells).
- **Zero-Transfer Payload Injection**: Embeds the full source of `vps_tunnel.py` encoded in Base64 within the SSH command string, writing directly to `/root/vps_tunnel.py` on the target host.
- **Credential Generation**: Dynamically generates cryptographic random alphanumeric strings (`secrets.choice`) for username and password when omitted.

### 2.2 `vps_tunnel.py` (Remote Dual Proxy Server)
- **Runtime**: Pure Python standard library (Python 3.8+) with `asyncio` event loop.
- **`HttpProxyServer`**:
  - Handles `CONNECT` method for arbitrary TCP tunneling (HTTPS, SSH, WebSockets) with `Proxy-Authorization: Basic` verification.
  - Handles cleartext HTTP request relaying with hop-by-hop `Proxy-*` header sanitization.
  - Supports optional TLS encapsulation via self-signed OpenSSL certificate (`--https`).
- **`Socks5ProxyServer`**:
  - Implements **RFC 1928** (SOCKS Protocol Version 5) method negotiation.
  - Implements **RFC 1929** (SOCKS5 Username/Password Subnegotiation).
  - Handles address types `0x01` (IPv4), `0x03` (Domain name resolution), and `0x04` (IPv6).
  - Executes asynchronous bidirectional stream forwarding with 64KB (`65536` bytes) buffer chunking.

---

## 3. Concurrency & Security Invariants

1. **Non-Blocking I/O**: Both `HttpProxyServer` and `Socks5ProxyServer` run concurrently within a single `asyncio` event loop utilizing `asyncio.gather()`.
2. **Constant-Time Comparison**: Authentication tokens and passwords are verified using `secrets.compare_digest()` to prevent side-channel timing attacks.
3. **Firewall Multi-Engine Defense**: Automatic port detection and rule creation targeting `ufw`, `iptables`, and `firewall-cmd`.
4. **Service Persistence**: Managed as an isolated systemd unit (`vps-tunnel.service`) with `Restart=always` and `RestartSec=3`.
