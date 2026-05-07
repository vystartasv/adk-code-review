"""
Run all 4 A2A servers for the Trusted Code Review Pipeline.
Uses ADK's built-in A2A deployment support: adk web or adk deploy cloud_run
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import utilities.config  # noqa: E402 — auto-injects GOOGLE_API_KEY from credential proxy


def run_local():
    """Run all agents locally using ADK's web UI."""
    logger.info("Starting Trusted Code Review Pipeline (ADK web mode)")
    logger.info("Agents: Planner → Security → Quality → Archive")
    logger.info("Ed25519 signing: ENABLED")
    logger.info("Access the web UI at http://localhost:8000")

    # ADK's web command serves the agent from the current directory
    subprocess.run(
        ["adk", "web", "--port", "8000", "--host", "0.0.0.0"],
        cwd=project_root,
        env={**os.environ, "GOOGLE_GENAI_USE_VERTEXAI": "False"},
    )


def deploy_cloud_run():
    """Deploy to Google Cloud Run using ADK's built-in deployment."""
    project = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    region = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    service_name = os.environ.get("SERVICE_NAME", "adk-code-review")

    if not project:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable required")
        sys.exit(1)

    logger.info(f"Deploying to Cloud Run: {project}/{region}/{service_name}")

    cmd = [
        "adk", "deploy", "cloud_run",
        "--project", project,
        "--region", region,
        "--service_name", service_name,
        "--app_name", "agents",
        "--with_ui",
        ".",
    ]
    subprocess.run(cmd, cwd=project_root)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Trusted Code Review Pipeline")
    parser.add_argument("--deploy", action="store_true", help="Deploy to Cloud Run")
    parser.add_argument("--local", action="store_true", help="Run locally with web UI")
    args = parser.parse_args()

    if args.deploy:
        deploy_cloud_run()
    else:
        run_local()
