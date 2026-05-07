# Trusted Code Review Pipeline

**A 4-agent multi-agent system built with Google ADK + A2A protocol, enhanced with the Works With Agents stack.**

Enter a GitHub repo URL → 4 specialized agents analyze, scan, gate, and verify → get a cryptographically signed audit report with trust scores.

## Architecture

```
You: "Review this repo"
  │
  ├─ Agent 1: Planner (analyzes structure, creates review plan)
  ├─ Agent 2: Security Scanner (deep scan, Ed25519-signed findings)  
  ├─ Agent 3: Quality Gate (LICENSE/README/CI checks, produces score)
  └─ Agent 4: Archive & Verify (rates agents, verifies signatures, final report)
```

## Works With Agents Stack (plugged in)

| Layer | Component | How it's used |
|-------|-----------|---------------|
| L2 | Ed25519 Identity | Each agent signs its output with a cryptographic key |
| L4 | Handoff Protocol | Agents pass context with signed handoff payloads |
| L5 | Trust Score | Archive agent rates each agent's output quality |
| L6 | Execution Verification Gate | Cryptographic signature verification of all claims |
| L7 | Quality Gates | CODE checks: license, README, CI/CD, security posture |

## Quick Start

### Prerequisites

- Python 3.11+
- Google AI Studio API key ([get one here](https://aistudio.google.com/apikey))

### Install

```bash
git clone https://github.com/vystartasv/adk-code-review.git
cd adk-code-review
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your API key
export GOOGLE_API_KEY=your_key_here
```

### Run Locally

```bash
# Option 1: Run the pipeline directly
python clients/pipeline_client.py https://github.com/vystartasv/agent-foundry

# Option 2: ADK web UI (interactive chat)
adk web --port 8000
```

### Deploy to Cloud Run

```bash
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_CLOUD_LOCATION=us-central1
export GOOGLE_GENAI_USE_VERTEXAI=True

adk deploy cloud_run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --service_name=adk-code-review \
  --with_ui \
  .
```

## Project Structure

```
adk-code-review/
├── agents/
│   ├── agent.py         # 4 specialized agents + SequentialAgent pipeline
│   ├── tools.py         # Tool functions (analyze, scan, quality check, rate, verify)
│   └── __init__.py
├── servers/
│   ├── a2a_servers.py   # A2A Agent Card configs (Planner, Security, Quality, Archive)
│   ├── run_servers.py   # Local + Cloud Run deployment
│   └── __init__.py
├── clients/
│   ├── pipeline_client.py  # Orchestrates the full pipeline
│   └── __init__.py
├── utilities/
│   ├── identity.py      # Ed25519 cryptographic identity (from WWA stack)
│   ├── quality_gate.py  # Code quality gates (adapted from PyPI quality gate)
│   ├── trust_score.py   # Agent trust score ledger
│   ├── types2.py        # A2A protocol types
│   └── __init__.py
├── frontend/
│   └── index.html       # Dashboard with real-time pipeline visualization
├── Dockerfile
├── requirements.txt
└── README.md
```

## License

CC BY 4.0 — [Works With Agents](https://workswithagents.dev)
