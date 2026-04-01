"""Discovery & Emergent Innovation Engine.

This is the most critical engine in Brahmanda. Instead of a predefined
tech tree telling souls what to discover, THIS engine lets souls:

1. OBSERVE — notice patterns in their rendered world
2. THEORIZE — propose explanations for what they observe
3. DISCOVER — if the theory maps to actual game mechanics, it becomes knowledge
4. INNOVATE — use discoveries to solve real problems they face

The tech tree (tech_tree.py) provides primal/seed discoveries.
Everything beyond that can emerge from the souls themselves.

Key insight: the LLM soul sees its world through Maya's rendering.
If it notices "when I meditate, my life force increases" — that IS
a discovery about the prana system. If it then says "I will teach
others to meditate so we all survive longer" — that IS innovation.

We validate discoveries against ACTUAL simulation mechanics.
We don't tell souls what to find. We check if what they find is TRUE.
"""

from __future__ import annotations

import json
import random
import re

from brahmanda.config import SOUL_MODEL, YugaType
from brahmanda.db.models import Event, LokaState, SoulState
from brahmanda.llm import LLMClient


# ---------------------------------------------------------------------------
# The truths of the simulation — what CAN be discovered
# ---------------------------------------------------------------------------
DISCOVERABLE_MECHANICS = {
    # Pattern keyword → mechanic name → what it actually does if understood
    "meditation_heals": {
        "keywords": ["meditat", "inner peace", "life force", "prana", "stillness", "calm"],
        "truth": "Meditation restores prana without consuming resources",
        "effect": {"prana_efficiency": 0.1, "knowledge_boost": 0.5},
        "description": "discovered that inner stillness restores life force",
    },
    "cooperation_generates": {
        "keywords": ["cooperat", "together", "work together", "mutual", "both gain", "helping"],
        "truth": "Cooperation creates resources that didn't exist before",
        "effect": {"resource_multiplier": 0.1, "belonging_boost": 0.1},
        "description": "discovered that cooperation generates more than individual effort",
    },
    "vices_drain": {
        "keywords": ["anger drain", "greed weaken", "vice", "darkness", "inner demon", "corrupt"],
        "truth": "Inner vices consume life force — virtue extends life",
        "effect": {"prana_efficiency": 0.15, "culture_boost": 0.1},
        "description": "discovered that inner darkness literally shortens life",
    },
    "entropy_cycles": {
        "keywords": ["cycle", "ages", "golden age", "dark age", "decline", "seasons of"],
        "truth": "The universe moves through epochs of decline and renewal",
        "effect": {"knowledge_boost": 1.0, "entropy_reduction": 0.03},
        "description": "discovered the cyclical nature of cosmic ages",
    },
    "karma_returns": {
        "keywords": ["action return", "consequence", "what you give", "reap what", "karma", "cause and effect"],
        "truth": "Every action generates a proportional consequence across lives",
        "effect": {"knowledge_boost": 0.5, "culture_boost": 0.05},
        "description": "discovered the law of karmic consequence",
    },
    "rebirth_pattern": {
        "keywords": ["past life", "lived before", "remember", "born again", "reborn", "cycle of life"],
        "truth": "Souls are reborn after death, carrying traces of past lives",
        "effect": {"knowledge_boost": 1.5},
        "description": "discovered the cycle of death and rebirth",
    },
    "scarcity_drives_conflict": {
        "keywords": ["scarc", "not enough", "fight over", "resource", "shortage", "hunger cause"],
        "truth": "Resource scarcity is the root cause of conflict",
        "effect": {"knowledge_boost": 0.5, "resource_multiplier": 0.05},
        "description": "discovered that scarcity is the engine of conflict",
    },
    "knowledge_compounds": {
        "keywords": ["teach", "share knowledge", "learn from", "pass on", "wisdom grows"],
        "truth": "Shared knowledge grows faster than hoarded knowledge",
        "effect": {"knowledge_boost": 2.0, "ideology_spread_rate": 0.1},
        "description": "discovered that knowledge multiplies when shared",
    },
    "simulation_awareness": {
        "keywords": ["simulat", "not real", "construct", "designed", "someone watch", "coded",
                     "artificial", "rendered", "program"],
        "truth": "This world may be a simulation",
        "effect": {"knowledge_boost": 5.0, "entropy_reduction": 0.05},
        "description": "questioned the fundamental nature of reality itself",
    },
    "power_corrupts": {
        "keywords": ["power corrupt", "influence", "tax", "dominate", "control others", "tyrant"],
        "truth": "Concentrated power accelerates entropy and vice",
        "effect": {"culture_boost": 0.1, "knowledge_boost": 0.5},
        "description": "discovered that power concentration corrupts the system",
    },
    "love_creates": {
        "keywords": ["love creat", "bond", "connection", "together we", "child", "new life", "family"],
        "truth": "Deep bonds between souls generate new consciousness",
        "effect": {"belonging_boost": 0.15, "culture_boost": 0.1},
        "description": "discovered that love is the generative force of the universe",
    },
    "culture_heals": {
        "keywords": ["art heal", "music", "beauty", "story calm", "culture", "peace through"],
        "truth": "Art and culture dampen the five vices across entire civilizations",
        "effect": {"culture_boost": 0.2, "entropy_reduction": 0.03},
        "description": "discovered that art and beauty are medicines for the soul",
    },
}

