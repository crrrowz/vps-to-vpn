# Configuration Reference

This document provides the authoritative specification for all environment variables, `.env` directives, and command-line flags.

---

## 1. Environment Variables Specification (`.env`)

| Variable | Type | Required / Default | Description |
| :--- | :--- | :--- | :--- |
| `VPS_HOST` | String | **Required** (or CLI prompt) | IP address or hostname of the destination VPS. |
| `SSH_PORT` | Integer | Optional (`22`) | Remote SSH listening port. |
| `SSH_USER` | String | Optional (`root`) | SSH username for authentication. |
| `SSH_PASS` | String | **Required** (or CLI prompt) | SSH password for the remote user. |
| `PROXY_USER` | String | Optional (auto-generated) | Username for HTTP and SOCKS5 proxy authentication. If empty, generates `user_<random_6_chars>`. |
| `PROXY_PASS` | String | Optional (auto-generated) | Password for HTTP and SOCKS5 proxy authentication. If empty, generates 12-char random alphanumeric. |
| `HTTP_PORT` | Integer | Optional (`8443`) | Port for the HTTP/HTTPS proxy tunnel server. |
| `SOCKS5_PORT` | Integer | Optional (`1080`) | Port for the SOCKS5 proxy tunnel server. |
| `ENABLE_HTTPS` | Boolean | Optional (`false`) | When set to `true`, `1`, or `yes`, enables TLS encryption for HTTP proxy. |

---

## 2. CLI Flags: `deploy_tunnel.py`

| Flag | Type | Default | Code Reference | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--host` | String | `env.VPS_HOST` | `deploy_tunnel.py:106` | Destination VPS IP or hostname. |
| `--ssh-port` | Integer | `22` | `deploy_tunnel.py:107` | Remote SSH daemon port. |
| `--ssh-user` | String | `root` | `deploy_tunnel.py:108` | Remote SSH user account. |
| `--ssh-pass` | String | `env.SSH_PASS` | `deploy_tunnel.py:109` | Remote SSH user password. |
| `--http-port` | Integer | `8443` | `deploy_tunnel.py:111` | Port allocated for HTTP/HTTPS proxy. |
| `--socks5-port` | Integer | `1080` | `deploy_tunnel.py:112` | Port allocated for SOCKS5 proxy. |
| `--proxy-user` | String | Auto-generated | `deploy_tunnel.py:113` | Custom proxy authentication username. |
| `--proxy-pass` | String | Auto-generated | `deploy_tunnel.py:114` | Custom proxy authentication password. |
| `--https` | Flag | `false` | `deploy_tunnel.py:115` | Enables self-signed TLS encryption for HTTP proxy. |

---

## 3. CLI Flags: `vps_tunnel.py`

| Flag | Type | Default | Code Reference | Description |
| :--- | :--- | :--- | :--- | :--- |
| `--http-port`, `--port` | Integer | `8443` | `vps_tunnel.py:442` | Port to bind the HTTP/HTTPS proxy server. |
| `--socks5-port` | Integer | `1080` | `vps_tunnel.py:443` | Port to bind the SOCKS5 proxy server. |
| `--user` | String | Auto-generated | `vps_tunnel.py:444` | Username for client authentication. |
| `--pass` | String | Auto-generated | `vps_tunnel.py:445` | Password for client authentication. |
| `--https` | Flag | `false` | `vps_tunnel.py:446` | Enables TLS encapsulation for HTTP proxy. |
| `--install-service` | Flag | `false` | `vps_tunnel.py:447` | Writes and registers `/etc/systemd/system/vps-tunnel.service`. |
| `--no-prompt` | Flag | `false` | `vps_tunnel.py:448` | Suppresses interactive console prompts. |
