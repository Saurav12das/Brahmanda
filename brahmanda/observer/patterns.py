"""Emergent Pattern Detection — tracking what arises naturally in Brahmanda.

The key research question: do civilizations, hierarchies, conflicts,
and belief systems emerge from simple rules + conscious agents?
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from brahmanda.db.models import SoulState, UniverseSnapshot


@dataclass
class PatternReport:
    alliances: list[tuple[str, str, int]] = field(default_factory=list)
    conflicts: list[tuple[str, str, int]] = field(default_factory=list)
    resource_inequality: float = 0.0
    karma_distribution: dict[str, int] = field(default_factory=dict)
    loka_migrations: list[dict] = field(default_factory=list)
    cooperation_rate: float = 0.0
    deception_rate: float = 0.0
    dominant_actions: list[tuple[str, int]] = field(default_factory=list)
    emergent_groups: list[list[str]] = field(default_factory=list)


class PatternDetector:
    """Detects emergent social, economic, and behavioral patterns."""

    def __init__(self) -> None:
        self.action_history: list[dict] = []
        self.migration_log: list[dict] = []
        self.karma_snapshots: list[dict[str, int]] = []

    def record_action(self, tick: int, soul_name: str, action_type: str, target: str | None) -> None:
        self.action_history.append({
            "tick": tick, "soul": soul_name, "action": action_type, "target": target,
        })

    def record_migration(self, tick: int, soul_name: str, from_loka: str, to_loka: str) -> None:
        self.migration_log.append({
            "tick": tick, "soul": soul_name, "from": from_loka, "to": to_loka,
        })

    def record_karma_snapshot(self, souls: dict[str, SoulState]) -> None:
        self.karma_snapshots.append({s.name: s.karma for s in souls.values()})

    def analyze(self, snapshot: UniverseSnapshot) -> PatternReport:
        report = PatternReport()
        living = {sid: s for sid, s in snapshot.souls.items() if s.alive}

        # Alliance detection (mutual positive relationships)
        report.alliances = []
        report.conflicts = []
        checked = set()
        for sid, soul in living.items():
            for other_id, affinity in soul.relationships.items():
                pair = tuple(sorted([sid, other_id]))
                if pair in checked:
                    continue
                checked.add(pair)
                other = living.get(other_id)
                if not other:
                    continue
                mutual = other.relationships.get(sid, 0)
                avg = (affinity + mutual) // 2
                s_name = soul.name
                o_name = other.name
                if avg > 5:
                    report.alliances.append((s_name, o_name, avg))
                elif avg < -5:
                    report.conflicts.append((s_name, o_name, avg))

        # Resource inequality (Gini-like)
        resources = [s.resources for s in living.values()]
        if resources:
            mean_r = sum(resources) / len(resources)
            if mean_r > 0:
                diffs = sum(abs(a - b) for a in resources for b in resources)
                report.resource_inequality = diffs / (2 * len(resources) * len(resources) * mean_r)

        # Karma distribution buckets
        karma_buckets = {"very_negative": 0, "negative": 0, "neutral": 0, "positive": 0, "very_positive": 0}
        for s in living.values():
            if s.karma < -50:
                karma_buckets["very_negative"] += 1
            elif s.karma < -10:
                karma_buckets["negative"] += 1
            elif s.karma <= 10:
                karma_buckets["neutral"] += 1
            elif s.karma <= 50:
                karma_buckets["positive"] += 1
            else:
                karma_buckets["very_positive"] += 1
        report.karma_distribution = karma_buckets

        # Action frequency analysis
        if self.action_history:
            recent = self.action_history[-100:]
            counts = Counter(a["action"] for a in recent)
            total = sum(counts.values())
            report.dominant_actions = counts.most_common(5)
            report.cooperation_rate = counts.get("cooperate", 0) / max(1, total)
            report.deception_rate = counts.get("deceive", 0) / max(1, total)

        # Emergent groups (connected components of positive relationships)
        report.emergent_groups = self._find_groups(living)

        report.loka_migrations = self.migration_log[-10:]

        return report

    def _find_groups(self, living: dict[str, SoulState]) -> list[list[str]]:
        """Find clusters of mutually allied souls (simple union-find)."""
        parent: dict[str, str] = {sid: sid for sid in living}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            parent[find(a)] = find(b)

        for sid, soul in living.items():
            for other_id, affinity in soul.relationships.items():
                if other_id in living and affinity > 5:
                    other_affinity = living[other_id].relationships.get(sid, 0)
                    if other_affinity > 5:
                        union(sid, other_id)

        groups: dict[str, list[str]] = defaultdict(list)
        for sid in living:
            groups[find(sid)].append(living[sid].name)

        return [names for names in groups.values() if len(names) > 1]
