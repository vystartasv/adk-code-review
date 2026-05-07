"""
Agent tools for the Trusted Code Review Pipeline.
Each tool is a function that can be called by the LLM agents via ADK.
"""
import json
import os
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Import our stack components
from utilities.identity import AgentIdentity
from utilities.quality_gate import run_all_checks
from utilities.trust_score import TrustScoreLedger

# Global trust score ledger shared across agents
_score_ledger = TrustScoreLedger()

# Agent identities (regenerated per pipeline run for freshness)
_IDENTITIES: dict[str, AgentIdentity] = {}


def get_identity(agent_name: str) -> AgentIdentity:
    """Get or create an Ed25519 identity for an agent."""
    if agent_name not in _IDENTITIES:
        _IDENTITIES[agent_name] = AgentIdentity(f"adk-{agent_name}")
    return _IDENTITIES[agent_name]


def analyze_repo(repo_url: str) -> dict:
    """
    Clone and analyze a GitHub repository structure.
    Returns file counts, languages, and key metrics.
    This is the Planner Agent's primary tool.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo_url, tmpdir],
                          capture_output=True, text=True, check=True, timeout=60)
        except Exception as e:
            return {"error": f"Failed to clone: {e}"}

        # Count files by type
        extensions = {}
        total_files = 0
        for f in Path(tmpdir).rglob("*"):
            if f.is_file() and ".git" not in str(f):
                total_files += 1
                ext = f.suffix or "no-extension"
                extensions[ext] = extensions.get(ext, 0) + 1

        # Detect key files
        key_files = []
        for name in ["README.md", "LICENSE", "setup.py", "pyproject.toml",
                     "package.json", "Dockerfile", "Makefile",
                     ".github/workflows", "requirements.txt"]:
            if (Path(tmpdir) / name).exists():
                key_files.append(name)

        return {
            "repo": repo_url,
            "total_files": total_files,
            "file_types": dict(sorted(extensions.items(), key=lambda x: -x[1])[:10]),
            "key_files_found": key_files,
            "has_tests": any("test" in str(f).lower() for f in Path(tmpdir).rglob("*") if f.is_dir()),
            "primary_language": max(extensions, key=extensions.get) if extensions else "unknown",
        }


def scan_security(repo_url: str) -> dict:
    """
    Deep scan for security vulnerabilities: secrets, unsafe patterns, injection risks.
    The Security Agent's primary tool. Output is Ed25519-signed.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo_url, tmpdir],
                          capture_output=True, text=True, check=True, timeout=60)
        except Exception as e:
            return {"error": f"Failed to clone: {e}"}

        findings = []

        for py_file in Path(tmpdir).rglob("*.py"):
            try:
                content = py_file.read_text()
            except Exception:
                continue  # Skip unreadable files (binary, permissions) — not a security issue

            # Hardcoded secrets
            for match in re.finditer(
                r'(?:api_key|API_KEY|password|PASSWORD|secret|SECRET|token|TOKEN)\s*=\s*["\'][\w\-]{8,}["\']',
                content
            ):
                findings.append({
                    "type": "hardcoded_secret",
                    "file": str(py_file.relative_to(tmpdir)),
                    "line": content[:match.start()].count("\n") + 1,
                    "severity": "high",
                })

            # SQL injection patterns
            if re.search(r'(?:execute|cursor\.execute)\s*\(\s*["\'].*%s.*["\']|f["\'][^"\']*SELECT', content, re.IGNORECASE):
                findings.append({
                    "type": "sql_injection_risk",
                    "file": str(py_file.relative_to(tmpdir)),
                    "severity": "critical",
                })

            # Unsafe eval
            if re.search(r'eval\(.*input|exec\(.*request', content):
                findings.append({
                    "type": "dangerous_eval",
                    "file": str(py_file.relative_to(tmpdir)),
                    "severity": "critical",
                })

        # Check for exposed .env files
        for env_file in Path(tmpdir).rglob(".env"):
            if ".git" not in str(env_file):
                findings.append({
                    "type": "exposed_env",
                    "file": str(env_file.relative_to(tmpdir)),
                    "severity": "high",
                })

        # Produce signed security report
        identity = get_identity("security_agent")
        report = {
            "agent_id": identity.agent_id,
            "repo": repo_url,
            "findings_count": len(findings),
            "findings": findings[:20],  # Cap
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        report["signature"] = identity.sign(report)
        report["public_key"] = identity.public_key

        return report


def run_quality_checks(repo_url: str) -> dict:
    """
    Run all quality gates on the repository.
    Returns a scored quality report. Quality Agent's primary tool.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(["git", "clone", "--depth", "1", repo_url, tmpdir],
                          capture_output=True, text=True, check=True, timeout=60)
        except Exception as e:
            return {"error": f"Failed to clone: {e}"}

        return run_all_checks(tmpdir)


def rate_agents(pipeline_results: dict) -> dict:
    """
    Rate each agent's performance based on their outputs.
    Archive Agent's tool — produces the final trust score chain.
    """
    ratings = {}

    for agent_name, result in pipeline_results.items():
        if isinstance(result, dict):
            # Rating logic: each agent gets scored based on output quality
            has_error = "error" in result
            checks_passed = result.get("checks_passed", 0)
            checks_total = result.get("checks_total", 0)

            rating = 5.0
            if has_error:
                rating -= 2.0
            if checks_total > 0 and checks_passed < checks_total:
                rating -= 1.0

            # When checks_total=0 (e.g. Planner, Security have no quality gate checks),
            # success_rate defaults to 1.0 — nothing was checked, nothing failed.
            success_rate = checks_passed / checks_total if checks_total > 0 else 1.0

            report = _score_ledger.record(
                agent_id=agent_name,
                rated_by="archive_agent",
                rating=max(rating, 0.5),
                success_rate=success_rate,
                checks_passed=checks_passed,
                checks_total=checks_total,
            )
            ratings[agent_name] = {
                "tier": report.tier,
                "rating": report.rating,
                "success_rate": report.success_rate,
            }

    # Sign the trust score chain
    identity = get_identity("archive_agent")
    chain_report = {
        "agent_id": identity.agent_id,
        "pipeline_timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_ratings": ratings,
        "trust_score_ledger": _score_ledger.summary(),
    }
    chain_report["signature"] = identity.sign(chain_report)
    chain_report["public_key"] = identity.public_key

    return chain_report


def verify_pipeline_signatures(pipeline_results: dict, archive_report: dict = None) -> dict:
    """
    Cryptographically verify all Ed25519 signatures in the pipeline chain.
    This is the final verification step — L6 Execution Verification Gate.

    Uses the public key from each agent's output (not shared state), so it
    works correctly across process restarts and concurrent pipeline runs.
    """
    verification_results = {}

    # Check each pipeline result for signature + public key
    for result_key, output in pipeline_results.items():
        if not isinstance(output, dict):
            continue

        pubkey = output.get("public_key", "")
        sig = output.get("signature", "")

        if pubkey and sig:
            payload = {k: v for k, v in output.items() if k not in ("signature", "public_key")}
            try:
                valid = AgentIdentity.verify_with_public_key(pubkey, payload, sig)
            except Exception:
                valid = False

            verification_results[result_key] = {
                "agent_id": output.get("agent_id", result_key),
                "public_key": pubkey[:16] + "...",
                "signature_valid": valid,
                "crypto": "ed25519",
            }

    # Verify archive agent's signed trust score chain
    if archive_report and isinstance(archive_report, dict):
        apk = archive_report.get("public_key", "")
        asig = archive_report.get("signature", "")
        if apk and asig:
            payload = {k: v for k, v in archive_report.items() if k not in ("signature", "public_key")}
            try:
                valid = AgentIdentity.verify_with_public_key(apk, payload, asig)
            except Exception:
                valid = False
            verification_results["archive"] = {
                "agent_id": archive_report.get("agent_id", "archive"),
                "public_key": apk[:16] + "...",
                "signature_valid": valid,
                "crypto": "ed25519",
            }

    all_ok = all(
        v.get("signature_valid") in (True,)
        for v in verification_results.values()
    )

    return {
        "verified_agents": len(verification_results),
        "signed_agents": sum(1 for v in verification_results.values() if v.get("signature_valid") is True),
        "all_verified": all_ok,
        "details": verification_results,
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
    }
