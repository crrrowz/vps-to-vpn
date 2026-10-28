#!/usr/bin/env python3
"""
One-Click Remote VPS Dual Tunnel Deployer (HTTP/HTTPS & SOCKS5)
--------------------------------------------------------------
Reads configuration from .env or CLI / interactive prompts,
connects to the VPS via SSH, deploys the dual proxy tunnel,
opens firewall ports, configures systemd, and prints connection strings.
"""

import os
import sys
import getpass
import tempfile
import subprocess
import argparse
import secrets
import string

def load_env_vars(filepath=".env"):
    """Load configuration from .env file and merge with os.environ."""
    env_vars = {}
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    if key:
                        env_vars[key] = val
        except Exception:
            pass

    # Merge with system / docker environment variables (os.environ takes precedence if set)
    for k, v in os.environ.items():
        if v is not None and v != "":
            env_vars[k] = v

    return env_vars

def generate_random_string(length=10):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def run_ssh_command(host, port, user, password, remote_cmd):
    """Executes a command via standard ssh client using temporary askpass."""
    is_windows = sys.platform.startswith("win")
    devnull_path = "NUL" if is_windows else "/dev/null"
    
    if is_windows:
        askpass_file = os.path.join(tempfile.gettempdir(), f"askpass_{secrets.token_hex(4)}.bat")
        with open(askpass_file, "w") as f:
            f.write(f'@"{sys.executable}" -c "import os; print(os.environ.get(\'SSH_TEMP_PASS\', \'\'))"\n')
    else:
        askpass_file = os.path.join(tempfile.gettempdir(), f"askpass_{secrets.token_hex(4)}.sh")
        with open(askpass_file, "w") as f:
            f.write('#!/bin/sh\nprintf "%s\\n" "$SSH_TEMP_PASS"\n')
        os.chmod(askpass_file, 0o700)

    env = os.environ.copy()
    env["SSH_ASKPASS"] = askpass_file
    env["SSH_ASKPASS_REQUIRE"] = "force"
    env["SSH_TEMP_PASS"] = password
    env["DISPLAY"] = "dummy:0"

    ssh_cmd = [
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", f"UserKnownHostsFile={devnull_path}",
        "-o", "PreferredAuthentications=password",
        "-o", "PubkeyAuthentication=no",
        f"{user}@{host}",
        remote_cmd
    ]

    try:
        proc = subprocess.Popen(
            ssh_cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        out, err = proc.communicate()
        return proc.returncode == 0, out, err
    finally:
        try:
            if os.path.exists(askpass_file):
                os.remove(askpass_file)
        except Exception:
            pass

def main():
    print("==========================================================")
    print("   AUTO VPS DUAL TUNNEL DEPLOYER (HTTP/HTTPS + SOCKS5)    ")
    print("==========================================================")

    # 1. Load .env and environment variables
    env = load_env_vars()

    parser = argparse.ArgumentParser(description="Deploy VPS Dual Tunnel automatically via SSH")
    parser.add_argument("--host", default=env.get("VPS_HOST"), help="VPS IP or Hostname")
    parser.add_argument("--ssh-port", type=int, default=int(env.get("SSH_PORT", 22)), help="SSH Port (default: 22)")
    parser.add_argument("--ssh-user", default=env.get("SSH_USER", "root"), help="SSH Username (default: root)")
    parser.add_argument("--ssh-pass", default=env.get("SSH_PASS"), help="SSH Password")
    
    parser.add_argument("--http-port", type=int, default=int(env.get("HTTP_PORT", 8443)), help="HTTP(S) Port (default: 8443)")
    parser.add_argument("--socks5-port", type=int, default=int(env.get("SOCKS5_PORT", 1080)), help="SOCKS5 Port (default: 1080)")
    parser.add_argument("--proxy-user", default=env.get("PROXY_USER") or None, help="Proxy Username (auto-generated if empty)")
    parser.add_argument("--proxy-pass", default=env.get("PROXY_PASS") or None, help="Proxy Password (auto-generated if empty)")
    parser.add_argument("--https", action="store_true", default=env.get("ENABLE_HTTPS", "").lower() in ("true", "1", "yes"), help="Enable HTTPS (TLS) proxy")

    args = parser.parse_args()

    # Determine Host & Credentials
    host = args.host or input("[?] VPS IP Address: ").strip()
    ssh_port = args.ssh_port
    ssh_user = args.ssh_user or input("[?] SSH Username [root]: ").strip() or "root"
    ssh_pass = args.ssh_pass or getpass.getpass("[?] SSH Password: ").strip()

    http_port = args.http_port
    socks5_port = args.socks5_port
    proxy_user = args.proxy_user or f"user_{generate_random_string(6)}"
    proxy_pass = args.proxy_pass or generate_random_string(12)
    https_flag = "--https" if args.https else ""

    print(f"\n[*] Target VPS       : {host}:{ssh_port}")
    print(f"[*] HTTP Port        : {http_port}")
    print(f"[*] SOCKS5 Port      : {socks5_port}")
    print(f"[*] Proxy User       : {proxy_user}")
    print(f"[*] Connecting to VPS and deploying dual tunnel service...")

    # Read vps_tunnel.py payload
    tunnel_script_path = os.path.join(os.path.dirname(__file__), "vps_tunnel.py")
    if os.path.exists(tunnel_script_path):
        with open(tunnel_script_path, "rb") as f:
            raw_code = f.read()
    else:
        print("[-] Error: vps_tunnel.py file not found.")
        sys.exit(1)

    import base64
    encoded_script = base64.b64encode(raw_code).decode("ascii")

    full_remote_cmd = (
        f"echo '{encoded_script}' | base64 -d > /root/vps_tunnel.py && "
        f"python3 /root/vps_tunnel.py --http-port {http_port} --socks5-port {socks5_port} "
        f"--user {proxy_user} --pass {proxy_pass} {https_flag} --install-service"
    )

    success, out, err = run_ssh_command(host, ssh_port, ssh_user, ssh_pass, full_remote_cmd)

    if success:
        print("\n" + out)
        print("[+] Deployment Complete! Both HTTP(S) and SOCKS5 proxies are live and active.")
    else:
        print(f"[-] Deployment failed:\n{err}\n{out}")

if __name__ == "__main__":
    main()
