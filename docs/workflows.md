# System Workflows & Lifecycle Specification

## 1. Remote Deployment & Provisioning Workflow

The following sequence illustrates the one-click deployment lifecycle executed by `deploy_tunnel.py` (or Docker container):

```text
Local / Client                deploy_tunnel.py                     Remote VPS (systemd/ufw)
      │                              │                                       │
      │── Execute (CLI/.env) ───────►│                                       │
      │                              │── Parse .env & Generate Credentials ──│
      │                              │── Create Ephemeral SSH_ASKPASS script │
      │                              │── OpenSSH Connect (Port 22) ─────────►│
      │                              │                                       │
      │                              │   [Remote Execution Phase]            │
      │                              │   1. Write /root/vps_tunnel.py        │
      │                              │   2. ufw allow 8443, 1080/tcp ───────►│ Open Firewall
      │                              │   3. iptables / firewalld rules ─────►│ Open Ports
      │                              │   4. Generate SSL cert (if --https)──►│ /root/server.crt
      │                              │   5. Write /etc/systemd/system/.. ───►│ Create Unit
      │                              │   6. systemctl daemon-reload ────────►│ Reload daemon
      │                              │   7. systemctl restart vps-tunnel ───►│ Start daemon
      │                              │   8. Query external IP (ipify/etc) ──►│ Detect Public IP
      │                              │◄── Output JSON / Format Strings ──────│
      │                              │                                       │
      │                              │── Purge Ephemeral Askpass Script ────►│
      │◄── Render Connection Table ──│                                       │
```

---

## 2. Service Management Workflow (on VPS)

The proxy tunnel is registered as a native system service: `/etc/systemd/system/vps-tunnel.service`.

### 2.1 Inspection
```bash
# Check service status & active connections
sudo systemctl status vps-tunnel

# Tail live daemon logs
sudo journalctl -u vps-tunnel -f
```

### 2.2 Operations
```bash
# Restart both HTTP and SOCKS5 tunnels
sudo systemctl restart vps-tunnel

# Stop service
sudo systemctl stop vps-tunnel

# Disable autostart on boot
sudo systemctl disable vps-tunnel
```

---

## 3. Firewall State Transitions

When `vps_tunnel.py` initializes or redeploys:
1. **UFW Detection**: If `which ufw` succeeds, executes `ufw allow <HTTP_PORT>/tcp` and `ufw allow <SOCKS5_PORT>/tcp`.
2. **FirewallD Detection**: If `which firewall-cmd` succeeds, executes `firewall-cmd --permanent --add-port=<PORT>/tcp` followed by `firewall-cmd --reload`.
3. **Iptables Fallback**: Executes `iptables -I INPUT -p tcp --dport <PORT> -j ACCEPT`.
