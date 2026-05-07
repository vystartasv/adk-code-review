"""
Trust Score — Agent credit score for multi-agent systems.
Wires Works With Agents Trust Score SDK into the pipeline.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class TrustScoreReport:
    """A trust score report for an agent's output quality."""
    agent_id: str
    rated_by: str
    rating: float  # 0.0 - 5.0
    success_rate: float  # 0.0 - 1.0
    checks_passed: int
    checks_total: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tier: str = "unrated"

    def __post_init__(self):
        # When checks_total=0 (no measurable checks), tier is based purely on rating
        if self.checks_total == 0:
            if self.rating >= 4.0:
                self.tier = "trusted"
            elif self.rating >= 3.0:
                self.tier = "caution"
            else:
                self.tier = "untrusted"
        elif self.rating >= 4.0 and self.success_rate >= 0.8:
            self.tier = "trusted"
        elif self.rating >= 3.0 and self.success_rate >= 0.6:
            self.tier = "caution"
        else:
            self.tier = "untrusted"


class TrustScoreLedger:
    """In-memory trust score ledger for the code review pipeline."""

    def __init__(self):
        self._scores: dict[str, list[TrustScoreReport]] = {}

    def record(self, agent_id: str, rated_by: str, rating: float,
               success_rate: float, checks_passed: int, checks_total: int) -> TrustScoreReport:
        report = TrustScoreReport(
            agent_id=agent_id,
            rated_by=rated_by,
            rating=rating,
            success_rate=success_rate,
            checks_passed=checks_passed,
            checks_total=checks_total,
        )
        if agent_id not in self._scores:
            self._scores[agent_id] = []
        self._scores[agent_id].append(report)
        return report

    def get(self, agent_id: str) -> Optional[dict]:
        """Get the latest trust score for an agent."""
        if agent_id not in self._scores or not self._scores[agent_id]:
            return None
        latest = self._scores[agent_id][-1]
        return {
            "agent_id": latest.agent_id,
            "tier": latest.tier,
            "rating": latest.rating,
            "success_rate": latest.success_rate,
            "history": len(self._scores[agent_id]),
            "last_rated": latest.timestamp,
        }

    def summary(self) -> dict:
        """Get a summary of all agent trust scores."""
        return {
            agent_id: self.get(agent_id)
            for agent_id in self._scores
        }
