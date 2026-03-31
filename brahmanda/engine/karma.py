"""Karma Engine — action-consequence tracker, prana mechanics, and samsara."""

from __future__ import annotations

import random

from brahmanda.config import (
    DEFAULT_LOKA,
    KARMA_ACTIONS,
    KARMA_DECAY_BASE_RATE,
    PRANA_AGE_DRAIN_ONSET,
    PRANA_AGE_DRAIN_RATE,
    PRANA_BASE_DRAIN,
    PRANA_ENTROPY_DRAIN_FACTOR,
    PRANA_MAX,
    PRANA_REPLENISH_RATE,
    PRANA_RESOURCE_CONVERSION,
    PRANA_VICE_DRAIN_FACTOR,
    SAMSARA_KARMA_RANGES,
    LokaID,
    YugaType,
    YUGA_PARAMS,
)
from brahmanda.db.models import Action, LokaState, SoulState


class KarmaEngine:
    """Scores actions, manages prana (life force), and determines rebirth."""

    # ------------------------------------------------------------------
    # Karma
    # ------------------------------------------------------------------
    def score_action(self, action_type: str, yuga: YugaType, context: dict | None = None) -> int:
        base = KARMA_ACTIONS.get(action_type, 0)
        multiplier = YUGA_PARAMS[yuga]["karma_multiplier"]
        if yuga == YugaType.KALI and base > 0:
            multiplier *= 1.5
        return int(base * multiplier)

    def apply_karma(self, soul: SoulState, delta: int) -> None:
        soul.karma = max(-200, min(200, soul.karma + delta))

    def decay_karma(self, soul: SoulState, loka_entropy: float, yuga: YugaType) -> None:
        """Karma decays toward 0 — rate scales with entropy, yuga, and vices."""
        base_rate = KARMA_DECAY_BASE_RATE
        entropy_factor = 1.0 + loka_entropy * 2.0
        yuga_factor = {"satya": 0.5, "treta": 0.8, "dvapara": 1.2, "kali": 1.8}[yuga.value]
        vice_factor = 1.0 + soul.klesha.total_darkness * 0.5

        rate = base_rate * entropy_factor * yuga_factor

        if soul.karma > 0:
            # Vices accelerate positive karma decay (hard to stay virtuous when corrupt)
            effective_rate = rate * vice_factor
            soul.karma = max(0, soul.karma - max(1, int(soul.karma * effective_rate)))
        elif soul.karma < 0:
            # Vices slow negative karma recovery (hard to redeem when corrupt)
            effective_rate = rate / vice_factor
            soul.karma = min(0, soul.karma + max(1, int(abs(soul.karma) * effective_rate)))

    # ------------------------------------------------------------------
    # Prana (Life Force) — replaces should_die
    # ------------------------------------------------------------------
    def drain_prana(self, soul: SoulState, loka_entropy: float, yuga: YugaType) -> float:
        """Drain prana each tick. Returns amount drained."""
        drain = PRANA_BASE_DRAIN
        drain += soul.klesha.total_darkness * PRANA_VICE_DRAIN_FACTOR
        drain += loka_entropy * PRANA_ENTROPY_DRAIN_FACTOR

        # Age factor — gradual increase after onset, not a cliff
        if soul.age > PRANA_AGE_DRAIN_ONSET:
            drain += (soul.age - PRANA_AGE_DRAIN_ONSET) * PRANA_AGE_DRAIN_RATE

        # Karma efficiency — positive karma reduces drain (up to 50%)
        karma_efficiency = max(0.5, 1.0 - soul.karma / 400.0)
        drain *= karma_efficiency

        # Avatars are more resilient
        if soul.is_avatar:
            drain *= 0.5

        soul.prana = max(0.0, soul.prana - drain)
        return drain

    def replenish_prana(self, soul: SoulState, loka_state: LokaState) -> float:
        """Replenish prana by consuming loka resources. Returns amount gained."""
        deficit = PRANA_MAX - soul.prana
        want = min(deficit, PRANA_REPLENISH_RATE)
        if want <= 0:
            return 0.0

        # Resource cost: PRANA_RESOURCE_CONVERSION prana per 1 loka resource
        resources_needed = int(want / PRANA_RESOURCE_CONVERSION) + 1
        resources_available = max(0, loka_state.resources)
        resources_consumed = min(resources_needed, resources_available)

        prana_gained = min(want, resources_consumed * PRANA_RESOURCE_CONVERSION)
        soul.prana = min(PRANA_MAX, soul.prana + prana_gained)
        loka_state.resources -= resources_consumed
        return prana_gained

    def is_dead(self, soul: SoulState) -> bool:
        """A soul dies when its prana is depleted."""
        return soul.prana <= 0.0

    # ------------------------------------------------------------------
    # Samsara (Rebirth)
    # ------------------------------------------------------------------
    def determine_rebirth_loka(self, soul: SoulState) -> LokaID:
        for loka_id, (low, high) in SAMSARA_KARMA_RANGES.items():
            if low <= soul.karma <= high:
                return loka_id
        return DEFAULT_LOKA

    def rebirth(self, soul: SoulState) -> SoulState:
        """Process samsara — death and rebirth with karma carryover + mutations."""
        new_loka = self.determine_rebirth_loka(soul)
        carried_karma = int(soul.karma * 0.7)

        # --- MUTATION: Vices ---
        karma_bias = -0.05 if soul.karma > 20 else 0.05 if soul.karma < -20 else 0.0
        k = soul.klesha
        soul.klesha = type(k)(
            kama=max(0.05, min(1.0, k.kama + random.uniform(-0.1, 0.1) + karma_bias)),
            krodha=max(0.05, min(1.0, k.krodha + random.uniform(-0.1, 0.1) + karma_bias)),
            lobha=max(0.05, min(1.0, k.lobha + random.uniform(-0.1, 0.1) + karma_bias)),
            moha=max(0.05, min(1.0, k.moha + random.uniform(-0.1, 0.1) + karma_bias)),
            ahamkara=max(0.05, min(1.0, k.ahamkara + random.uniform(-0.1, 0.1) + karma_bias)),
        )

        # --- MUTATION: Desires ---
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
                idx = random.randint(0, len(soul.desires) - 1)
                available = [d for d in _ALL_DESIRES if d not in soul.desires]
                if available:
                    soul.desires[idx] = random.choice(available)
            elif mutation_type == "add" and len(soul.desires) < 4:
                available = [d for d in _ALL_DESIRES if d not in soul.desires]
                if available:
                    soul.desires.append(random.choice(available))

        # --- MUTATION: Skills ---
        if random.random() < 0.2:
            _ALL_SKILLS = [
                "persuasion", "crafting", "meditation", "combat", "healing",
                "diplomacy", "stealth", "teaching", "strategy", "oration",
                "survival", "trade", "intimidation", "empathy", "deception",
            ]
            if random.random() < 0.6 and len(soul.skills) < 4:
                available = [s for s in _ALL_SKILLS if s not in soul.skills]
                if available:
                    soul.skills.append(random.choice(available))
            elif soul.skills:
                soul.skills.pop(random.randint(0, len(soul.skills) - 1))

        # --- Standard rebirth ---
        from brahmanda.engine.potential import assign_potential
        soul.alive = True
        soul.age = 0
        soul.lives += 1
        soul.loka = new_loka
        soul.karma = carried_karma
        soul.resources = 10
        soul.prana = PRANA_MAX  # full life force at rebirth
        soul.potential = assign_potential()  # new spark each life
        soul.potential_manifested = None
        soul.memories = soul.memories[-3:]
        soul.relationships = {}
        soul.is_avatar = False
        soul.avatar_mission = None
        return soul

    # ------------------------------------------------------------------
    # Action Classification
    # ------------------------------------------------------------------
    def classify_action(self, raw_action: str) -> str:
        raw = raw_action.lower().strip()
        if "fight" in raw:
            if any(w in raw for w in ("justified", "defend", "protect", "righteous", "duty")):
                return "fight_justified"
            return "fight_unjustified"
        if raw in KARMA_ACTIONS:
            return raw
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
        delta = self.score_action(action_type, yuga)
        self.apply_karma(soul, delta)
        return Action(
            tick=tick, soul_id=soul.id, action_type=action_type,
            target_id=target_id, description=description,
            karma_delta=delta, loka=soul.loka,
        )
