# REPOSITORY IDENTITY & MISSION CONTRACT

## 1. Core Identity & Architectural Mission

- **Project Name**: `vps-to-vpn` (VPS Dual Tunnel & Proxy Deployer)
- **Primary Mission**: Deliver a zero-friction, single-command automated toolset that establishes dual-protocol proxy tunnels (HTTP/HTTPS CONNECT and RFC 1928/1929 SOCKS5) on remote Linux VPS instances, with automated multi-engine firewall traversal and resilient background service management.
- **Architectural Tenets**:
  1. **Zero External Runtime Dependencies on VPS**: Pure Python standard library (`asyncio`, `socket`, `struct`, `ssl`, `secrets`).
  2. **Hermetic Client Deployment**: Docker containerization (`python:3.11-alpine` + OpenSSH) providing deterministic local execution without polluting host environments.
  3. **Zero-Touch Security Automation**: Ephemeral credential isolation (`SSH_ASKPASS`), automated firewall rule configuration (`ufw`, `iptables`, `firewalld`), and constant-time token comparison (`secrets.compare_digest`).

---

## 2. Definitive Documentation Graph & Truth Matrix

```text
                                [ README.md ]
                     (Primary Operations & Entrypoint)
                                      │
        ┌───────────────────┬─────────┴─────────┬───────────────────┐
        ▼                   ▼                   ▼                   ▼
[ architecture.md ]  [ configuration.md ] [ api-reference.md ]  [ workflows.md ]
 (System Topology)   (Env Vars & Flags)  (Protocols & RFCs)    (Lifecycle / Ops)
        │                                                           │
        └───────────────────────────┬───────────────────────────────┘
                                    ▼
                        [ project-structure.md ]
                        (Layout & File Ownership)
                                    │
                                    ▼
                [ reports/documentation-drift-report.md ]
                  (Forensic Matrix & Coverage Scorecard)
```

---

## 3. Subsystem Ownership & Boundaries

| Component | Responsibility Domain | Authoritative Documentation |
| :--- | :--- | :--- |
| **Local Orchestrator** (`deploy_tunnel.py`) | Config ingestion (`.env`/CLI), SSH credential management, remote payload transmission | [`docs/architecture.md`](docs/architecture.md), [`docs/configuration.md`](docs/configuration.md) |
| **Remote Server** (`vps_tunnel.py`) | Async HTTP/HTTPS & SOCKS5 proxy serving, authentication, stream forwarding | [`docs/api-reference.md`](docs/api-reference.md), [`docs/architecture.md`](docs/architecture.md) |
| **Containerization Engine** (`Dockerfile`, `docker-compose.yml`) | Ephemeral client runtime packaging with environment variable mapping | [`docs/architecture.md`](docs/architecture.md), [`README.md`](README.md) |
| **Daemon & Firewall Infrastructure** | Multi-engine port management and systemd unit registration | [`docs/workflows.md`](docs/workflows.md) |

---

## 4. Contractual Invariants

1. **Protocol Compliance**: HTTP CONNECT per RFC 7231 / RFC 7617 Basic Auth; SOCKS5 per RFC 1928 & RFC 1929 Username/Password Subnegotiation.
2. **Deterministic Overwrite**: Redeploying on an active VPS cleanly terminates previous daemon instances, opens newly specified ports, and brings up the updated proxy without port contention.
3. **Source of Truth Rule**: All documentation strictly reflects the physical codebase reality verified by the Documentation Drift Matrix.
