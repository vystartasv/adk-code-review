"""
Pipeline Client — Orchestrates the full 4-agent code review pipeline.
Sends a GitHub repo URL through Planner → Security → Quality → Archive.
"""
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from agents.tools import (
    analyze_repo,
    scan_security,
    run_quality_checks,
    rate_agents,
    verify_pipeline_signatures,
)


async def run_pipeline(repo_url: str) -> dict:
    """
    Run the full 4-agent pipeline on a GitHub repository.
    Returns the complete audited report with Ed25519 signatures and trust scores.
    """
    pipeline_id = f"cr-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    print(f"\n{'='*60}")
    print(f"  Trusted Code Review Pipeline — {pipeline_id}")
    print(f"  Target: {repo_url}")
    print(f"{'='*60}\n")

    pipeline_results = {}

    # ── Agent 1: Planner ────────────────────────────────────────────
    print("── Agent 1/4: Planner — Analyzing repository structure ──")
    plan = analyze_repo(repo_url)
    pipeline_results["planner"] = plan
    if "error" in plan:
        print(f"  ❌ Planner failed: {plan['error']}")
        return {"status": "failed", "stage": "planner", "error": plan["error"]}
    print(f"  ✓ Found {plan['total_files']} files, {len(plan['key_files_found'])} key files")
    print(f"  ✓ Primary language: {plan.get('primary_language', 'unknown')}")
    print(f"  ✓ Has tests: {plan.get('has_tests', False)}")

    # ── Agent 2: Security ────────────────────────────────────────────
    print("\n── Agent 2/4: Security — Scanning for vulnerabilities ──")
    security = scan_security(repo_url)
    pipeline_results["security"] = security
    if "error" in security:
        print(f"  ❌ Security scan failed: {security['error']}")
    else:
        print(f"  ✓ Findings: {security['findings_count']}")
        print(f"  ✓ Signed: Ed25519-{security.get('public_key', '')[:16]}...")
        for f in security.get("findings", []):
            print(f"    [{f['severity'].upper()}] {f['type']}: {f['file']}")

    # ── Agent 3: Quality ─────────────────────────────────────────────
    print("\n── Agent 3/4: Quality — Running quality gates ──")
    quality = run_quality_checks(repo_url)
    pipeline_results["quality"] = quality
    if "error" in quality:
        print(f"  ❌ Quality checks failed: {quality['error']}")
    else:
        print(f"  ✓ Score: {quality['score']}/100 ({quality['tier'].upper()})")
        for check in quality.get("checks", []):
            status = "✓" if check["passed"] else "✗"
            print(f"    {status} {check['check']}: {check['detail']}")

    # ── Agent 4: Archive & Verify ────────────────────────────────────
    print("\n── Agent 4/4: Archive — Rating agents + verifying signatures ──")
    ratings = rate_agents(pipeline_results)
    verification = verify_pipeline_signatures(pipeline_results, ratings)
    pipeline_results["archive"] = {
        "ratings": ratings,
        "verification": verification,
    }

    print(f"  ✓ Agents rated: {len(ratings.get('agent_ratings', {}))}")
    for agent, score in ratings.get("agent_ratings", {}).items():
        print(f"    {agent}: {score['tier'].upper()} (rating: {score['rating']}/5)")
    print(f"  ✓ Cryptographic verification: {'ALL VERIFIED' if verification['all_verified'] else 'ISSUES FOUND'}")

    # ── Final Report ─────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE")
    print(f"  Pipeline ID: {pipeline_id}")
    print(f"  Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Trust Score Chain: {len(ratings.get('agent_ratings', {}))} agents rated")
    print(f"  Signature Verification: {'PASSED' if verification['all_verified'] else 'FAILED'}")
    print(f"{'='*60}\n")

    return {
        "status": "completed",
        "pipeline_id": pipeline_id,
        "repo": repo_url,
        "results": pipeline_results,
        "verification": verification,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }


async def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Trusted Code Review Pipeline Client")
    parser.add_argument("repo_url", nargs="?", help="GitHub repository URL to review")
    parser.add_argument("--output", "-o", help="Save report to JSON file")
    args = parser.parse_args()

    repo_url = args.repo_url
    if not repo_url:
        repo_url = input("Enter GitHub repo URL to review: ").strip()

    result = await run_pipeline(repo_url)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Report saved to: {args.output}")

    return result


if __name__ == "__main__":
    asyncio.run(main())
