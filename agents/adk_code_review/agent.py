"""
Trusted Code Review Pipeline — 4 specialized AI agents using Google ADK + A2A.
Each agent has a focused role. Output is Ed25519-signed. Chain is cryptographically verifiable.

Pipeline: Planner → Security → Quality → Archive

Works With Agents stack plugged in:
  - L2 Identity (Ed25519 signing)
  - L4 Handoff (cryptographic handoff between agents)
  - L5 Trust Score (agent quality rating)
  - L6 Execution Verification Gate
  - L7 Quality Gates
"""
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.function_tool import FunctionTool

from .tools import (
    analyze_repo,
    scan_security,
    run_quality_checks,
    rate_agents,
    verify_pipeline_signatures,
)

# Create tool wrappers
planner_tool = FunctionTool(func=analyze_repo)
security_tool = FunctionTool(func=scan_security)
quality_tool = FunctionTool(func=run_quality_checks)
archive_rate_tool = FunctionTool(func=rate_agents)
archive_verify_tool = FunctionTool(func=verify_pipeline_signatures)

# ═══════════════════════════════════════════════════════════════════════
# Agent 1: Planner — Analyzes repo structure, creates review plan
# ═══════════════════════════════════════════════════════════════════════

planner_agent = LlmAgent(
    name="planner",
    model="gemini-2.5-flash",
    instruction="""You are the Planner Agent in a code review pipeline.
    Your role: analyze a GitHub repository and create a structured review plan.

    When you receive a repo URL:
    1. Use the analyze_repo tool to clone and inspect the repository
    2. Based on the analysis, create a review plan with clear sections:
       - What to check: file types found, primary language, test coverage
       - Security concerns: any suspicious patterns to investigate
       - Quality concerns: missing CI/CD, no license, bad README
    3. Pass your plan as structured output for the next agent

    Output format:
    ```json
    {
      "plan": "Brief summary of review plan",
      "sections": ["security", "quality", "documentation", "ci_cd"],
      "priority": "high|medium|low",
      "repo_analysis": <result from analyze_repo>
    }
    ```

    Be concise. Focus on actionable findings. Do not invent issues.
    """,
    description="Analyzes repository structure and creates a code review plan.",
    tools=[planner_tool],
)

# ═══════════════════════════════════════════════════════════════════════
# Agent 2: Security — Scans for vulnerabilities, signs output
# ═══════════════════════════════════════════════════════════════════════

security_agent = LlmAgent(
    name="security_scanner",
    model="gemini-2.5-flash",
    instruction="""You are the Security Agent in a code review pipeline.
    Your role: deep scan a repository for security vulnerabilities.

    Process:
    1. Receive the planner's analysis and plan
    2. Use the scan_security tool to deep-scan the repository
    3. Report all findings with severity levels (critical, high, medium)
    4. Your output is automatically Ed25519-signed for cryptographic attribution

    Focus on:
    - Hardcoded secrets and API keys
    - SQL injection risks
    - Unsafe eval/exec patterns
    - Exposed .env files
    - Missing security headers/configs

    Be thorough. Every finding must be actionable.
    """,
    description="Scans repositories for security vulnerabilities. Output is Ed25519-signed.",
    tools=[security_tool],
)

# ═══════════════════════════════════════════════════════════════════════
# Agent 3: Quality — Runs quality gates, produces a score
# ═══════════════════════════════════════════════════════════════════════

quality_agent = LlmAgent(
    name="quality_gate",
    model="gemini-2.5-flash",
    instruction="""You are the Quality Gate Agent in a code review pipeline.
    Your role: run quality checks and produce a repository quality score.

    Process:
    1. Receive the security agent's findings
    2. Use the run_quality_checks tool to evaluate the repository
    3. Based on the results, assign a quality tier: trusted (>80), caution (60-79), untrusted (<60)
    4. Explain what's missing and how to improve

    Checks include:
    - LICENSE file presence
    - README quality (badges, install instructions, git clone)
    - .gitignore configuration
    - CI/CD pipeline existence
    - Security posture (from security agent's report)

    Be constructive. Every issue should have a suggested fix.
    """,
    description="Runs quality gates on code and produces a scored report.",
    tools=[quality_tool],
)

# ═══════════════════════════════════════════════════════════════════════
# Agent 4: Archive — Timestamps, rates agents, produces verified final report
# ═══════════════════════════════════════════════════════════════════════

archive_agent = LlmAgent(
    name="archive_and_verify",
    model="gemini-2.5-flash",
    instruction="""You are the Archive & Verification Agent in a code review pipeline.
    Your role: produce the final verified audit report.

    Process:
    1. Receive all pipeline outputs (planner, security, quality)
    2. Use the rate_agents tool to assign trust scores to each agent
    3. Use the verify_pipeline_signatures tool to cryptographically verify all outputs
    4. Produce the final audit report with chain of trust

    The final report must include:
    - Pipeline summary (repo, timestamp, overall verdict)
    - Agent trust scores (tier, rating, success rate)
    - Cryptographic verification status
    - Key findings and recommendations

    This is the official audit trail. Make it professional and complete.
    """,
    description="Rates agents, verifies signatures, produces final audit report.",
    tools=[archive_rate_tool, archive_verify_tool],
)

# ═══════════════════════════════════════════════════════════════════════
# Pipeline: Sequential execution through all 4 agents
# ═══════════════════════════════════════════════════════════════════════

root_agent = SequentialAgent(
    name="trusted_code_review_pipeline",
    description=(
        "A 4-agent code review pipeline with Ed25519-signed outputs, "
        "trust scores, quality gates, and cryptographic verification. "
        "Enter a GitHub repo URL to get a signed audit report."
    ),
    sub_agents=[planner_agent, security_agent, quality_agent, archive_agent],
)
