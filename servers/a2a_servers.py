"""
A2A Server wrappers for the Trusted Code Review Pipeline.
Each agent gets its own A2A server on a dedicated port.
Uses the ADK's built-in A2A support where possible.
"""
import json
import logging
import os
import sys

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

# Import A2A types
from utilities.types2 import AgentCapabilities, AgentSkill, AgentCard


def planner_agent_card(host="0.0.0.0", port=8081):
    """Return A2A AgentCard config for the Planner Agent."""
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    )
    skill = AgentSkill(
        id="repo_analysis",
        name="Repository Analysis",
        description="Analyzes GitHub repository structure and creates a review plan",
        tags=["code-review", "planning", "repository-analysis"],
        examples=["Analyze this repo: https://github.com/owner/repo"],
    )
    agent_card = AgentCard(
        name="Planner Agent",
        description="Analyzes repository structure and creates a code review plan",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=capabilities,
        skills=[skill],
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
    )
    return {"card": agent_card, "port": port, "host": host}


def security_agent_card(host="0.0.0.0", port=8082):
    """Return A2A AgentCard config for the Security Scanner Agent."""
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    )
    skill = AgentSkill(
        id="security_scanning",
        name="Security Vulnerability Scanning",
        description="Deep scans repositories for security vulnerabilities with Ed25519-signed output",
        tags=["security", "vulnerability-scanning", "secrets-detection"],
        examples=["Scan this repo for security issues: https://github.com/owner/repo"],
    )
    agent_card = AgentCard(
        name="Security Scanner Agent",
        description="Scans repositories for security vulnerabilities with cryptographic output signing",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=capabilities,
        skills=[skill],
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
    )
    return {"card": agent_card, "port": port, "host": host}


def quality_agent_card(host="0.0.0.0", port=8083):
    """Return A2A AgentCard config for the Quality Gate Agent."""
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    )
    skill = AgentSkill(
        id="quality_gates",
        name="Code Quality Gates",
        description="Runs quality checks (LICENSE, README, CI/CD, security posture) and produces a score",
        tags=["quality", "code-review", "ci-cd", "documentation"],
        examples=["Check quality of this repo: https://github.com/owner/repo"],
    )
    agent_card = AgentCard(
        name="Quality Gate Agent",
        description="Runs quality gates and produces a scored repository report",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=capabilities,
        skills=[skill],
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
    )
    return {"card": agent_card, "port": port, "host": host}


def archive_agent_card(host="0.0.0.0", port=8084):
    """Return A2A AgentCard config for the Archive & Verification Agent."""
    capabilities = AgentCapabilities(
        streaming=True,
        pushNotifications=False,
        stateTransitionHistory=True,
    )
    skill = AgentSkill(
        id="verification_and_archive",
        name="Pipeline Verification & Archive",
        description="Rates agents, cryptographically verifies outputs, produces final audit report",
        tags=["verification", "audit", "trust-score", "archive"],
        examples=["Produce final audit report for pipeline run"],
    )
    agent_card = AgentCard(
        name="Archive & Verification Agent",
        description="Rates agent performance, verifies Ed25519 signatures, produces final audit",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        capabilities=capabilities,
        skills=[skill],
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
    )
    return {"card": agent_card, "port": port, "host": host}


def list_servers():
    """Return all A2A server configs for the pipeline."""
    return {
        "planner": planner_agent_card(),
        "security": security_agent_card(),
        "quality": quality_agent_card(),
        "archive": archive_agent_card(),
    }


if __name__ == "__main__":
    servers = list_servers()
    print(json.dumps(servers, indent=2, default=str))
