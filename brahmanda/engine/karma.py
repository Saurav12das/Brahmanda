"""Karma Engine — action-consequence tracker, prana mechanics, and samsara."""

from __future__ import annotations

import random

import brahmanda.config as cfg
from brahmanda.config import (
    DEFAULT_LOKA,
    KARMA_ACTIONS,
    LAWS,
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
        base_rate = cfg.KARMA_DECAY_BASE_RATE
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
    def drain_prana(self, soul: SoulState, loka_entropy: float, yuga: YugaType,
                   innovation_efficiency: float = 0.0) -> float:
        """Drain prana each tick. Returns amount drained.
        innovation_efficiency: prana drain reduction from tech tree discoveries.
        """
        drain = cfg.PRANA_BASE_DRAIN
        drain += soul.klesha.total_darkness * cfg.PRANA_VICE_DRAIN_FACTOR
        drain += loka_entropy * cfg.PRANA_ENTROPY_DRAIN_FACTOR

        # Innovation efficiency — cooking, medicine, yoga reduce drain
        drain = max(0.3, drain - innovation_efficiency)

        # Age factor — gradual increase after onset, not a cliff
        if soul.age > cfg.PRANA_AGE_DRAIN_ONSET:
            drain += (soul.age - cfg.PRANA_AGE_DRAIN_ONSET) * cfg.PRANA_AGE_DRAIN_RATE

        # Karma efficiency — positive karma reduces drain (up to 50%)
        karma_efficiency = max(0.5, 1.0 - soul.karma / 400.0)
        drain *= karma_efficiency

        # Hope reduces prana drain; despair accelerates it
        hope_factor = 1.0 - soul.hope * LAWS["hope_prana_dampening"]
        hope_factor = max(0.8, min(1.2, hope_factor))  # clamp
        drain *= hope_factor

        # Avatars are more resilient
        if soul.is_avatar:
            drain *= 0.5

        soul.prana = max(0.0, soul.prana - drain)
        return drain

    def replenish_prana(self, soul: SoulState, loka_state: LokaState) -> float:
        """Replenish prana by consuming loka resources. Returns amount gained."""
        deficit = cfg.PRANA_MAX - soul.prana
        want = min(deficit, cfg.PRANA_REPLENISH_RATE)
        if want <= 0:
            return 0.0

        # Resource cost: PRANA_RESOURCE_CONVERSION prana per 1 loka resource
        resources_needed = int(want / cfg.PRANA_RESOURCE_CONVERSION) + 1
        resources_available = max(0, loka_state.resources)
        resources_consumed = min(resources_needed, resources_available)

        prana_gained = min(want, resources_consumed * cfg.PRANA_RESOURCE_CONVERSION)
        soul.prana = min(cfg.PRANA_MAX, soul.prana + prana_gained)
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

        # --- Past life echo: condense this life's most important lesson ---
        past_life_echo = None
        if soul.memories:
            # Summarize what this soul learned in their life
            action_memories = [m for m in soul.memories if "chose to" in m]
            if action_memories:
                past_life_echo = f"Past life echo: In a previous life as {soul.name}, I {action_memories[-1].split('I ')[-1] if 'I ' in action_memories[-1] else 'lived and learned'}"

        # --- Standard rebirth ---
        from brahmanda.engine.potential import assign_potential
        soul.alive = True
        soul.age = 0
        soul.lives += 1
        soul.loka = new_loka
        soul.karma = carried_karma
        soul.resources = 10
        soul.prana = cfg.PRANA_MAX  # full life force at rebirth
        soul.potential = assign_potential()  # new spark each life
        soul.potential_manifested = None

        # Keep last 3 personal memories + past life echo
        soul.memories = soul.memories[-3:]
        if past_life_echo:
            soul.memories.insert(0, past_life_echo)
        soul.relationships = {}
        soul.emulating = None          # fresh start — no allegiance carries over
        # times_emulated persists — reputation echoes across lives
        soul.last_action = None
        soul.is_avatar = False
        soul.avatar_mission = None
        # Hope carries over with decay and mutation
        soul.hope = soul.hope * LAWS["hope_rebirth_carry"] + random.uniform(-0.1, 0.1)
        soul.hope = max(-1.0, min(1.0, soul.hope))
        return soul

    def inject_akashic_memory(self, soul: SoulState, loka_state) -> None:
        """Inject loka's cultural memory into a soul (birth or rebirth).
        This is how civilizations compound knowledge across generations.
        """
        if hasattr(loka_state, 'akashic_memory') and loka_state.akashic_memory:
            # Give the soul up to 3 cultural memories from their birth loka
            import random as _rng
            available = [m for m in loka_state.akashic_memory if m not in soul.memories]
            count = min(3, len(available))
            if count > 0:
                inherited = _rng.sample(available, count)
                soul.memories = inherited + soul.memories

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
            "emulate": ["emulate", "follow", "copy", "imitate", "mimic", "learn from", "model after"],
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
