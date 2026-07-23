# STACK-MAP — ellmos-stack composition blueprint

> Derived overview of what this stack is made of and which function each part
> serves. Canonical sources: [`stack.v2.json`](stack.v2.json) (machine-readable
> manifest, schema `ellmos.stack.v2`), [`docker-compose.yml`](docker-compose.yml),
> [`OPERATIONS.md`](OPERATIONS.md), [`RELEASE_GATE.md`](RELEASE_GATE.md).
> Update this map when the manifest or the compose file changes.

## Role in the stack family

ellmos-stack is the **public, self-hosted base layer** ("deployment chassis") of the
ellmos stack family: a local-first AI research kit. Higher editions nest it —
ellmos-stack ⊂ sovereign-private ⊂ sovereign-hosted.

## Map

```
                         USER / AGENT (localhost only by default)
                                        │
 ┌─ ellmos-stack ── Docker Compose, pinned images, Linux ────────────────────────────┐
 │                                                                                   │
 │  ┌─ Inference ─────────────┐   ┌─ Automation ────────────┐                        │
 │  │ Ollama (docker)         │   │ n8n (docker)            │                        │
 │  │ role: local-inference   │   │ role: automation        │                        │
 │  └─────────────────────────┘   └─────────────────────────┘                        │
 │                                                                                   │
 │  ┌─ Knowledge / RAG ───────────────────┐   ┌─ Memory & Tasks ─────────────┐       │
 │  │ KnowledgeDigest (module component)  │   │ rinnsal (pinned-git)         │       │
 │  │ role: knowledge.search.default      │   │ role: memory-and-tasks       │       │
 │  │ ingest → chunk → FTS5 → summarize   │   │ (legacy runtime)             │       │
 │  └─────────────────────────────────────┘   └──────────────────────────────┘       │
 │                                                                                   │
 │  ┌─ Included services (services/) ───────────────────────────────────────────┐    │
 │  │ research_pipeline  role: research   — paper search & processing           │    │
 │  │ auto_ingest        — feeds documents into KnowledgeDigest                 │    │
 │  │ process_summaries  — LLM summarization pass                               │    │
 │  │ telegram_gateway   — optional chat entry point                            │    │
 │  │ env_config         — environment/config plumbing                          │    │
 │  └───────────────────────────────────────────────────────────────────────────┘    │
 │                                                                                   │
 │  External literature APIs: pubmed · arxiv  (role: paper-search, https)            │
 └───────────────────────────────────────────────────────────────────────────────────┘
   Policies: local_first · network declared · max data sensitivity "user-local"
   Release gate: RELEASE_GATE.md + .github/workflows/release-gate.yml (pinned images)
```

## Component roles (from `stack.v2.json`)

| Component | Kind | Role | Source |
|---|---|---|---|
| KnowledgeDigest | module component | `knowledge.search.default` (RAG) | module registry |
| Ollama | model-runtime | local-inference | docker |
| n8n | workflow-engine | automation | docker |
| rinnsal | legacy-runtime | memory-and-tasks | pinned-git |
| research-pipeline | included-service | research | this repository |
| pubmed / arxiv | literature-api | paper-search | https |

## Deliberately out of scope

- Not a generic n8n starter kit, not an Open-WebUI-only setup, not a hosted agent
  platform (see README positioning).
- No remote access without TLS/auth — services bind to localhost by default.
- Multi-tenant, SSO, billing and hosted operations belong to the sovereign
  editions, not here.
