# Project Structure & Repository Physical Layout

This document describes the directory tree, file responsibilities, and architectural boundaries of the repository.

```text
vps-to-vpn/
├── .env                              # Active environment configuration (SSH & proxy credentials)
├── .env.example                      # Template for environment configuration
├── Dockerfile                        # Hermetic multi-platform deployment container (Python 3.11-alpine + OpenSSH)
├── docker-compose.yml                # Docker compose orchestration definition with .env cascading
├── deploy_tunnel.py                  # Local orchestration client (SSH transport, askpass automation, remote deploy)
├── vps_tunnel.py                     # Standalone dual-protocol proxy server (HTTP/HTTPS + SOCKS5, systemd, firewall)
├── README.md                         # Canonical entry point and quickstart guide
└── docs/                             # Deep-dive enterprise documentation
    ├── architecture.md               # System topology, component decomposition, concurrency & security invariants
    ├── configuration.md              # Complete .env and CLI flag specifications
    ├── api-reference.md              # HTTP CONNECT & RFC 1928/1929 SOCKS5 protocol specifications
    ├── workflows.md                  # Deployment lifecycle, service management, and firewall mechanics
    ├── project-structure.md          # Physical directory layout and file ownership (this file)
    └── reports/
        └── documentation-drift-report.md  # Audit matrix and coverage scorecard
```

---

## File Responsibilities

| File Path | Role & Responsibility | Execution Environment |
| :--- | :--- | :--- |
| `deploy_tunnel.py` | Orchestration script that reads `.env`/CLI, connects to VPS via SSH, and installs the server. | Local Machine / Docker Container |
| `vps_tunnel.py` | Asynchronous dual proxy server implementing HTTP/HTTPS and SOCKS5 authentication and traffic piping. | Remote VPS (Root / Systemd) |
| `Dockerfile` | Lightweight Alpine-based container packaging `deploy_tunnel.py` and OpenSSH client for zero-dependency execution. | Docker Engine |
| `docker-compose.yml` | Declarative container specification linking `.env` values and terminal interaction. | Docker Compose |
| `.env.example` | Canonical template for all required and optional configuration keys. | Reference |
| `README.md` | Primary operational guide for end-users covering Docker, Python, and direct VPS usage. | Documentation |
