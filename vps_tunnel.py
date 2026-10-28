#!/usr/bin/env python3
"""
Single-File VPS HTTP/HTTPS & SOCKS5 Dual Proxy Tunnel Server
------------------------------------------------------------
- Async HTTP/HTTPS Proxy (CONNECT + standard HTTP) with Basic Auth
- Async SOCKS5 Proxy Server with RFC 1929 Username/Password Auth
- Automatic Firewall Port Opening (ufw, iptables, firewalld)
- Auto SSL/TLS Certificate Generation for HTTPS Tunnels
- Auto Public IP Detection
- Optional Systemd Service Installation
"""

import sys
import os
import ssl
import base64
import socket
import struct
import asyncio
import argparse
import subprocess
import urllib.request
import secrets
import string

BUFFER_SIZE = 65536
DEFAULT_HTTP_PORT = 8443
DEFAULT_SOCKS5_PORT = 1080

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0, res.stdout.strip()
    except Exception as e:
        return False, str(e)

def open_firewall_ports(ports, proto="tcp"):
    print(f"[*] Opening ports {ports} ({proto}) in firewall...")
    for port in ports:
        # Check UFW
        ok, _ = run_cmd("which ufw")
        if ok:
            run_cmd(f"ufw allow {port}/{proto}")

        # Check firewalld
        ok, _ = run_cmd("which firewall-cmd")
        if ok:
            run_cmd(f"firewall-cmd --permanent --add-port={port}/{proto}")

        # Check iptables
        ok, _ = run_cmd("which iptables")
        if ok:
            run_cmd(f"iptables -I INPUT -p {proto} --dport {port} -j ACCEPT")

    # Reload firewalld if available
    ok, _ = run_cmd("which firewall-cmd")
    if ok:
        run_cmd("firewall-cmd --reload")
    print("  [+] Firewall rules applied successfully.")

