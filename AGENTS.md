# ADK Code Review Pipeline

A 4-agent multi-agent system built with Google ADK + A2A protocol, enhanced
with the Works With Agents stack (Ed25519 identity, trust scores, quality gates).

## Quick Context for Agents

- **Stack:** Python 3.11+, Google ADK >= 1.18.0, pynacl (Ed25519)
- **Entry points:** `clients/pipeline_client.py` (CLI), `servers/run_servers.py` (local/Cloud Run)
- **Tests:** `pytest` (where they exist)
- **Deploy:** `adk deploy cloud_run` (requires GOOGLE_CLOUD_PROJECT, GOOGLE_API_KEY)
- **License:** CC BY 4.0
- **Repo:** https://github.com/vystartasv/adk-code-review

## Architecture

```
agents/        — 4 ADK LlmAgents + SequentialAgent pipeline
servers/       — A2A server wrappers, local + Cloud Run deployment
clients/       — Pipeline orchestrator CLI
utilities/     — Ed25519 identity, quality gates, trust scores, A2A types
frontend/      — Dashboard HTML (light theme, no framework)
```

## Pipeline

```
Planner → Security Scanner → Quality Gate → Archive & Verify
```

All agent outputs are Ed25519-signed. Archive agent verifies the signature chain.