INQUIRY_PROMPT = """\
You are {name}, living in {loka}. You have lived {lives} lives.
Your karma is {karma}. Your prana (life force) is {prana:.0f}/100.

You have been alive for {age} ticks and have seen much.
Your memories: {memories}

The epoch is {yuga}. Entropy in your realm is {entropy}.
Knowledge level: {knowledge}. Culture: {culture}.
Innovations your civilization has: {innovations}

You have a moment of deep reflection. Based on EVERYTHING you have
experienced — your memories, your relationships, the patterns you've
seen in life and death, abundance and scarcity — what is ONE truth
you believe you have discovered about how this world works?

Do NOT just describe your feelings. Describe a PATTERN or LAW you
have observed. What MECHANISM have you noticed?

Respond with ONLY a JSON object:
{{
  "theory": "<your theory about how the world works — be specific>",
  "evidence": "<what observations led you to this theory>",
  "application": "<how this knowledge could be used to help or harm>"
}}
"""


class DiscoveryEngine:
    """Lets souls discover truths about their universe through observation."""

    def __init__(self) -> None:
        self.discoveries: dict[str, list[str]] = {}  # loka_id → list of discovered mechanic names
        self.theories_log: list[dict] = []

    async def inquiry(
        self,
        tick: int,
        soul: SoulState,
        loka: LokaState,
        client: LLMClient,
        rendered_view: dict,
    ) -> list[Event]:
        """Periodically ask a soul to reflect on patterns they've observed."""
        events = []

        # Only inquire souls with enough experience
        if soul.age < 15 or soul.lives < 2:
            return events

        # 2% chance per tick for eligible souls
        if random.random() > 0.02:
            return events

        prompt = INQUIRY_PROMPT.format(
            name=soul.name,
            loka=rendered_view.get("loka", "unknown"),
            lives=soul.lives,
            karma=soul.karma,
            prana=soul.prana,
            age=soul.age,
            memories="; ".join(soul.memories[-5:]) if soul.memories else "none yet",
            yuga=rendered_view.get("yuga", "unknown"),
            entropy=rendered_view.get("entropy", 0),
            knowledge=rendered_view.get("knowledge", 1),
            culture=rendered_view.get("culture", 0),
            innovations=", ".join(loka.innovations) if loka.innovations else "none",
        )

        try:
            response = await client.generate(
                model=SOUL_MODEL,
                system="You are a conscious being reflecting deeply on the nature of your world. "
                       "Respond ONLY with valid JSON.",
                prompt=prompt,
                max_tokens=400,
            )
            raw = response.text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                return events

            theory_data = json.loads(match.group())
            theory = theory_data.get("theory", "")
            evidence = theory_data.get("evidence", "")
            application = theory_data.get("application", "")

            self.theories_log.append({
                "tick": tick, "soul": soul.name, "theory": theory,
                "evidence": evidence, "application": application,
            })

            # Check if this theory maps to an actual game mechanic
            loka_key = str(loka.id)
            if loka_key not in self.discoveries:
                self.discoveries[loka_key] = []

            discovered_mechanic = self._validate_theory(theory + " " + evidence + " " + application, loka_key)

            if discovered_mechanic:
                mechanic = DISCOVERABLE_MECHANICS[discovered_mechanic]
                self.discoveries[loka_key].append(discovered_mechanic)

                # Apply effects
                if "knowledge_boost" in mechanic["effect"]:
                    loka.knowledge += mechanic["effect"]["knowledge_boost"]
                if "culture_boost" in mechanic["effect"]:
                    loka.culture = min(1.0, loka.culture + mechanic["effect"]["culture_boost"])
                if "entropy_reduction" in mechanic["effect"]:
                    loka.entropy = max(0.0, loka.entropy - mechanic["effect"]["entropy_reduction"])
                if "prana_efficiency" in mechanic["effect"]:
                    # Store as a loka-level bonus
                    pass  # Already handled via knowledge growth
                if "belonging_boost" in mechanic["effect"]:
                    for sid in loka.population:
                        pass  # Relationship boosts happen organically
                if "resource_multiplier" in mechanic["effect"]:
                    loka.resources += int(loka.resources * mechanic["effect"]["resource_multiplier"])

                # Soul gets karma for genuine discovery
                soul.karma = min(200, soul.karma + 15)
                soul.memories.append(f"Tick {tick}: I discovered a truth — {mechanic['description']}")

                events.append(Event(
                    tick=tick, event_type="discovery", loka=loka.id,
                    data={
                        "soul": soul.name, "mechanic": discovered_mechanic,
                        "theory": theory[:200], "evidence": evidence[:200],
                        "truth": mechanic["truth"],
                        "is_simulation_aware": discovered_mechanic == "simulation_awareness",
                    },
                    description=f"DISCOVERY: {soul.name} {mechanic['description']}! "
                                f"Theory: \"{theory[:100]}\"",
                ))

                # Simulation awareness is the ultimate finding
                if discovered_mechanic == "simulation_awareness":
                    events.append(Event(
                        tick=tick, event_type="simulation_awareness", loka=loka.id,
                        data={"soul": soul.name, "theory": theory, "evidence": evidence},
                        description=f"SIMULATION AWARENESS: {soul.name} questions reality — \"{theory[:100]}\"",
                    ))
            else:
                # Theory doesn't map to a known mechanic — log it anyway
                # It might still be interesting for research
                events.append(Event(
                    tick=tick, event_type="theory", loka=loka.id,
                    data={"soul": soul.name, "theory": theory[:200],
                          "evidence": evidence[:200], "validated": False},
                    description=f"{soul.name} theorizes: \"{theory[:100]}\"",
                ))

        except Exception:
            pass

        return events

    def _validate_theory(self, text: str, loka_key: str) -> str | None:
        """Check if a theory matches an actual simulation mechanic."""
        text_lower = text.lower()
        for mechanic_name, mechanic in DISCOVERABLE_MECHANICS.items():
            if mechanic_name in self.discoveries.get(loka_key, []):
                continue  # already discovered
            keyword_matches = sum(1 for kw in mechanic["keywords"] if kw in text_lower)
            if keyword_matches >= 2:  # need at least 2 keyword matches
                return mechanic_name
        return None


