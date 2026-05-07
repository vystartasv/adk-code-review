# Trusted Code Review Pipeline — Dockerfile
# Multi-agent system on Google ADK + A2A + Cloud Run

FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# ADK requires an agent.py in the agents/ directory
# Point AGENT_PATH to the agents directory
ENV AGENT_PATH="/app/agents"

# Expose ADK web UI port
EXPOSE 8000

# Run with ADK web
CMD ["adk", "web", "--port", "8000", "--host", "0.0.0.0"]