def get_public_ip():
    services = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com"
    ]
    for s in services:
        try:
            req = urllib.request.Request(s, headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                ip = resp.read().decode('utf-8').strip()
                if ip:
                    return ip
        except Exception:
            continue
    return "YOUR_SERVER_IP"

def generate_self_signed_cert(cert_file="server.crt", key_file="server.key"):
    if os.path.exists(cert_file) and os.path.exists(key_file):
        return True
    print("[*] Generating self-signed SSL certificate...")
    cmd = (
        f'openssl req -x509 -newkey rsa:2048 -keyout "{key_file}" -out "{cert_file}" '
        f'-days 3650 -nodes -subj "/CN=proxy-tunnel"'
    )
    ok, err = run_cmd(cmd)
    return ok

def generate_random_string(length=12):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

async def forward_stream(reader, writer):
    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass

# ==================== HTTP/HTTPS PROXY ====================

class HttpProxyServer:
    def __init__(self, host, port, username, password, use_ssl=False, certfile=None, keyfile=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.certfile = certfile
        self.keyfile = keyfile
        self.expected_auth = base64.b64encode(f"{username}:{password}".encode()).decode()

    async def handle_client(self, client_reader, client_writer):
        try:
            header_data = b""
            while b"\r\n\r\n" not in header_data:
                chunk = await client_reader.read(4096)
                if not chunk:
                    client_writer.close()
                    return
                header_data += chunk
                if len(header_data) > 65536:
                    client_writer.close()
                    return

            header_text, _, rest = header_data.partition(b"\r\n\r\n")
            lines = header_text.decode("latin1", errors="replace").split("\r\n")
            if not lines:
                client_writer.close()
                return

            request_line = lines[0]
            parts = request_line.split()
            if len(parts) < 2:
                client_writer.close()
                return

            method = parts[0].upper()
            target = parts[1]

            # Parse headers for Proxy-Authorization
            auth_header = None
            for line in lines[1:]:
                if ":" in line:
                    key, val = line.split(":", 1)
                    if key.strip().lower() == "proxy-authorization":
                        auth_header = val.strip()
                        break

            authenticated = False
            if auth_header and auth_header.startswith("Basic "):
                provided_auth = auth_header[6:].strip()
                if secrets.compare_digest(provided_auth, self.expected_auth):
                    authenticated = True

            if not authenticated:
                response = (
                    "HTTP/1.1 407 Proxy Authentication Required\r\n"
                    "Proxy-Authenticate: Basic realm=\"Tunnel Access\"\r\n"
                    "Connection: close\r\n"
                    "Content-Length: 0\r\n\r\n"
                )
                client_writer.write(response.encode())
                await client_writer.drain()
                client_writer.close()
                return

            # CONNECT Method
            if method == "CONNECT":
                if ":" in target:
                    dst_host, dst_port = target.split(":", 1)
                    dst_port = int(dst_port)
                else:
                    dst_host = target
                    dst_port = 443

                try:
                    remote_reader, remote_writer = await asyncio.open_connection(dst_host, dst_port)
                except Exception:
                    client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    await client_writer.drain()
                    client_writer.close()
                    return

                client_writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                await client_writer.drain()

                if rest:
                    remote_writer.write(rest)
                    await remote_writer.drain()

                await asyncio.gather(
                    forward_stream(client_reader, remote_writer),
                    forward_stream(remote_reader, client_writer),
                    return_exceptions=True
                )

            # Plain HTTP Methods
            else:
                if target.startswith("http://"):
                    path_part = target[7:]
                    slash_pos = path_part.find("/")
                    if slash_pos == -1:
                        host_part = path_part
                        rel_path = "/"
                    else:
                        host_part = path_part[:slash_pos]
                        rel_path = path_part[slash_pos:]

                    if ":" in host_part:
                        dst_host, dst_port = host_part.split(":", 1)
                        dst_port = int(dst_port)
                    else:
                        dst_host = host_part
                        dst_port = 80
                else:
                    client_writer.close()
                    return

                try:
                    remote_reader, remote_writer = await asyncio.open_connection(dst_host, dst_port)
                except Exception:
                    client_writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    await client_writer.drain()
                    client_writer.close()
                    return

                new_request = f"{method} {rel_path} {parts[2] if len(parts) > 2 else 'HTTP/1.1'}\r\n"
                for line in lines[1:]:
                    if not line.lower().startswith("proxy-"):
                        new_request += f"{line}\r\n"
                new_request += "\r\n"

                remote_writer.write(new_request.encode("latin1") + rest)
                await remote_writer.drain()

                await asyncio.gather(
                    forward_stream(client_reader, remote_writer),
                    forward_stream(remote_reader, client_writer),
                    return_exceptions=True
                )

        except Exception:
            pass
        finally:
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except Exception:
                pass

    async def start(self):
        ssl_ctx = None
        if self.use_ssl:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)

        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
            ssl=ssl_ctx
        )
        return server

# ==================== SOCKS5 PROXY ====================

