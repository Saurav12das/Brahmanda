"""Karma Engine — action-consequence tracker and samsara (rebirth) logic."""

from __future__ import annotations

import random

from brahmanda.config import (
    DEFAULT_LOKA,
    KARMA_ACTIONS,
    KARMA_DECAY_RATE,
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

    def decay_karma(self, soul: SoulState) -> None:
        """Karma naturally decays toward 0 each tick — nothing is permanent."""
        if soul.karma > 0:
            soul.karma = max(0, soul.karma - max(1, int(soul.karma * KARMA_DECAY_RATE)))
        elif soul.karma < 0:
            soul.karma = min(0, soul.karma + max(1, int(abs(soul.karma) * KARMA_DECAY_RATE)))

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
        """Process samsara — soul dies and is reborn with karma carryover + mutations.

        Each rebirth introduces random mutations:
        - Vices (klesha): small random drift, influenced by past-life karma
        - Desires: chance to gain/lose/swap desires based on past-life experience
        - Skills: chance to gain a new skill or lose one (knowledge isn't guaranteed)
        This models spiritual evolution — souls can grow OR degrade across lives.
        """
        new_loka = self.determine_rebirth_loka(soul)
        carried_karma = int(soul.karma * 0.7)

        # --- MUTATION: Vices ---
        # Karma influences vice drift direction:
        #   Positive karma → vices tend to decrease (spiritual growth)
        #   Negative karma → vices tend to increase (deeper corruption)
        karma_bias = -0.05 if soul.karma > 20 else 0.05 if soul.karma < -20 else 0.0

        # Each vice mutates independently
        k = soul.klesha
        soul.klesha = type(k)(
            kama=max(0.05, min(1.0, k.kama + random.uniform(-0.1, 0.1) + karma_bias)),
            krodha=max(0.05, min(1.0, k.krodha + random.uniform(-0.1, 0.1) + karma_bias)),
            lobha=max(0.05, min(1.0, k.lobha + random.uniform(-0.1, 0.1) + karma_bias)),
            moha=max(0.05, min(1.0, k.moha + random.uniform(-0.1, 0.1) + karma_bias)),
            ahamkara=max(0.05, min(1.0, k.ahamkara + random.uniform(-0.1, 0.1) + karma_bias)),
        )

        # --- MUTATION: Desires ---
        # 30% chance to mutate a desire based on past-life actions
        if random.random() < 0.3 and soul.desires:
            _ALL_DESIRES = [
                "seek knowledge", "accumulate power", "find love", "protect the weak",
                "transcend suffering", "build legacy", "uncover truth", "dominate rivals",
                "achieve immortality", "serve dharma", "explore the unknown", "create beauty",
                "seek revenge", "hoard wealth", "indulge senses", "escape this world",
                "find meaning", "destroy enemies", "attain peace", "gain followers",
            ]
            mutation_type = random.choice(["swap", "add", "intensify"])
            if mutation_type == "swap" and len(soul.desires) > 0:
                # Replace a random desire with a new one
                idx = random.randint(0, len(soul.desires) - 1)
                new_desire = random.choice([d for d in _ALL_DESIRES if d not in soul.desires])
                soul.desires[idx] = new_desire
            elif mutation_type == "add" and len(soul.desires) < 4:
                new_desire = random.choice([d for d in _ALL_DESIRES if d not in soul.desires])
                soul.desires.append(new_desire)
            # "intensify" — keep same desires but they carry more weight (no change needed)

        # --- MUTATION: Skills ---
        # 20% chance to gain or lose a skill
        if random.random() < 0.2:
            _ALL_SKILLS = [
                "persuasion", "crafting", "meditation", "combat", "healing",
                "diplomacy", "stealth", "teaching", "strategy", "oration",
                "survival", "trade", "intimidation", "empathy", "deception",
            ]
            if random.random() < 0.6 and len(soul.skills) < 4:
                # Gain a skill
                new_skill = random.choice([s for s in _ALL_SKILLS if s not in soul.skills])
                soul.skills.append(new_skill)
            elif soul.skills:
                # Lose a skill (forgotten across lives)
                soul.skills.pop(random.randint(0, len(soul.skills) - 1))

        # --- Standard rebirth ---
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

        # Handle fight first (before the loop matches fight_justified/fight_unjustified)
        if "fight" in raw:
            if any(w in raw for w in ("justified", "defend", "protect", "righteous", "duty")):
                return "fight_justified"
            return "fight_unjustified"

        # Exact match first
        if raw in KARMA_ACTIONS:
            return raw

        # Synonym / fuzzy matching
        SYNONYMS = {
            "cooperate": ["cooperate", "collaborate", "work together", "help", "assist", "ally", "join"],
            "trade": ["trade", "exchange", "barter", "deal", "negotiate"],
            "create": ["create", "build", "craft", "construct", "invent", "make"],
            "meditate": ["meditate", "reflect", "contemplate", "pray", "seek wisdom", "introspect"],
            "share": ["share", "give", "donate", "offer", "gift", "distribute"],
            "teach": ["teach", "instruct", "guide", "mentor", "educate", "enlighten"],
            "deceive": ["deceive", "lie", "trick", "manipulate", "betray", "mislead", "cheat"],
            "steal": ["steal", "rob", "take", "pilfer", "loot", "plunder"],
            "hoard": ["hoard", "accumulate", "stockpile", "gather", "amass", "collect greedily"],
            "explore": ["explore", "wander", "travel", "search", "discover", "venture", "move"],
            "neutral": ["neutral", "observe", "wait", "rest", "nothing", "idle", "watch", "do nothing"],
        }
        for action_type, keywords in SYNONYMS.items():
            for kw in keywords:
                if kw in raw:
                    return action_type

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
