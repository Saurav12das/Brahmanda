"""Karma Engine — action-consequence tracker and samsara (rebirth) logic."""

from __future__ import annotations

import random

from brahmanda.config import (
    DEFAULT_LOKA,
    KARMA_ACTIONS,
    SAMSARA_KARMA_RANGES,
    LokaID,
    YugaType,
    YUGA_PARAMS,
)
from brahmanda.db.models import Action, SoulState


class KarmaEngine:
    """Scores actions, accumulates karma, and determines rebirth."""

    def score_action(self, action_type: str, yuga: YugaType, context: dict | None = None) -> int:
        """Calculate karma delta for an action, scaled by current yuga."""
        base = KARMA_ACTIONS.get(action_type, 0)
        multiplier = YUGA_PARAMS[yuga]["karma_multiplier"]
        # In Kali Yuga, even small good deeds are amplified (mercy rule)
        if yuga == YugaType.KALI and base > 0:
            multiplier *= 1.5
        return int(base * multiplier)

    def apply_karma(self, soul: SoulState, delta: int) -> None:
        """Apply karma delta to a soul, clamped to [-200, 200]."""
        soul.karma = max(-200, min(200, soul.karma + delta))

    def should_die(self, soul: SoulState, tick: int) -> bool:
        """Determine if a soul dies this tick (age + karma-weighted probability)."""
        if soul.age < 10:
            return False
        # Base mortality increases with age, very negative karma shortens life
        base_chance = (soul.age - 10) * 0.02
        karma_factor = max(0, -soul.karma) * 0.005
        return random.random() < (base_chance + karma_factor)

    def determine_rebirth_loka(self, soul: SoulState) -> LokaID:
        """Based on accumulated karma, determine which loka the soul is reborn in."""
        for loka_id, (low, high) in SAMSARA_KARMA_RANGES.items():
            if low <= soul.karma <= high:
                return loka_id
        return DEFAULT_LOKA

    def rebirth(self, soul: SoulState) -> SoulState:
        """Process samsara — soul dies and is reborn with karma carryover."""
        new_loka = self.determine_rebirth_loka(soul)
        # Karma partially carries over (70% retained across lives)
        carried_karma = int(soul.karma * 0.7)
        soul.alive = True
        soul.age = 0
        soul.lives += 1
        soul.loka = new_loka
        soul.karma = carried_karma
        soul.resources = 10
        soul.memories = soul.memories[-3:]  # faint past-life memories
        soul.relationships = {}
        soul.is_avatar = False
        soul.avatar_mission = None
        return soul

    def classify_action(self, raw_action: str) -> str:
        """Map a raw LLM action string to a known action type."""
        raw = raw_action.lower().strip()
        for action_type in KARMA_ACTIONS:
            if action_type in raw:
                return action_type
        # Handle fight variants
        if "fight" in raw:
            if "justified" in raw or "defend" in raw or "protect" in raw:
                return "fight_justified"
            return "fight_unjustified"
        return "neutral"

    def create_action_record(
        self, tick: int, soul: SoulState, action_type: str,
        target_id: str | None, description: str, yuga: YugaType,
    ) -> Action:
        """Create a scored action record."""
        delta = self.score_action(action_type, yuga)
        self.apply_karma(soul, delta)
        return Action(
            tick=tick,
            soul_id=soul.id,
            action_type=action_type,
            target_id=target_id,
            description=description,
            karma_delta=delta,
            loka=soul.loka,
        )
