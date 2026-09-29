# Dual VPS Tunnel & Proxy Deployer (HTTP/HTTPS + SOCKS5)

## 📌 Repository Identity & Purpose
This repository provides a single-command automated deployment solution for provisioning high-performance dual-protocol proxy tunnels (**HTTP/HTTPS CONNECT** and **RFC 1928/1929 SOCKS5**) on Linux VPS servers.

---

## 🧭 Codebase Guidelines for AI Agents

1. **Zero External Runtime Dependencies**: The proxy server `vps_tunnel.py` must only use the Python standard library (`asyncio`, `socket`, `struct`, `ssl`, `secrets`). Do not introduce third-party packages on the VPS side.
2. **Deterministic Orchestration**: `deploy_tunnel.py` manages remote VPS configuration over SSH with ephemeral askpass scripts. Never store plaintext credentials on disk after execution.
3. **Environment Source of Truth**: All configurable parameters originate from `.env` or CLI arguments and are defined in [`docs/configuration.md`](docs/configuration.md).
4. **Documentation Sync Discipline**: When modifying protocol logic, flags, or configuration variables, immediately synchronize the corresponding docs in `docs/` and log any drift in `docs/reports/documentation-drift-report.md`.

---

## 🗂️ Documentation Navigation

| Topic | Document Path |
| :--- | :--- |
| **System Architecture & Topology** | [`docs/architecture.md`](docs/architecture.md) |
| **Environment Variables & CLI Reference** | [`docs/configuration.md`](docs/configuration.md) |
| **Protocols & RFC Standards** | [`docs/api-reference.md`](docs/api-reference.md) |
| **Lifecycle, Systemd & Firewall Workflows** | [`docs/workflows.md`](docs/workflows.md) |
| **Repository Identity & Invariants** | [`docs/repository-identity.md`](docs/repository-identity.md) |
| **Physical Directory Layout** | [`docs/project-structure.md`](docs/project-structure.md) |
| **Documentation Drift Audit Matrix** | [`docs/reports/documentation-drift-report.md`](docs/reports/documentation-drift-report.md) |
