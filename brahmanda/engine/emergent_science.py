"""Emergent Science Engine — souls autonomously create new branches of knowledge.

Unlike the predefined tech tree (tech_tree.py) and the 12 discoverable mechanics
(discovery.py), this engine lets souls INVENT entirely new fields of science
that become real, compounding nodes in the knowledge graph.

How it works:
1. A soul with enough experience + discoveries + existing innovations reflects
2. The LLM proposes a new field of science based on what the soul knows
3. We validate the proposal (bounded effects, real prerequisites, not duplicate)
4. The new science becomes a REAL Innovation node in the emergent tree
5. Future souls can build on it — creating autonomous branching

This means two different simulation runs can produce completely different
scientific traditions. One universe might develop "Acoustic Healing" from
Medicine + Music. Another might develop "Entropy Mathematics" from
Mathematics + entropy_cycles discovery. The souls decide.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field

from brahmanda.config import LAWS, SOUL_MODEL
from brahmanda.db.models import Event, LokaState, SoulState
from brahmanda.llm import LLMClient


# ---------------------------------------------------------------------------
# Emergent Innovation node (same shape as tech_tree.Innovation but dynamic)
# ---------------------------------------------------------------------------
@dataclass
class EmergentInnovation:
    """A soul-created branch of science."""
    name: str
    description: str
    created_by: str                                  # soul name
    created_tick: int
    prerequisites: list[str] = field(default_factory=list)   # existing innovations it builds on
    based_on_discoveries: list[str] = field(default_factory=list)  # discoveries that inspired it
    effects: dict = field(default_factory=dict)
    built_upon_count: int = 0                        # how many further sciences reference this


# Allowed effect keys and their max values (prevents runaway cascading)
ALLOWED_EFFECTS = {
    "resource_multiplier": 0.3,
    "prana_efficiency": 0.2,
    "knowledge_boost": 2.0,
    "culture_boost": 0.15,
    "entropy_reduction": 0.04,
    "truth_visibility_boost": 0.08,
    "trade_multiplier": 0.25,
    "belonging_boost": 0.15,
    "ideology_spread_rate": 0.15,
    "free_time": 0.15,
    "explore_range": 0.2,
}

SCIENCE_PROPOSAL_PROMPT = """\
You are {name}, a soul in {loka} during the {yuga} age.
You have lived {lives} lives. Your karma is {karma}. Your skills: {skills}.

Your civilization has discovered these innovations:
{innovations}

Your people have understood these truths about the world:
{discoveries}

You have a flash of insight. By COMBINING what your civilization already knows,
you envision an entirely NEW field of knowledge — a new science or discipline
that nobody has conceived before.

This new field must BUILD ON at least 2 existing innovations or discoveries.
It should be something that would genuinely emerge from combining those ideas.

Examples of what emergence looks like:
- Medicine + Mathematics → "Anatomical Geometry" (mapping the body with numbers)
- Fire + Philosophy → "Thermodynamic Ethics" (understanding energy and moral order)
- Agriculture + Astronomy → "Seasonal Science" (celestial planting calendars)
- Writing + karma_returns → "Karmic Record-Keeping" (tracking moral causation)

Be creative but grounded. Name it something evocative.

