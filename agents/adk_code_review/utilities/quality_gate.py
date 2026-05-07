"""
Code Quality Gates — Adapted from Works With Agents PyPI quality gate.
Checks a codebase for common issues before it passes through the agent pipeline.
"""
import re
import subprocess
import urllib.request
from pathlib import Path
from typing import Optional


def check_license(repo_path: str) -> dict:
    """Check if the repository has a recognizable license file."""
    license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "COPYING"]
    found = []
    for f in license_files:
        if (Path(repo_path) / f).exists():
            found.append(f)
    return {
        "check": "license",
        "passed": len(found) > 0,
        "detail": f"Found: {', '.join(found)}" if found else "No LICENSE file found"
    }


def check_readme(repo_path: str) -> dict:
    """Check if the repository has a README with sufficient content."""
    readme_files = ["README.md", "README.rst", "README.txt", "README"]
    for f in readme_files:
        path = Path(repo_path) / f
        if path.exists():
            content = path.read_text()
            issues = []

            # Check for broken badge links
            badges = re.findall(r'\[!\[.*?\]\(.*?\)\]\(\)', content)
            if badges:
                issues.append(f"{len(badges)} badge(s) with empty link targets")

            # Check for placeholder git clone
            clones = re.findall(r'git clone ([\S]+)', content)
            for clone in clones:
                if "<" in clone or clone in ("<repo-url>", "<url>", "<repo>"):
                    issues.append(f"git clone uses placeholder: '{clone}'")

            # Check pip install matches package name
            # (simplified — just check there IS a pip install command)
            has_pip = bool(re.search(r'pip install', content))
            if not has_pip and "python" in content.lower():
                issues.append("No pip install instructions found")

            return {
                "check": "readme",
                "passed": len(issues) == 0,
                "detail": f"README {f} found, {len(content)} chars",
                "issues": issues
            }
    return {"check": "readme", "passed": False, "detail": "No README found"}


def check_gitignore(repo_path: str) -> dict:
    """Check if .gitignore exists and covers common patterns."""
    gitignore = Path(repo_path) / ".gitignore"
    if not gitignore.exists():
        return {"check": "gitignore", "passed": False, "detail": "No .gitignore found"}

    content = gitignore.read_text().lower()
    missing = []
    for pattern in ["*.pyc", "__pycache__", ".env", "dist/", ".venv"]:
        if pattern.lower() not in content:
            missing.append(pattern)

    return {
        "check": "gitignore",
        "passed": len(missing) == 0,
        "detail": f"Missing patterns: {missing}" if missing else "Well-configured"
    }


def check_security(repo_path: str) -> dict:
    """Scan for common security issues in the codebase."""
    issues = []
    for py_file in Path(repo_path).rglob("*.py"):
        try:
            content = py_file.read_text()
        except Exception:
            continue  # Skip unreadable files (binary, permissions) — not a quality issue

        # Hardcoded secrets
        if re.search(r'(api_key|password|secret|token)\s*=\s*["\'][\w\-]{8,}', content):
            issues.append(f"Hardcoded secret in {py_file.name}")

        # Dangerous eval/exec
        if "eval(" in content and "input" in content:
            issues.append(f"Potentially dangerous eval() in {py_file.name}")

        # Empty except blocks
        if re.search(r'except\s+\w+:\s*\n\s+(pass|continue)', content) and \
           "suppress" not in content.lower():
            issues.append(f"Silent exception in {py_file.name}")

    return {
        "check": "security",
        "passed": len(issues) == 0,
        "detail": f"Found {len(issues)} potential issues" if issues else "Clean",
        "issues": issues[:10]  # Cap at 10
    }


def check_github_actions(repo_path: str) -> dict:
    """Check if CI/CD is configured."""
    ci_paths = [
        ".github/workflows",
        ".gitlab-ci.yml",
        "Jenkinsfile",
        "azure-pipelines.yml"
    ]
    for p in ci_paths:
        if (Path(repo_path) / p).exists():
            return {"check": "ci_cd", "passed": True, "detail": f"Found: {p}"}
    return {"check": "ci_cd", "passed": False, "detail": "No CI/CD configuration found"}


def run_all_checks(repo_path: str) -> dict:
    """Run all quality gates on a repository. Returns scored report."""
    checks = [
        check_license(repo_path),
        check_readme(repo_path),
        check_gitignore(repo_path),
        check_security(repo_path),
        check_github_actions(repo_path),
    ]

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round((passed / total) * 100)

    tier = "trusted" if score >= 80 else "caution" if score >= 60 else "untrusted"

    return {
        "repository": repo_path,
        "total_checks": total,
        "checks_passed": passed,
        "score": score,
        "tier": tier,
        "checks": checks,
    }