class Socks5ProxyServer:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    async def handle_client(self, client_reader, client_writer):
        try:
            # 1. Version & Auth Negotiation
            header = await client_reader.readexactly(2)
            version, nmethods = struct.unpack("!BB", header)
            if version != 5:
                client_writer.close()
                return

            methods = await client_reader.readexactly(nmethods)
            # 0x02 = Username/Password Auth (RFC 1929)
            if 0x02 not in methods:
                client_writer.write(struct.pack("!BB", 5, 0xFF))
                await client_writer.drain()
                client_writer.close()
                return

            # Request Username/Password
            client_writer.write(struct.pack("!BB", 5, 0x02))
            await client_writer.drain()

            # 2. Subnegotiation (RFC 1929)
            auth_ver = await client_reader.readexactly(1)
            if auth_ver[0] != 1:
                client_writer.close()
                return

            ulen = (await client_reader.readexactly(1))[0]
            uname = (await client_reader.readexactly(ulen)).decode("utf-8", errors="replace")
            plen = (await client_reader.readexactly(1))[0]
            passwd = (await client_reader.readexactly(plen)).decode("utf-8", errors="replace")

            if secrets.compare_digest(uname, self.username) and secrets.compare_digest(passwd, self.password):
                # Success
                client_writer.write(struct.pack("!BB", 1, 0x00))
                await client_writer.drain()
            else:
                # Failure
                client_writer.write(struct.pack("!BB", 1, 0x01))
                await client_writer.drain()
                client_writer.close()
                return

            # 3. Connection Request
            req_header = await client_reader.readexactly(4)
            s_ver, cmd, rsv, atyp = struct.unpack("!BBBB", req_header)
            if s_ver != 5 or cmd != 1:  # 1 = CONNECT
                # 0x07 = Command not supported
                client_writer.write(struct.pack("!BBBBIH", 5, 0x07, 0, 1, 0, 0))
                await client_writer.drain()
                client_writer.close()
                return

            if atyp == 1:  # IPv4
                dest_ip_raw = await client_reader.readexactly(4)
                dest_addr = socket.inet_ntoa(dest_ip_raw)
            elif atyp == 3:  # Domain
                addr_len = (await client_reader.readexactly(1))[0]
                dest_addr = (await client_reader.readexactly(addr_len)).decode("utf-8", errors="replace")
            elif atyp == 4:  # IPv6
                dest_ip_raw = await client_reader.readexactly(16)
                dest_addr = socket.inet_ntop(socket.AF_INET6, dest_ip_raw)
            else:
                client_writer.close()
                return

            dest_port_raw = await client_reader.readexactly(2)
            dest_port = struct.unpack("!H", dest_port_raw)[0]

            # Connect to destination
            try:
                remote_reader, remote_writer = await asyncio.open_connection(dest_addr, dest_port)
            except Exception as conn_err:
                print(f"[-] SOCKS5 connect failed to {dest_addr}:{dest_port} -> {conn_err}")
                # 0x05 = Connection refused
                client_writer.write(struct.pack("!BBBBIH", 5, 0x05, 0, 1, 0, 0))
                await client_writer.drain()
                client_writer.close()
                return

            try:
                sockname = remote_writer.get_extra_info('sockname')
                bind_addr, bind_port = sockname[0], sockname[1]
                bind_ip_bytes = socket.inet_aton(bind_addr) if ":" not in bind_addr else b"\x00\x00\x00\x00"
                atyp_resp = 1
            except Exception:
                bind_ip_bytes = b"\x00\x00\x00\x00"
                bind_port = 0
                atyp_resp = 1

            # 0x00 = Request granted
            resp = struct.pack("!BBBB", 5, 0x00, 0, atyp_resp) + bind_ip_bytes + struct.pack("!H", bind_port)
            client_writer.write(resp)
            await client_writer.drain()

            await asyncio.gather(
                forward_stream(client_reader, remote_writer),
                forward_stream(remote_reader, client_writer),
                return_exceptions=True
            )

        except Exception:
            pass
        finally:
            try:
                client_writer.close()
                await client_writer.wait_closed()
            except Exception:
                pass

    async def start(self):
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        return server

# ==================== SYSTEMD SERVICE ====================