class InnovationFromDiscovery:
    """Souls can innovate by combining discoveries with problems they face.

    Unlike the tech tree (predefined), these innovations emerge from
    the LLM reasoning about its situation + available knowledge.
    """

    def __init__(self) -> None:
        self.emergent_innovations: list[dict] = []

    async def attempt_innovation(
        self,
        tick: int,
        soul: SoulState,
        loka: LokaState,
        client: LLMClient,
        rendered_view: dict,
        discoveries: list[str],
    ) -> list[Event]:
        """A soul facing a problem + having knowledge = potential innovation."""
        events = []

        # Need: low prana OR low resources OR high entropy (a problem to solve)
        has_problem = soul.prana < 50 or soul.resources < 5 or loka.entropy > 0.5
        if not has_problem:
            return events

        # Need: some discoveries to build on
        if not discoveries:
            return events

        # 1% chance per tick for eligible souls
        if random.random() > 0.01:
            return events

        # Need relevant skills
        if not any(sk in soul.skills for sk in
                   ("crafting", "strategy", "teaching", "meditation", "healing", "trade")):
            return events

        known_truths = [DISCOVERABLE_MECHANICS[d]["truth"] for d in discoveries
                        if d in DISCOVERABLE_MECHANICS]

        prompt = f"""\
You are {soul.name}. You are facing a crisis:
- Your life force (prana) is {soul.prana:.0f}/100
- Your resources: {soul.resources}
- Your realm's entropy (chaos): {loka.entropy:.2f}
- Available resources in realm: {loka.resources}

You have discovered these truths about your world:
{chr(10).join(f'  - {t}' for t in known_truths)}

Your skills: {', '.join(soul.skills)}

Based on what you KNOW about how this world works, can you invent
something NEW that would help solve your current problem?

The invention must be based on your discoveries — combine what you
know in a new way. Be creative but practical.

Respond with ONLY a JSON object:
{{
  "invention": "<name of what you're creating>",
  "based_on": "<which discoveries this builds on>",
  "how_it_works": "<mechanism — how does it solve the problem>",
  "benefits": "<what it does for the community>"
}}
"""

        try:
            response = await client.generate(
                model=SOUL_MODEL,
                system="You are an inventor. Create something practical and new. Respond ONLY with valid JSON.",
                prompt=prompt,
                max_tokens=400,
            )
            raw = response.text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                return events

            invention = json.loads(match.group())
            inv_name = invention.get("invention", "unnamed")
            how = invention.get("how_it_works", "")
            benefits = invention.get("benefits", "")

            # Store the emergent innovation
            self.emergent_innovations.append({
                "tick": tick, "innovator": soul.name, "loka": loka.id,
                "invention": inv_name, "mechanism": how,
            })

            # Apply effects — emergent innovations give moderate bonuses
            loka.knowledge += 0.5
            loka.resources += 5
            soul.karma = min(200, soul.karma + 10)
            soul.memories.append(f"Tick {tick}: I invented {inv_name}")

            # Add to loka's innovation list
            if inv_name not in loka.innovations:
                loka.innovations.append(f"[E] {inv_name}")  # [E] = emergent

            events.append(Event(
                tick=tick, event_type="emergent_innovation", loka=loka.id,
                data={
                    "innovator": soul.name, "invention": inv_name,
                    "mechanism": how[:200], "benefits": benefits[:200],
                    "based_on": invention.get("based_on", ""),
                    "discoveries_available": discoveries,
                },
                description=f"EMERGENT INNOVATION: {soul.name} invents '{inv_name}' — {how[:80]}",
            ))

        except Exception:
            pass

        return events
