"""Tests for the Trusted Code Review Pipeline."""
import os
import sys
import json
import tempfile
from pathlib import Path

# Add project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import pytest

from agents.tools import analyze_repo, get_identity
from utilities.identity import AgentIdentity
from utilities.trust_score import TrustScoreLedger


class TestAnalyzeRepo:
    """Tests for the Planner Agent's analyze_repo tool."""

    def test_invalid_url_returns_error(self):
        """Invalid/non-existent repo URL should return error dict gracefully."""
        result = analyze_repo("https://github.com/nonexistent/repo-12345-does-not-exist")
        assert isinstance(result, dict)
        assert "error" in result

    def test_valid_repo_returns_structure(self):
        """A real (tiny) repo should return file analysis."""
        result = analyze_repo("https://github.com/vystartasv/agent-foundry")
        assert isinstance(result, dict)
        # Should have analysis, not error
        if "error" not in result:
            assert "total_files" in result
            assert "file_types" in result
            assert "key_files_found" in result
            assert isinstance(result["total_files"], int)
            assert result["total_files"] > 0
        # If clone fails (network), that's acceptable — just verify shape

    def test_returns_expected_keys(self):
        """All return paths should return a dict."""
        result = analyze_repo("https://github.com/nonexistent/repo")
        assert isinstance(result, dict)
        # Error path has "error", success path has "repo" + "total_files"
        assert "error" in result or ("repo" in result and "total_files" in result)


class TestAgentIdentity:
    """Tests for Ed25519 cryptographic identity."""

    def test_identity_creation(self):
        """Identity should create with an agent_id and derive a public key."""
        identity = AgentIdentity("test-agent")
        assert identity.agent_id == "test-agent"
        assert identity.public_key is not None
        assert len(identity.public_key) == 64  # Ed25519 hex-encoded public key = 64 chars

    def test_sign_and_verify(self):
        """Signed payload should verify against the same identity."""
        identity = AgentIdentity("test-agent-2")
        payload = {"action": "scan", "findings": 3}
        signature = identity.sign(payload)
        assert len(signature) > 0
        assert identity.verify(payload, signature)

    def test_tampered_payload_fails_verification(self):
        """Modified payload should NOT verify."""
        identity = AgentIdentity("test-agent-3")
        payload = {"action": "scan", "findings": 3}
        signature = identity.sign(payload)
        tampered = {"action": "scan", "findings": 999}
        assert not identity.verify(tampered, signature)

    def test_verify_with_public_key(self):
        """verify_with_public_key should work without shared state."""
        identity_a = AgentIdentity("agent-a")
        payload = {"result": "ok"}
        signature = identity_a.sign(payload)
        assert AgentIdentity.verify_with_public_key(
            identity_a.public_key, payload, signature
        )

    def test_different_key_fails_verification(self):
        """Signature from one agent should NOT verify against another's key."""
        agent_a = AgentIdentity("agent-a")
        agent_b = AgentIdentity("agent-b")
        payload = {"result": "ok"}
        signature = agent_a.sign(payload)
        assert not AgentIdentity.verify_with_public_key(
            agent_b.public_key, payload, signature
        )

    def test_deterministic_seed(self):
        """Same seed should produce same public key."""
        seed = "a" * 64  # 32 bytes hex
        id1 = AgentIdentity("test", seed_hex=seed)
        id2 = AgentIdentity("test", seed_hex=seed)
        assert id1.public_key == id2.public_key


class TestTrustScoreLedger:
    """Tests for the trust score ledger."""

    def test_record_and_summary(self):
        """Recording a rating should be reflected in the summary."""
        ledger = TrustScoreLedger()
        report = ledger.record(
            agent_id="test-agent",
            rated_by="archive",
            rating=4.5,
            success_rate=0.9,
            checks_passed=9,
            checks_total=10,
        )
        assert report.rating == 4.5
        assert report.tier in ("trusted", "caution", "untrusted")

        summary = ledger.summary()
        assert "test-agent" in str(summary)

    def test_tier_thresholds(self):
        """Trust tiers should follow expected thresholds."""
        ledger = TrustScoreLedger()
        high = ledger.record("high", "a", rating=5.0, success_rate=1.0,
                            checks_passed=10, checks_total=10)
        mid = ledger.record("mid", "a", rating=3.0, success_rate=0.7,
                           checks_passed=7, checks_total=10)
        low = ledger.record("low", "a", rating=1.0, success_rate=0.3,
                           checks_passed=3, checks_total=10)
        assert high.tier == "trusted"
        assert mid.tier == "caution"
        assert low.tier == "untrusted"


class TestGetIdentity:
    """Tests for the shared identity cache."""

    def test_returns_same_identity_on_repeat_calls(self):
        """get_identity should cache identities per agent name."""
        id1 = get_identity("security_agent")
        id2 = get_identity("security_agent")
        assert id1.public_key == id2.public_key

    def test_different_agents_get_different_identities(self):
        """Different agent names should produce different identities."""
        id1 = get_identity("planner")
        id2 = get_identity("security")
        assert id1.public_key != id2.public_key
