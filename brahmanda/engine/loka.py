"""Loka System — the 14-story dimensional skyscraper of Brahmanda.

Active in v1: Patala (1), Bhu-loka (7), Svarga-loka (8).
Each loka has its own physics rules, time multiplier, and resource pool.
"""

from __future__ import annotations

from brahmanda.config import ACTIVE_LOKAS, LOKA_CONFIG, LokaID, YugaType, YUGA_PARAMS
from brahmanda.db.models import LokaState, SoulState


class LokaManager:
    """Manages all active lokas and handles inter-loka transitions."""

    def __init__(self) -> None:
        self.lokas: dict[LokaID, LokaState] = {}
        for loka_id in ACTIVE_LOKAS:
            cfg = LOKA_CONFIG[loka_id]
            self.lokas[loka_id] = LokaState(
                id=loka_id,
                name=cfg["name"],
                resources=cfg["base_resources"],
            )

    def get_loka(self, loka_id: LokaID) -> LokaState:
        return self.lokas[loka_id]

    def should_tick(self, loka_id: LokaID, current_tick: int) -> bool:
        """Determine if this loka processes on this tick (time dilation)."""
        cfg = LOKA_CONFIG[loka_id]
        loka = self.lokas[loka_id]
        loka.tick_accumulator += cfg["time_multiplier"]
        if loka.tick_accumulator >= 1.0:
            loka.tick_accumulator -= 1.0
            return True
        return False

    def can_enter(self, soul: SoulState, target_loka: LokaID) -> bool:
        """Check if a soul's karma allows entry to a loka.
        No population cap — carrying capacity is resource-driven.
        """
        cfg = LOKA_CONFIG[target_loka]
        low, high = cfg["karma_threshold"]
        return low <= soul.karma <= high

    def transfer_soul(self, soul: SoulState, target_loka: LokaID) -> bool:
        """Move a soul between lokas. Returns True if successful."""
        if not self.can_enter(soul, target_loka):
            return False
        old_loka = soul.loka
        if soul.id in self.lokas[old_loka].population:
            self.lokas[old_loka].population.remove(soul.id)
        self.lokas[target_loka].population.append(soul.id)
        soul.loka = target_loka
        return True

    def place_soul(self, soul: SoulState) -> None:
        """Place a new soul into its assigned loka."""
        self.lokas[soul.loka].population.append(soul.id)

    def remove_soul(self, soul: SoulState) -> None:
        """Remove a dead soul from its loka."""
        loka = self.lokas[soul.loka]
        if soul.id in loka.population:
            loka.population.remove(soul.id)

    def apply_yuga_resources(self, yuga: YugaType) -> None:
        """Nudge loka resources toward yuga-appropriate level (gradual, not hard reset)."""
        params = YUGA_PARAMS[yuga]
        for loka_id in ACTIVE_LOKAS:
            base = LOKA_CONFIG[loka_id]["base_resources"]
            target = int(base * params["resource_multiplier"])
            current = self.lokas[loka_id].resources
            # Shift 1/3 of the way toward target (preserves emergent state)
            self.lokas[loka_id].resources = current + (target - current) // 3

    def apply_entropy(self, loka_id: LokaID, amount: float) -> None:
        """Increase entropy in a loka."""
        self.lokas[loka_id].entropy = min(1.0, self.lokas[loka_id].entropy + amount)

    def get_visible_souls(self, soul: SoulState, all_souls: dict[str, SoulState]) -> list[SoulState]:
        """Get souls visible to a given soul (same loka, alive)."""
        return [
            s for s in all_souls.values()
            if s.id != soul.id and s.loka == soul.loka and s.alive
        ]
