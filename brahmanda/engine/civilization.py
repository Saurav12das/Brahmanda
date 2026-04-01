"""Civilization Engine — knowledge, innovation, culture, ideology, and power.

The 0.01% that changes everything. While 99.99% of soul behavior is driven
by resource competition and the Arishadvarga, this engine models the rare
sparks that reshape civilization: breakthroughs, art, belief systems, and
the concentration of power.
"""

from __future__ import annotations

import random

from brahmanda.config import ACTIVE_LOKAS, LOKA_CONFIG, LokaID, YugaType, YUGA_PARAMS
from brahmanda.db.models import Event, LokaState, SoulState
from brahmanda.engine.potential import check_manifestation
from brahmanda.engine.tech_tree import TechTree

# Ideologies that can spread through teaching
IDEOLOGIES = [
    "dharma — duty above desire",
    "artha — wealth enables virtue",
    "kama — pleasure is the purpose",
    "moksha — liberation from the cycle",
    "ahimsa — non-violence above all",
    "shakti — power protects the weak",
    "maya — nothing is as it seems",
    "karma — every action returns",
]


class CivilizationEngine:
    """Manages the 0.01% — knowledge, innovation, culture, and power dynamics."""

    def __init__(self) -> None:
        self.global_innovations: dict[LokaID, list[str]] = {lid: [] for lid in ACTIVE_LOKAS}
        self.tech_tree = TechTree()

    # ------------------------------------------------------------------
    # Knowledge
    # ------------------------------------------------------------------
    def apply_knowledge_growth(self, loka: LokaState, souls: list[SoulState]) -> list[Event]:
        """Knowledge grows from teaching, meditation, and creation. Decays with entropy."""
        events = []
        if not souls:
            return events

        # Knowledge contribution from soul actions (accumulated from prior tick)
        teachers = sum(1 for s in souls if "teaching" in s.skills or "teach" in s.skills)
        meditators = sum(1 for s in souls if "meditation" in s.skills)
        creators = sum(1 for s in souls if "crafting" in s.skills or "create" in (s.desires or []))

        growth = (teachers * 0.1 + meditators * 0.05 + creators * 0.08)

        # Knowledge sharing bonus — more souls = faster growth (anti-rivalrous)
        if len(souls) > 1:
            growth *= (1.0 + len(souls) * 0.05)

        # Entropy erodes knowledge (chaos destroys libraries)
        decay = loka.entropy * 0.1 * loka.knowledge

        net = growth - decay
        loka.knowledge = max(0.1, loka.knowledge + net)

        return events

    # ------------------------------------------------------------------
    # Innovation (tech tree — branching, compounding)
    # ------------------------------------------------------------------
    def check_innovation(self, tick: int, loka: LokaState, souls: list[SoulState], yuga: YugaType) -> list[Event]:
        """Attempt tech tree discoveries — prerequisites must be met first."""
        if not souls:
            return []
        return self.tech_tree.attempt_discovery(tick, loka, souls, yuga.value)

    def get_innovation_resource_multiplier(self, loka: LokaState) -> float:
        """Total resource generation multiplier from all innovations."""
        return self.tech_tree.get_resource_multiplier(loka)

    def get_prana_efficiency(self, loka: LokaState) -> float:
        """Total prana drain reduction from innovations."""
        return self.tech_tree.get_prana_efficiency(loka)

    def get_trade_multiplier(self, loka: LokaState) -> float:
        """Total trade effectiveness from innovations."""
        return self.tech_tree.get_trade_multiplier(loka)

    # ------------------------------------------------------------------
    # Culture & Art (vice dampener)
    # ------------------------------------------------------------------
    def apply_culture(self, loka: LokaState, souls: list[SoulState]) -> list[Event]:
        """Culture grows from art/create actions, dampens vices for all souls."""
        events = []
        if not souls:
            return events

        # Culture grows from creative and empathetic souls
        artists = sum(1 for s in souls if "oration" in s.skills or "crafting" in s.skills
                      or any("beauty" in d for d in s.desires))
        empaths = sum(1 for s in souls if "empathy" in s.skills or "healing" in s.skills
                      or any("protect" in d for d in s.desires))

        culture_growth = (artists * 0.03 + empaths * 0.02)

        # Culture decays with entropy and low population
        culture_decay = loka.entropy * 0.05 + max(0, (3 - len(souls)) * 0.02)

        net = culture_growth - culture_decay
        old_culture = loka.culture
        loka.culture = max(0.0, min(1.0, loka.culture + net))

        # Log significant culture shifts
        if loka.culture >= 0.3 and old_culture < 0.3:
            events.append(Event(
                tick=0, event_type="culture_milestone", loka=loka.id,
                data={"culture": round(loka.culture, 2)},
                description=f"Cultural renaissance in {loka.name}! Art and empathy flourish.",
            ))

        return events

    def get_vice_dampening(self, loka: LokaState) -> float:
        """Culture reduces vice amplification. Returns a multiplier 0.7-1.0."""
        return max(0.7, 1.0 - loka.culture * 0.3)

    # ------------------------------------------------------------------
    # Ideology (memetic drift)
    # ------------------------------------------------------------------
    def apply_ideology_spread(self, tick: int, souls: list[SoulState]) -> list[Event]:
        """When a soul teaches, nearby souls may adopt a modified ideology."""
        events = []
        if len(souls) < 2:
            return events

        # Souls with teaching skill or high karma can spread ideology
        teachers = [s for s in souls if "teaching" in s.skills or s.karma > 30]
        if not teachers:
            return events

        for teacher in teachers:
            if not teacher.ideology:
                # Teacher develops an ideology from their desires
                if random.random() < 0.02:  # 2% chance per tick
                    base_ideologies = [i for i in IDEOLOGIES]
                    # Bias toward ideologies matching their personality
                    if teacher.klesha.lobha > 0.6:
                        base_ideologies.append("artha — wealth enables virtue")
                    if teacher.klesha.krodha < 0.3:
                        base_ideologies.append("ahimsa — non-violence above all")
                    if teacher.klesha.total_darkness < 0.3:
                        base_ideologies.append("moksha — liberation from the cycle")
                    teacher.ideology = random.choice(base_ideologies)
                    events.append(Event(
                        tick=tick, event_type="ideology_birth", loka=teacher.loka,
                        data={"soul": teacher.name, "ideology": teacher.ideology},
                        description=f"{teacher.name} develops a belief: '{teacher.ideology}'",
                    ))
            else:
                # 5% chance to spread ideology to a random nearby soul
                if random.random() < 0.05:
                    students = [s for s in souls if s.id != teacher.id and not s.ideology]
                    if students:
                        student = random.choice(students)
                        # Memetic drift: the student's version may mutate
                        if random.random() < 0.3:
                            # Drift — student reinterprets
                            student.ideology = teacher.ideology.split(" — ")[0] + " — " + random.choice([
                                "reinterpreted through suffering",
                                "but power is needed to enforce it",
                                "as the only path to peace",
                                "though the world resists",
                                "combined with the pursuit of knowledge",
                            ])
                        else:
                            student.ideology = teacher.ideology
                        events.append(Event(
                            tick=tick, event_type="ideology_spread", loka=teacher.loka,
                            data={"teacher": teacher.name, "student": student.name,
                                  "ideology": student.ideology,
                                  "drifted": student.ideology != teacher.ideology},
                            description=f"{student.name} adopts '{student.ideology}' from {teacher.name}",
                        ))

        return events

    # ------------------------------------------------------------------
    # Power Dynamics
    # ------------------------------------------------------------------
    def apply_power_dynamics(self, tick: int, loka: LokaState, souls: list[SoulState]) -> list[Event]:
        """Souls with high resources + high ahamkara accumulate influence.
        Influential souls passively drain resources from others (taxation/dominance).
        """
        events = []
        if len(souls) < 2:
            return events

        # Influence grows with resources and ego
        for soul in souls:
            resource_factor = min(1.0, soul.resources / 50.0)
            ego_factor = soul.klesha.ahamkara
            target_influence = resource_factor * ego_factor
            # Gradual shift toward target
            soul.influence += (target_influence - soul.influence) * 0.1
            soul.influence = max(0.0, min(1.0, soul.influence))

        # Power mongers (influence > 0.5) passively tax others
        power_mongers = [s for s in souls if s.influence > 0.5]
        subjects = [s for s in souls if s.influence <= 0.3 and s.resources > 2]

        for pm in power_mongers:
            if not subjects:
                break
            # Tax 1 resource from up to 3 subjects
            taxed = random.sample(subjects, min(3, len(subjects)))
            for subject in taxed:
                if subject.resources > 2:
                    subject.resources -= 1
                    pm.resources += 1

            if taxed:
                events.append(Event(
                    tick=tick, event_type="power_taxation", loka=loka.id,
                    data={"power_monger": pm.name, "influence": round(pm.influence, 2),
                          "taxed": [s.name for s in taxed]},
                    description=f"{pm.name} (influence={pm.influence:.2f}) extracts tribute from {len(taxed)} souls",
                ))

        return events

    # ------------------------------------------------------------------
    # Run all civilization systems for a loka
    # ------------------------------------------------------------------
    def process_loka(
        self, tick: int, loka: LokaState, souls: list[SoulState],
        yuga: YugaType, all_souls: dict[str, SoulState] | None = None,
    ) -> list[Event]:
        """Run all civilization systems for a single loka."""
        events = []
        events.extend(self.apply_knowledge_growth(loka, souls))
        events.extend(self.check_innovation(tick, loka, souls, yuga))
        events.extend(self.apply_culture(loka, souls))
        events.extend(self.apply_ideology_spread(tick, souls))
        events.extend(self.apply_power_dynamics(tick, loka, souls))

        # Potential manifestation — the rare spark
        if all_souls:
            for soul in souls:
                events.extend(check_manifestation(tick, soul, loka, all_souls))

        return events
