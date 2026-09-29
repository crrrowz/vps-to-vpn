# API & Protocol Reference

This document outlines the protocols, authentication schemas, response codes, and client integration examples for the Dual VPS Proxy Tunnel.

---

## 1. HTTP/HTTPS CONNECT Proxy Protocol

The HTTP proxy listens on `HTTP_PORT` (`8443` default) and supports both cleartext HTTP forwarding and transparent TCP tunneling via the `CONNECT` method.

### 1.1 Authentication (RFC 7617 Basic Authentication)
- Clients must provide credentials via the `Proxy-Authorization` header:
  ```http
  Proxy-Authorization: Basic <base64(username:password)>
  ```
- **Unauthorized Response (`407 Proxy Authentication Required`)**:
  ```http
  HTTP/1.1 407 Proxy Authentication Required
  Proxy-Authenticate: Basic realm="Tunnel Access"
  Connection: close
  Content-Length: 0
  ```

### 1.2 Tunnel Establishment (`CONNECT`)
```http
CONNECT target.domain.com:443 HTTP/1.1
Host: target.domain.com:443
Proxy-Authorization: Basic dXNlcjpwYXNz
```

**Success Response (`200 Connection Established`)**:
```http
HTTP/1.1 200 Connection Established
```
Once returned, the proxy transitions into bidirectional byte streaming.

---

## 2. SOCKS5 Proxy Protocol (RFC 1928 & RFC 1929)

The SOCKS5 proxy listens on `SOCKS5_PORT` (`1080` default) and implements authenticated SOCKS5 negotiation.

### 2.1 Negotiation & Subnegotiation Flow
1. **Client Greeting**: `0x05` (Version 5), `0x01` (1 Method), `0x02` (Username/Password Auth).
2. **Server Response**: `0x05 0x02` (Accepts Username/Password).
3. **Client Auth Subnegotiation (RFC 1929)**: `0x01` (Subneg Version) + `[User Length][Username]` + `[Pass Length][Password]`.
4. **Server Auth Result**:
   - `0x01 0x00` -> Authentication Successful.
   - `0x01 0x01` -> Authentication Failed (Connection terminated).
5. **Connection Request (`CONNECT 0x01`)**:
   - Address Types: `0x01` (IPv4), `0x03` (Domain name), `0x04` (IPv6).
   - Server Response: `0x05 0x00 0x00 [ATYP] [Bind Address] [Bind Port]`.

---

## 3. Client Integration Examples

### 3.1 cURL
```bash
# HTTP Proxy
curl -x http://user:pass@139.84.175.230:8443 https://api.ipify.org

# SOCKS5 Proxy (with remote DNS resolution)
curl --socks5-hostname 139.84.175.230:1080 --proxy-user user:pass https://api.ipify.org
```

### 3.2 Python (`requests` / `urllib3`)
```python
import requests

# HTTP/HTTPS Proxy
proxies_http = {
    "http": "http://user:pass@139.84.175.230:8443",
    "https": "http://user:pass@139.84.175.230:8443",
}
resp = requests.get("https://api.ipify.org?format=json", proxies=proxies_http)
print("HTTP Proxy IP:", resp.json())

# SOCKS5 Proxy (requires requests[socks])
proxies_socks5 = {
    "http": "socks5h://user:pass@139.84.175.230:1080",
    "https": "socks5h://user:pass@139.84.175.230:1080",
}
resp_socks = requests.get("https://api.ipify.org?format=json", proxies=proxies_socks5)
print("SOCKS5 Proxy IP:", resp_socks.json())
```
