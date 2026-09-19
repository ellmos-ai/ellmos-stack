# Third-Party Licenses & Software Bill of Materials (SBOM)

> **Level 1 SBOM and Governance Inventory for `ellmos-stack`**  
> Canonical repository: [ellmos-ai/ellmos-stack](https://github.com/ellmos-ai/ellmos-stack)  
> Umbrella ecosystem: [open-bricks](https://github.com/open-bricks)  
> Audit Date: 2026-09-19  
> Target Release: v0.1.1  

---

## 1. Executive Summary & Non-Elevation Certification

`ellmos-stack` is a self-hosted, local-first artificial intelligence research and knowledge-management stack. It integrates local inference engines, workflow automation, curated and organic agent memory, task management, and private document search.

### Non-Elevation Invariant (`RunAsInvoker`)
- **Certification**: All runtime services, Python CLI scripts, and utility modules within this repository run under standard user privileges (`RunAsInvoker`).
- **No Mandatory Elevation**: Neither administrative (`Administrator` on Windows) nor `root` privileges (on Linux) are required to execute the Python runtime, run unit/smoke tests, or interact with APIs.
- **Service Isolation**: In production installations (`/opt/ellmos-stack`), services run under a dedicated unprivileged system account (`ellmos-stack`), and configuration credentials are restricted to file mode `0600`. Docker daemon access is handled via standard socket group permissions without exposing root login shells.

---

## 2. Software Bill of Materials (Level 1 SBOM)

### 2.1 Core Orchestration & Container Engines

| Component | Role | License | Homepage / Source |
|-----------|------|---------|-------------------|
| **Ollama** | Local LLM inference engine | MIT License | [github.com/ollama/ollama](https://github.com/ollama/ollama) |
| **n8n** | Workflow automation engine | Fair-code (Sustainable Use License) | [github.com/n8n-io/n8n](https://github.com/n8n-io/n8n) |
| **PostgreSQL** | Relational database (optional n8n backend) | PostgreSQL License | [postgresql.org](https://www.postgresql.org) |

### 2.2 Specialized Stack Modules (Pinned Git Components)

| Component | Role | Schema Role | License | Repository |
|-----------|------|-------------|---------|------------|
| **USMC** | Curated agent memory | `memory.curated` | MIT License | [ellmos-ai/usmc](https://github.com/ellmos-ai/usmc) |
| **GARDENER** | Organic memory substrate | `memory.organic` | MIT License | [ellmos-ai/gardener](https://github.com/ellmos-ai/gardener) |
| **task-master** | Dedicated task state | `tasks.default` | MIT License | [ellmos-ai/task-master](https://github.com/ellmos-ai/task-master) |
| **KnowledgeDigest** | Document ingestion & search | `knowledge.search.default` | MIT License | [file-bricks/knowledgedigest](https://github.com/file-bricks/knowledgedigest) |

### 2.3 Python Runtime & Dependencies

| Package | Version Range | License | Role |
|---------|---------------|---------|------|
| **Python** | >=3.10 | PSF-2.0 | Core runtime environment and standard library |
| **PyYAML** | >=6.0 | MIT License | Configuration and Docker Compose manifest parsing |
| **pytest** | >=7.0 (dev) | MIT License | Automated contract and regression test runner |
| **ruff** | >=0.4 (dev) | MIT / Apache-2.0 | Static analysis and code hygiene linting |

### 2.4 External Research APIs

| Service | Protocol | Access Terms | Role |
|---------|----------|--------------|------|
| **PubMed E-utilities** | HTTPS REST | NLM/NCBI Public Domain & Data API Terms | Academic biomedical literature metadata retrieval |
| **arXiv API** | HTTPS Atom | arXiv.org Terms of Use (Cornell University) | Open-access scientific preprint metadata retrieval |

---

## 3. Governance Invariants (INV-LOCAL-01 through INV-SLA-10)

The following ten operational invariants are enforced across the codebase, installation scripts, and continuous integration pipelines:

1. **`INV-LOCAL-01` (Zero Default Egress)**: Local LLM inference via Ollama, local memory storage (USMC, GARDENER), and document databases (KnowledgeDigest) never transmit user data to external cloud providers by default.
2. **`INV-LOCAL-02` (Restricted Filesystem Permissions)**: Secrets in `.env` are protected with file mode `0600`. Services operate in designated, isolated runtime directories.
3. **`INV-LOCAL-03` (No Hardcoded Credentials)**: The repository strictly forbids tracking API tokens, secrets, encryption keys, or authentication databases (`.env`, `*.key`, `*.pem`, `*.secret`, `*.db`).
4. **`INV-LOCAL-04` (Deterministic Module Pinning)**: All submodule components (USMC, GARDENER, task-master, KnowledgeDigest) are pinned to immutable 40-character Git commit hashes in `install.sh`.
5. **`INV-LOCAL-05` (Localhost Network Binding)**: Ollama (`127.0.0.1:11434`), n8n (`127.0.0.1:5678`), and KnowledgeDigest (`127.0.0.1:8787`) bind strictly to loopback interfaces by default.
6. **`INV-LOCAL-06` (Secured Remote Access)**: Any external access must utilize authenticated TLS reverse proxies or SSH tunnels. Plain HTTP exposure of administrative ports is explicitly prohibited.
7. **`INV-LOCAL-07` (Public Release Gate Verification)**: Every release candidate must pass all 27 static and evidence checks defined in `RELEASE_GATE.md` and verified by `tools/check_release_gate.py`.
8. **`INV-LOCAL-08` (Zero Copyleft Contagion Guarantee)**: The repository code and its direct subcomponents are distributed under the permissive MIT License; no GPL or AGPL viral copyleft requirements infect consuming applications.
9. **`INV-LOCAL-09` (Rehearsed Restore & Disaster Recovery)**: Backup, restore verification, and non-starting rollback procedures are formally codified and rehearsed according to `OPERATIONS.md`.
10. **`INV-LOCAL-10` (48-Hour Security Response SLA)**: Critical vulnerabilities reported in runtime components or dependencies are triaged within 48 hours and resolved via upstream patch or mitigation advisory.

---

## 4. License Texts Summary

- **MIT License**: Copyright (c) ellmos-ai / BACH Contributors. Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the Software without restriction.
- **Python Software Foundation License Version 2 (PSF-2.0)**: Governs Python runtime standard library usage.
- **PostgreSQL License**: Liberal open-source license similar to MIT/BSD.
- **Fair-code / Sustainable Use License**: Governs standalone n8n community distribution.