Respond with ONLY a JSON object:
{{
  "field_name": "<name of the new science — 2-4 words, evocative>",
  "description": "<one sentence — what this field studies>",
  "builds_on": ["<innovation or discovery 1>", "<innovation or discovery 2>"],
  "key_insight": "<what combination of existing knowledge makes this possible>",
  "benefits": "<what this enables for civilization — be specific>"
}}
"""


class EmergentScienceEngine:
    """Lets souls autonomously create new branches of science.

    These become real nodes in the knowledge graph that other souls
    can build upon, creating truly autonomous scientific branching.
    """

    def __init__(self) -> None:
        # loka_id → list of emergent sciences created in that loka
        self.emergent_tree: dict[str, list[EmergentInnovation]] = {}
        self.all_sciences: dict[str, EmergentInnovation] = {}  # name → node (global registry)
        self.proposal_log: list[dict] = []

    def get_loka_sciences(self, loka_key: str) -> list[EmergentInnovation]:
        """Get all emergent sciences available in a loka."""
        return self.emergent_tree.get(loka_key, [])

    def get_all_innovation_names(self, loka: LokaState) -> list[str]:
        """All innovations available in a loka (predefined + emergent)."""
        loka_key = str(loka.id)
        emergent_names = [s.name for s in self.get_loka_sciences(loka_key)]
        return list(loka.innovations) + emergent_names

    async def attempt_new_science(
        self,
        tick: int,
        soul: SoulState,
        loka: LokaState,
        client: LLMClient,
        rendered_view: dict,
        discoveries: list[str],
    ) -> list[Event]:
        """A knowledgeable soul may propose a new branch of science."""
        events: list[Event] = []
        loka_key = str(loka.id)

        # --- Gate conditions ---
        # Need enough base innovations (at least 3 from tech tree or prior emergent)
        all_innovations = self.get_all_innovation_names(loka)
        if len(all_innovations) < int(LAWS["esci_min_innovations"]):
            return events

        # Need at least 2 discoveries
        if len(discoveries) < int(LAWS["esci_min_discoveries"]):
            return events

        # Soul needs relevant skills
        relevant_skills = {"teaching", "strategy", "meditation", "crafting", "healing", "trade", "oration"}
        if not any(sk in relevant_skills for sk in soul.skills):
            return events

        # Soul needs enough experience
        if soul.age < int(LAWS["esci_age_req"]) or soul.lives < int(LAWS["esci_lives_req"]):
            return events

        # 0.5% chance per tick for eligible souls
        if random.random() > LAWS["esci_attempt_chance"]:
            return events

        # Cap emergent sciences per loka to prevent explosion
        if len(self.get_loka_sciences(loka_key)) >= int(LAWS["esci_max_per_loka"]):
            return events

        # --- Build the LLM prompt ---
        from brahmanda.engine.discovery import DISCOVERABLE_MECHANICS

        discovery_descriptions = []
        for d in discoveries:
            if d in DISCOVERABLE_MECHANICS:
                discovery_descriptions.append(f"  - {d}: {DISCOVERABLE_MECHANICS[d]['truth']}")

        prompt = SCIENCE_PROPOSAL_PROMPT.format(
            name=soul.name,
            loka=rendered_view.get("loka", "unknown"),
            yuga=rendered_view.get("yuga", "unknown"),
            lives=soul.lives,
            karma=soul.karma,
            skills=", ".join(soul.skills),
            innovations=", ".join(all_innovations) if all_innovations else "none",
            discoveries="\n".join(discovery_descriptions) if discovery_descriptions else "none yet",
        )

        try:
            response = await client.generate(
                model=SOUL_MODEL,
                system="You are a visionary thinker creating a new field of knowledge. "
                       "Respond ONLY with valid JSON.",
                prompt=prompt,
                max_tokens=400,
            )
            raw = response.text
            from brahmanda.llm import strip_markdown_fences
            raw = strip_markdown_fences(raw)
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                return events

            proposal = json.loads(match.group())
            field_name = proposal.get("field_name", "").strip()
            description = proposal.get("description", "").strip()
            builds_on = proposal.get("builds_on", [])
            key_insight = proposal.get("key_insight", "")
            benefits = proposal.get("benefits", "")

            if not field_name or not description or len(builds_on) < 2:
                return events

            # Log the proposal regardless of validation
            self.proposal_log.append({
                "tick": tick, "soul": soul.name, "loka": loka_key,
                "field_name": field_name, "builds_on": builds_on,
                "description": description,
            })

            # --- Validate the proposal ---
            validated = self._validate_proposal(
                field_name, builds_on, all_innovations, discoveries, loka_key,
            )
            if not validated:
                events.append(Event(
                    tick=tick, event_type="science_proposal_rejected", loka=loka.id,
                    data={"soul": soul.name, "field_name": field_name,
                          "reason": "prerequisites not found or duplicate"},
                    description=f"{soul.name} proposes '{field_name}' but it doesn't hold up yet",
                ))
                return events

            # --- Determine effects based on what it builds on ---
            effects = self._derive_effects(builds_on, all_innovations, discoveries)

            # --- Create the emergent science node ---
            # Figure out which builds_on are discoveries vs innovations
            based_on_disc = [b for b in builds_on if b in discoveries]
            based_on_innov = [b for b in builds_on if b in all_innovations]

            science = EmergentInnovation(
                name=field_name,
                description=description,
                created_by=soul.name,
                created_tick=tick,
                prerequisites=based_on_innov,
                based_on_discoveries=based_on_disc,
                effects=effects,
            )

            # Register it
            if loka_key not in self.emergent_tree:
                self.emergent_tree[loka_key] = []
            self.emergent_tree[loka_key].append(science)
            self.all_sciences[field_name] = science

            # Add to loka's innovation list so it shows up everywhere
            loka.innovations.append(f"[S] {field_name}")  # [S] = soul-created science

            # Apply immediate effects to loka
            self._apply_effects(effects, loka)

            # Reward the soul
            soul.karma = min(200, soul.karma + 20)
            soul.memories.append(
                f"Tick {tick}: I founded a new science — {field_name}: {description}"
            )

            # Update built_upon_count for prerequisites
            for prereq_name in based_on_innov:
                # Check if it's an emergent science
                if prereq_name.replace("[S] ", "") in self.all_sciences:
                    self.all_sciences[prereq_name.replace("[S] ", "")].built_upon_count += 1

            events.append(Event(
                tick=tick, event_type="emergent_science", loka=loka.id,
                data={
                    "soul": soul.name,
                    "field_name": field_name,
                    "description": description,
                    "builds_on": builds_on,
                    "key_insight": key_insight[:200],
                    "benefits": benefits[:200],
                    "effects": effects,
                    "loka_sciences_count": len(self.emergent_tree[loka_key]),
                },
                description=(
                    f"NEW SCIENCE: {soul.name} founds '{field_name}' — {description} "
                    f"(builds on: {', '.join(builds_on)})"
                ),
            ))

        except Exception:
            pass

        return events

    def _validate_proposal(
        self,
        field_name: str,
        builds_on: list[str],
        all_innovations: list[str],
        discoveries: list[str],
        loka_key: str,
    ) -> bool:
        """Check that the proposal is valid."""
        # No duplicates (check against all known sciences + innovations)
        name_lower = field_name.lower()
        for existing in all_innovations:
            if existing.lower().replace("[s] ", "").replace("[e] ", "") == name_lower:
                return False
        if name_lower in {s.lower() for s in self.all_sciences}:
            return False

        # At least 2 builds_on must reference real innovations or discoveries
        valid_refs = 0
        # Normalize innovation names (strip [S] and [E] prefixes)
        normalized_innovations = {
            inn.replace("[S] ", "").replace("[E] ", "").lower()
            for inn in all_innovations
        }
        normalized_discoveries = {d.lower() for d in discoveries}

        for ref in builds_on:
            ref_lower = ref.lower()
            if ref_lower in normalized_innovations or ref_lower in normalized_discoveries:
                valid_refs += 1

        return valid_refs >= 2

    def _derive_effects(
        self,
        builds_on: list[str],
        all_innovations: list[str],
        discoveries: list[str],
    ) -> dict:
        """Generate bounded effects based on what the science builds on.

        Effects are moderate — roughly half the strength of a predefined
        innovation — because they're emergent and less "fundamental."
        """
        effects: dict[str, float] = {}

        # Base: every new science gives a knowledge boost
        effects["knowledge_boost"] = 1.0

        # Add effects based on what it builds on
        # If it builds on resource-related things → resource effects
        # If it builds on knowledge things → knowledge effects
        # etc.
        resource_refs = {"agriculture", "fire", "stone tools", "cooking", "metallurgy",
                         "animal husbandry", "pottery", "wheel", "weaving",
                         "cooperation_generates", "scarcity_drives_conflict"}
        knowledge_refs = {"writing", "mathematics", "philosophy", "language", "storytelling",
                          "knowledge_compounds", "entropy_cycles", "rebirth_pattern"}
        healing_refs = {"medicine", "yoga & meditation", "meditation_heals", "vices_drain",
                        "culture_heals", "love_creates"}
        culture_refs = {"storytelling", "philosophy", "culture_heals", "power_corrupts"}
        truth_refs = {"astronomy", "simulation_awareness", "karma_returns", "navigation"}

        for ref in builds_on:
            ref_lower = ref.lower()
            if ref_lower in resource_refs:
                effects["resource_multiplier"] = min(
                    ALLOWED_EFFECTS["resource_multiplier"],
                    effects.get("resource_multiplier", 0) + 0.1,
                )
            if ref_lower in knowledge_refs:
                effects["knowledge_boost"] = min(
                    ALLOWED_EFFECTS["knowledge_boost"],
                    effects.get("knowledge_boost", 0) + 0.5,
                )
            if ref_lower in healing_refs:
                effects["prana_efficiency"] = min(
                    ALLOWED_EFFECTS["prana_efficiency"],
                    effects.get("prana_efficiency", 0) + 0.1,
                )
            if ref_lower in culture_refs:
                effects["culture_boost"] = min(
                    ALLOWED_EFFECTS["culture_boost"],
                    effects.get("culture_boost", 0) + 0.05,
                )
            if ref_lower in truth_refs:
                effects["truth_visibility_boost"] = min(
                    ALLOWED_EFFECTS["truth_visibility_boost"],
                    effects.get("truth_visibility_boost", 0) + 0.03,
                )

        return effects

    def _apply_effects(self, effects: dict, loka: LokaState) -> None:
        """Apply the science's effects to the loka."""
        if "knowledge_boost" in effects:
            loka.knowledge += effects["knowledge_boost"]
        if "culture_boost" in effects:
            loka.culture = min(1.0, loka.culture + effects["culture_boost"])
        if "entropy_reduction" in effects:
            loka.entropy = max(0.0, loka.entropy - effects["entropy_reduction"])
        if "resource_multiplier" in effects:
            loka.resources += int(loka.resources * effects["resource_multiplier"])

    def get_science_tree_summary(self) -> list[dict]:
        """Get a summary of all emergent sciences for the observer report."""
        summary = []
        for name, science in self.all_sciences.items():
            summary.append({
                "name": science.name,
                "description": science.description,
                "created_by": science.created_by,
                "created_tick": science.created_tick,
                "builds_on": science.prerequisites + science.based_on_discoveries,
                "effects": science.effects,
                "built_upon_count": science.built_upon_count,
            })
        return summary
