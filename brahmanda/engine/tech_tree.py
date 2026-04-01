"""Tech Tree — Innovation as a branching, compounding system.

Each innovation:
- Has prerequisites (other innovations that must exist first)
- Has discovery conditions (knowledge level, specific skills, luck)
- Unlocks MULTIPLE compound effects (not just "+X resources")
- Acts as a platform for downstream innovations

Fire doesn't just give warmth — it enables cooking (prana efficiency),
light (perception), and metallurgy (which enables tools, weapons, cities).

Agriculture doesn't just give food — it creates surplus (free time),
settlement (belonging), and trade (which needs wheel + surplus).

The tree branches: different civilizations develop different paths.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from brahmanda.db.models import Event, LokaState, SoulState


@dataclass
class Innovation:
    """A node in the tech tree."""
    name: str
    description: str
    prerequisites: list[str] = field(default_factory=list)   # names of required innovations
    knowledge_req: float = 1.0                                # minimum loka knowledge
    discovery_chance: float = 0.005                           # base chance per tick when conditions met
    relevant_skills: list[str] = field(default_factory=list)  # skills that boost discovery
    # Compound effects — each innovation changes multiple things
    effects: dict = field(default_factory=dict)
    # Effects can include:
    #   resource_multiplier: float    — multiplies loka resource regen
    #   prana_efficiency: float       — reduces prana drain for all souls
    #   knowledge_boost: float        — one-time knowledge injection
    #   culture_boost: float          — one-time culture boost
    #   entropy_cost: float           — entropy price of progress
    #   entropy_reduction: float      — some innovations REDUCE entropy
    #   belonging_boost: float        — community feeling for all souls
    #   truth_visibility_boost: float — perception clarity increase
    #   trade_multiplier: float       — trade actions yield more
    #   fight_power: float            — combat effectiveness
    #   ideology_spread_rate: float   — ideas spread faster
    #   free_time: float              — enables downstream innovations faster
    #   explore_range: float          — exploration yields more


# ---------------------------------------------------------------------------
# The Tech Tree
# ---------------------------------------------------------------------------
TECH_TREE: list[Innovation] = [
    # TIER 0 — Primal discoveries (no prerequisites)
    Innovation(
        name="Fire",
        description="Lightning strikes, a soul understands flame — everything changes",
        prerequisites=[],
        knowledge_req=0.5,
        discovery_chance=0.02,  # relatively common — it's the first spark
        relevant_skills=["survival", "crafting"],
        effects={
            "prana_efficiency": 0.15,        # cooking makes food nourish more
            "truth_visibility_boost": 0.05,  # light reveals truth
            "entropy_cost": 0.02,
            "knowledge_boost": 0.5,          # understanding fire is transformative
        },
    ),
    Innovation(
        name="Stone Tools",
        description="Shaped stone becomes extension of will — the first technology",
        prerequisites=[],
        knowledge_req=0.3,
        discovery_chance=0.02,
        relevant_skills=["crafting", "combat", "survival"],
        effects={
            "resource_multiplier": 0.2,
            "fight_power": 0.1,
            "knowledge_boost": 0.3,
        },
    ),
    Innovation(
        name="Language",
        description="Sounds become meaning — thoughts can travel between souls",
        prerequisites=[],
        knowledge_req=0.5,
        discovery_chance=0.015,
        relevant_skills=["oration", "teaching", "persuasion"],
        effects={
            "ideology_spread_rate": 0.3,
            "knowledge_boost": 1.0,          # language accelerates all learning
            "belonging_boost": 0.1,
            "culture_boost": 0.05,
        },
    ),

    # TIER 1 — Foundational (need 1-2 primal)
    Innovation(
        name="Cooking",
        description="Fire meets food — nourishment transforms, life extends",
        prerequisites=["Fire"],
        knowledge_req=1.0,
        discovery_chance=0.015,
        relevant_skills=["crafting", "survival"],
        effects={
            "prana_efficiency": 0.2,          # cooked food = much better prana
            "resource_multiplier": 0.15,      # food goes further
        },
    ),
    Innovation(
        name="Shelter",
        description="Walls against the chaos — a place to belong",
        prerequisites=["Stone Tools"],
        knowledge_req=1.0,
        discovery_chance=0.015,
        relevant_skills=["crafting", "survival"],
        effects={
            "prana_efficiency": 0.1,
            "belonging_boost": 0.15,          # shelter creates home
            "entropy_reduction": 0.02,        # order against chaos
        },
    ),
    Innovation(
        name="Storytelling",
        description="Memory transcends one life — the past speaks to the future",
        prerequisites=["Language"],
        knowledge_req=1.5,
        discovery_chance=0.01,
        relevant_skills=["oration", "teaching"],
        effects={
            "culture_boost": 0.1,
            "knowledge_boost": 0.5,
            "ideology_spread_rate": 0.2,
        },
    ),

    # TIER 2 — Civilization starters
    Innovation(
        name="Agriculture",
        description="Seeds become intention — the earth yields to patient hands",
        prerequisites=["Stone Tools", "Fire"],
        knowledge_req=2.0,
        discovery_chance=0.008,
        relevant_skills=["crafting", "strategy", "survival"],
        effects={
            "resource_multiplier": 0.5,       # massive resource boost
            "belonging_boost": 0.2,           # settlement creates community
            "free_time": 0.3,                 # surplus enables specialization
            "entropy_cost": 0.03,
        },
    ),
    Innovation(
        name="Animal Husbandry",
        description="Beasts become companions and sustenance — a covenant with nature",
        prerequisites=["Fire", "Language"],
        knowledge_req=2.0,
        discovery_chance=0.008,
        relevant_skills=["empathy", "survival"],
        effects={
            "resource_multiplier": 0.3,
            "prana_efficiency": 0.1,
            "explore_range": 0.2,
        },
    ),
    Innovation(
        name="Pottery",
        description="Earth shaped by hands and fire — storage conquers time",
        prerequisites=["Fire", "Shelter"],
        knowledge_req=2.0,
        discovery_chance=0.01,
        relevant_skills=["crafting"],
        effects={
            "resource_multiplier": 0.15,      # storage reduces waste
            "trade_multiplier": 0.15,         # goods can be contained
            "culture_boost": 0.05,
        },
    ),

    # TIER 3 — Early civilization
    Innovation(
        name="Wheel",
        description="Circular motion defies friction — distance shrinks",
        prerequisites=["Stone Tools", "Animal Husbandry"],
        knowledge_req=3.0,
        discovery_chance=0.005,
        relevant_skills=["crafting", "strategy"],
        effects={
            "trade_multiplier": 0.4,          # trade networks explode
            "explore_range": 0.4,
            "ideology_spread_rate": 0.2,      # ideas travel with goods
            "resource_multiplier": 0.2,
        },
    ),
    Innovation(
        name="Weaving",
        description="Threads become fabric — nakedness gives way to identity",
        prerequisites=["Agriculture", "Animal Husbandry"],
        knowledge_req=2.5,
        discovery_chance=0.01,
        relevant_skills=["crafting"],
        effects={
            "trade_multiplier": 0.2,
            "culture_boost": 0.1,
            "prana_efficiency": 0.05,
        },
    ),
    Innovation(
        name="Metallurgy",
        description="Stone yields to metal — bronze reshapes power",
        prerequisites=["Fire", "Stone Tools"],
        knowledge_req=4.0,
        discovery_chance=0.004,
        relevant_skills=["crafting", "strategy"],
        effects={
            "resource_multiplier": 0.4,
            "fight_power": 0.3,
            "entropy_cost": 0.05,
            "knowledge_boost": 0.5,
        },
    ),

    # TIER 4 — Knowledge revolution
    Innovation(
        name="Writing",
        description="Thought becomes permanent — knowledge survives death",
        prerequisites=["Language", "Storytelling"],
        knowledge_req=4.0,
        discovery_chance=0.004,
        relevant_skills=["teaching", "oration"],
        effects={
            "knowledge_boost": 3.0,           # MASSIVE — knowledge persists
            "ideology_spread_rate": 0.4,
            "culture_boost": 0.1,
            "free_time": 0.1,
        },
    ),
    Innovation(
        name="Mathematics",
        description="Pattern beneath chaos — the universe speaks in numbers",
        prerequisites=["Writing", "Pottery"],
        knowledge_req=6.0,
        discovery_chance=0.003,
        relevant_skills=["strategy", "teaching"],
        effects={
            "knowledge_boost": 2.0,
            "trade_multiplier": 0.3,
            "resource_multiplier": 0.2,
            "free_time": 0.2,
        },
    ),
    Innovation(
        name="Medicine",
        description="Suffering meets understanding — the body reveals its secrets",
        prerequisites=["Cooking", "Language"],
        knowledge_req=4.0,
        discovery_chance=0.005,
        relevant_skills=["healing", "empathy", "meditation"],
        effects={
            "prana_efficiency": 0.25,         # major survival boost
            "knowledge_boost": 1.0,
            "entropy_reduction": 0.02,
        },
    ),

    # TIER 5 — Philosophical/spiritual
    Innovation(
        name="Philosophy",
        description="Why? — the question that has no end but transforms everything",
        prerequisites=["Writing", "Storytelling"],
        knowledge_req=5.0,
        discovery_chance=0.004,
        relevant_skills=["meditation", "teaching", "oration"],
        effects={
            "entropy_reduction": 0.05,        # understanding reduces chaos
            "culture_boost": 0.2,
            "knowledge_boost": 2.0,
            "belonging_boost": 0.1,
        },
    ),
    Innovation(
        name="Yoga & Meditation",
        description="The inner world opens — prana flows by will, not chance",
        prerequisites=["Medicine", "Philosophy"],
        knowledge_req=6.0,
        discovery_chance=0.004,
        relevant_skills=["meditation", "healing"],
        effects={
            "prana_efficiency": 0.3,          # massive prana boost
            "entropy_reduction": 0.08,        # inner peace = outer order
            "culture_boost": 0.15,
        },
    ),

    # TIER 6 — Advanced
    Innovation(
        name="Architecture",
        description="Space bends to vision — temples rise, cities emerge",
        prerequisites=["Metallurgy", "Mathematics"],
        knowledge_req=8.0,
        discovery_chance=0.003,
        relevant_skills=["crafting", "strategy"],
        effects={
            "belonging_boost": 0.3,
            "resource_multiplier": 0.3,
            "culture_boost": 0.15,
            "entropy_cost": 0.04,
        },
    ),
    Innovation(
        name="Astronomy",
        description="Eyes turn skyward — the cosmos reveals its rhythm",
        prerequisites=["Mathematics", "Philosophy"],
        knowledge_req=10.0,
        discovery_chance=0.002,
        relevant_skills=["meditation", "strategy"],
        effects={
            "knowledge_boost": 3.0,
            "truth_visibility_boost": 0.1,
            "entropy_reduction": 0.03,
        },
    ),
    Innovation(
        name="Navigation",
        description="Stars become maps — the unknown beckons",
        prerequisites=["Astronomy", "Wheel"],
        knowledge_req=12.0,
        discovery_chance=0.002,
        relevant_skills=["strategy", "survival"],
        effects={
            "explore_range": 0.5,
            "trade_multiplier": 0.5,
            "resource_multiplier": 0.2,
        },
    ),
]


class TechTree:
    """Manages innovation discovery and compound effects."""

    def can_discover(self, innovation: Innovation, loka: LokaState) -> bool:
        """Check if prerequisites and knowledge requirements are met."""
        if innovation.name in loka.innovations:
            return False
        if loka.knowledge < innovation.knowledge_req:
            return False
        for prereq in innovation.prerequisites:
            if prereq not in loka.innovations:
                return False
        return True

    def get_available(self, loka: LokaState) -> list[Innovation]:
        """Get all innovations currently discoverable by this loka."""
        return [inn for inn in TECH_TREE if self.can_discover(inn, loka)]

    def attempt_discovery(
        self, tick: int, loka: LokaState, souls: list[SoulState], yuga_value: str,
    ) -> list[Event]:
        """Attempt innovation discovery. Multiple innovations can be available simultaneously."""
        events = []
        available = self.get_available(loka)
        if not available:
            return events

        yuga_mod = {"satya": 2.0, "treta": 1.5, "dvapara": 1.0, "kali": 0.5}[yuga_value]

        # Free time from prior innovations boosts all discovery
        free_time_bonus = self.get_compound_effect(loka, "free_time")

        for innovation in available:
            # Find souls with relevant skills
            innovators = [s for s in souls if any(
                sk in s.skills for sk in innovation.relevant_skills
            )]
            # Even without specific skills, any soul can stumble onto discovery
            if not innovators:
                innovators = souls[:1] if souls else []
                skill_bonus = 0.5
            else:
                skill_bonus = 1.0 + len(innovators) * 0.3

            chance = innovation.discovery_chance * yuga_mod * skill_bonus * (1.0 + free_time_bonus)

            if random.random() < chance:
                innovator = random.choice(innovators)
                self._apply_innovation(innovation, loka, souls)

                events.append(Event(
                    tick=tick, event_type="innovation", loka=loka.id,
                    data={
                        "innovation": innovation.name,
                        "innovator": innovator.name,
                        "tier": self._get_tier(innovation),
                        "prerequisites": innovation.prerequisites,
                        "effects": innovation.effects,
                        "knowledge": round(loka.knowledge, 1),
                        "total_innovations": len(loka.innovations),
                    },
                    description=f"BREAKTHROUGH: {innovator.name} discovers {innovation.name}! "
                                f"— {innovation.description}",
                ))
                break  # one discovery per tick max

        return events

    def _apply_innovation(self, innovation: Innovation, loka: LokaState, souls: list[SoulState]) -> None:
        """Apply all compound effects of an innovation."""
        loka.innovations.append(innovation.name)

        effects = innovation.effects

        if "knowledge_boost" in effects:
            loka.knowledge += effects["knowledge_boost"]
        if "culture_boost" in effects:
            loka.culture = min(1.0, loka.culture + effects["culture_boost"])
        if "entropy_cost" in effects:
            loka.entropy = min(1.0, loka.entropy + effects["entropy_cost"])
        if "entropy_reduction" in effects:
            loka.entropy = max(0.0, loka.entropy - effects["entropy_reduction"])
        if "belonging_boost" in effects:
            # Boost relationships slightly for all souls in loka
            for soul in souls:
                for other in souls:
                    if other.id != soul.id:
                        current = soul.relationships.get(other.id, 0)
                        soul.relationships[other.id] = min(100, current + int(effects["belonging_boost"] * 10))

    def get_compound_effect(self, loka: LokaState, effect_name: str) -> float:
        """Sum a specific effect across all discovered innovations."""
        total = 0.0
        for inn in TECH_TREE:
            if inn.name in loka.innovations:
                total += inn.effects.get(effect_name, 0.0)
        return total

    def get_resource_multiplier(self, loka: LokaState) -> float:
        """Total resource generation multiplier from all innovations."""
        return 1.0 + self.get_compound_effect(loka, "resource_multiplier")

    def get_prana_efficiency(self, loka: LokaState) -> float:
        """Total prana drain reduction from all innovations."""
        return self.get_compound_effect(loka, "prana_efficiency")

    def get_trade_multiplier(self, loka: LokaState) -> float:
        """Total trade effectiveness multiplier."""
        return 1.0 + self.get_compound_effect(loka, "trade_multiplier")

    def _get_tier(self, innovation: Innovation) -> int:
        """Determine the tier (depth) of an innovation."""
        if not innovation.prerequisites:
            return 0
        max_depth = 0
        for prereq_name in innovation.prerequisites:
            for inn in TECH_TREE:
                if inn.name == prereq_name:
                    max_depth = max(max_depth, self._get_tier(inn) + 1)
        return max_depth