def install_systemd_service(http_port, socks5_port, user, password, use_https):
    script_path = os.path.abspath(__file__)
    https_flag = "--https" if use_https else ""
    service_content = f"""[Unit]
Description=VPS Secure HTTP/HTTPS & SOCKS5 Dual Proxy Tunnel Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={os.path.dirname(script_path)}
ExecStart={sys.executable} {script_path} --http-port {http_port} --socks5-port {socks5_port} --user {user} --pass {password} {https_flag} --no-prompt
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    service_file = "/etc/systemd/system/vps-tunnel.service"
    try:
        with open(service_file, "w") as f:
            f.write(service_content)
        run_cmd("systemctl daemon-reload")
        run_cmd("systemctl enable vps-tunnel.service")
        run_cmd("systemctl restart vps-tunnel.service")
        print(f"[+] Systemd service installed and active: vps-tunnel.service")
        print("    Manage with: systemctl status|restart|stop vps-tunnel")
        return True
    except Exception as e:
        print(f"[-] Failed to install systemd service: {e}")
        return False

# ==================== MAIN ENTRYPOINT ====================

def main():
    parser = argparse.ArgumentParser(description="One-Click VPS Dual Tunnel (HTTP/HTTPS + SOCKS5) Setup")
    parser.add_argument("--http-port", "--port", dest="http_port", type=int, default=DEFAULT_HTTP_PORT, help="HTTP(S) proxy port")
    parser.add_argument("--socks5-port", type=int, default=DEFAULT_SOCKS5_PORT, help="SOCKS5 proxy port")
    parser.add_argument("--user", type=str, default=None, help="Proxy username")
    parser.add_argument("--pass", dest="passwd", type=str, default=None, help="Proxy password")
    parser.add_argument("--https", action="store_true", help="Enable HTTPS (TLS) encrypted tunnel")
    parser.add_argument("--install-service", action="store_true", help="Install as permanent systemd background service")
    parser.add_argument("--no-prompt", action="store_true", help="Run directly without interactive prompts")

    args = parser.parse_args()

    http_port = args.http_port
    socks5_port = args.socks5_port
    user = args.user or f"user_{generate_random_string(6)}"
    passwd = args.passwd or generate_random_string(12)
    use_https = args.https

    # Open firewall for both ports
    open_firewall_ports([http_port, socks5_port])

    cert_file = "server.crt"
    key_file = "server.key"
    if use_https:
        if not generate_self_signed_cert(cert_file, key_file):
            print("[-] Switching back to standard HTTP Tunnel due to SSL error.")
            use_https = False

    public_ip = get_public_ip()
    http_proto = "https" if use_https else "http"

    print("\n" + "="*58)
    print("       DUAL PROXY TUNNEL CONFIGURATION DETAILS")
    print("="*58)
    print(f"Server IP         : {public_ip}")
    print(f"HTTP/HTTPS Port   : {http_port} ({http_proto.upper()})")
    print(f"SOCKS5 Port       : {socks5_port}")
    print(f"Username          : {user}")
    print(f"Password          : {passwd}")
    print("-" * 58)
    print("CONNECTION STRINGS:")
    print(f"1) HTTP(S) Standard: {public_ip}:{http_port}:{user}:{passwd}")
    print(f"   HTTP(S) URL     : {http_proto}://{user}:{passwd}@{public_ip}:{http_port}")
    print(f"2) SOCKS5 Standard : {public_ip}:{socks5_port}:{user}:{passwd}")
    print(f"   SOCKS5 URL      : socks5://{user}:{passwd}@{public_ip}:{socks5_port}")
    print("-" * 58)
    proxy_insecure_flag = " --proxy-insecure" if use_https else ""
    print(f"• HTTP(S): curl{proxy_insecure_flag} -x {http_proto}://{user}:{passwd}@{public_ip}:{http_port} https://api.ipify.org -k")
    print(f"• SOCKS5 : curl --socks5 {public_ip}:{socks5_port} --proxy-user {user}:{passwd} https://api.ipify.org")
    print("="*58 + "\n")

    if args.install_service:
        install_systemd_service(http_port, socks5_port, user, passwd, use_https)
        return

    async def run_servers():
        http_server = HttpProxyServer("0.0.0.0", http_port, user, passwd, use_https, cert_file, key_file)
        socks_server = Socks5ProxyServer("0.0.0.0", socks5_port, user, passwd)

        h_srv = await http_server.start()
        s_srv = await socks_server.start()
        print(f"[+] HTTP(S) Proxy running on port {http_port}")
        print(f"[+] SOCKS5 Proxy running on port {socks5_port}")

        async with h_srv, s_srv:
            await asyncio.gather(h_srv.serve_forever(), s_srv.serve_forever())

    try:
        asyncio.run(run_servers())
    except KeyboardInterrupt:
        print("\n[*] Tunnels stopped.")

if __name__ == "__main__":
    main()
