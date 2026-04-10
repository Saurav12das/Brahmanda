"""Atman Engine — the soul's deepest needs beyond survival.

Resources keep you alive. Prana is your life force. But what makes
a soul HUMAN is the search for meaning:

1. MOKSHA — the desire to transcend, to escape the cycle
2. BELONGING — the need to be part of something, to matter to someone
3. PURPOSE — the feeling that your existence has meaning

When these needs are met, souls flourish and cooperate.
When they fail, souls turn against society — conflict, destruction, nihilism.

Also models:
- Random encounters (destiny — souls cross paths by chance)
- Love bonds (deep connections that create new life)
- Generation through love (new souls born from bonded pairs)
- Soul fulfillment scoring (how close to moksha/belonging/purpose)
"""

from __future__ import annotations

import random

from brahmanda.config import LAWS, LOKA_CONFIG, LokaID, YugaType
from brahmanda.db.models import Event, Klesha, LokaState, SoulState, _uid
from brahmanda.engine.potential import assign_potential
from brahmanda.engine.propagation import compute_propagation_factor, evaluate_name_made


# ---------------------------------------------------------------------------
# Soul Fulfillment — the three existential needs
# ---------------------------------------------------------------------------
def calculate_fulfillment(soul: SoulState, loka: LokaState, all_souls: dict[str, SoulState]) -> dict:
    """Calculate how fulfilled a soul's three existential needs are.
    Each ranges 0.0 (empty) to 1.0 (fully met).
    """
    # MOKSHA — transcendence need
    # Met by: meditation, high karma, low vices, philosophical ideology
    moksha_karma = max(0, soul.karma) / 200  # 0-1
    moksha_vice = 1.0 - soul.klesha.total_darkness  # low vices = closer to moksha
    moksha_practice = 0.3 if "meditation" in soul.skills else 0.0
    moksha_ideology = 0.2 if soul.ideology and "moksha" in (soul.ideology or "").lower() else 0.0
    moksha = min(1.0, (moksha_karma * 0.3 + moksha_vice * 0.3 + moksha_practice + moksha_ideology))

    # BELONGING — community need
    # Met by: positive relationships, being in a populated loka, having an ideology shared by others
    positive_rels = sum(1 for v in soul.relationships.values() if v > 5)
    total_rels = max(1, len(soul.relationships))
    belonging_rels = min(1.0, positive_rels / 3)  # 3+ friends = fully met

    pop = len(loka.population)
    belonging_community = min(1.0, pop / 8)  # 8+ neighbors = full community

    # Shared ideology bonus
    if soul.ideology:
        same_ideo = sum(1 for sid in loka.population
                        if sid in all_souls and all_souls[sid].ideology == soul.ideology
                        and sid != soul.id)
        belonging_shared = min(0.3, same_ideo * 0.1)
    else:
        belonging_shared = 0.0

    belonging = min(1.0, belonging_rels * 0.4 + belonging_community * 0.3 + belonging_shared)

    # PURPOSE — validation need
    # Met by: manifested potential, high influence, teaching others, creating things
    purpose_manifest = 0.4 if soul.potential_manifested else 0.0
    purpose_influence = soul.influence * 0.3
    purpose_skills = min(0.3, len(soul.skills) * 0.1)
    purpose_age = min(0.2, soul.age / 100)  # wisdom from experience
    purpose = min(1.0, purpose_manifest + purpose_influence + purpose_skills + purpose_age)

    return {
        "moksha": round(moksha, 2),
        "belonging": round(belonging, 2),
        "purpose": round(purpose, 2),
        "total": round((moksha + belonging + purpose) / 3, 2),
    }


# ---------------------------------------------------------------------------
# Random Encounters — destiny brings souls together
# ---------------------------------------------------------------------------
def process_encounters(tick: int, loka: LokaState, souls: list[SoulState]) -> list[Event]:
    """Each tick, random pairs of souls have meaningful encounters.
    These can spark friendship, rivalry, or love.
    """
    events = []
    if len(souls) < 2:
        return events

    # 15% chance of a significant encounter per tick per loka
    if random.random() > LAWS["atman_encounter_chance"]:
        return events

    soul_a, soul_b = random.sample(souls, 2)

    # What kind of encounter? Based on compatibility
    compatibility = _calculate_compatibility(soul_a, soul_b)

    if compatibility > LAWS["atman_compatibility_positive"]:
        # Strong positive encounter — potential love or deep friendship
        _update_rel(soul_a, soul_b.id, random.randint(5, 15))
        _update_rel(soul_b, soul_a.id, random.randint(5, 15))

        # Hope contagion — spreads between bonded souls with diminishing returns
        if compatibility > LAWS["atman_compatibility_positive"]:
            cap = LAWS["hope_contagion_cap"]
            rate = LAWS["hope_contagion_rate"]
            for s in (soul_a, soul_b):
                other = soul_b if s is soul_a else soul_a
                # Diminishing returns: souls near extremes absorb less
                absorption = rate * (1.0 - abs(s.hope) * 0.8)
                s.hope += (other.hope - s.hope) * absorption
                # Hard cap from contagion
                s.hope = max(-cap, min(cap, s.hope))

        encounter_type = "love_spark" if compatibility > 0.8 and random.random() < 0.3 else "deep_bond"

        if encounter_type == "love_spark":
            soul_a.memories.append(f"Tick {tick}: I felt a deep connection with {soul_b.name}")
            soul_b.memories.append(f"Tick {tick}: Something stirred when I met {soul_a.name}")
            events.append(Event(
                tick=tick, event_type="encounter_love", loka=loka.id,
                data={"soul_a": soul_a.name, "soul_b": soul_b.name,
                      "compatibility": round(compatibility, 2)},
                description=f"♥ {soul_a.name} and {soul_b.name} feel a profound connection (compatibility={compatibility:.2f})",
            ))
        else:
            events.append(Event(
                tick=tick, event_type="encounter_bond", loka=loka.id,
                data={"soul_a": soul_a.name, "soul_b": soul_b.name},
                description=f"{soul_a.name} and {soul_b.name} form a deep bond",
            ))

    elif compatibility < LAWS["atman_compatibility_negative"]:
        # Negative encounter — instant rivalry
        _update_rel(soul_a, soul_b.id, random.randint(-10, -3))
        _update_rel(soul_b, soul_a.id, random.randint(-10, -3))
        events.append(Event(
            tick=tick, event_type="encounter_rivalry", loka=loka.id,
            data={"soul_a": soul_a.name, "soul_b": soul_b.name},
            description=f"⚔ {soul_a.name} and {soul_b.name} clash on sight — instant rivals",
        ))

    return events


def _calculate_compatibility(a: SoulState, b: SoulState) -> float:
    """How compatible are two souls? -1.0 to +1.0.

    Based on: complementary desires, opposite vices (opposites attract
    in some dimensions), shared ideology, karma alignment.
    """
    # Shared desires
    shared_desires = len(set(a.desires) & set(b.desires))
    desire_score = shared_desires * 0.15

    # Karma alignment (similar karma = more compatible)
    karma_diff = abs(a.karma - b.karma)
    karma_score = max(-0.3, 0.3 - karma_diff / 200)

    # Vice complementarity (one strong where other is weak = attraction)
    vice_complement = 0
    for va, vb in [(a.klesha.kama, b.klesha.moha), (a.klesha.moha, b.klesha.kama),
                    (a.klesha.krodha, b.klesha.ahamkara)]:
        if abs(va - vb) > 0.4:
            vice_complement += 0.1

    # Shared ideology
    ideo_score = 0.2 if a.ideology and a.ideology == b.ideology else 0.0

    # Random chemistry — sometimes it just clicks
    chemistry = random.uniform(-0.2, 0.2)

    return max(-1.0, min(1.0, desire_score + karma_score + vice_complement + ideo_score + chemistry))


# ---------------------------------------------------------------------------
# Love & Generation — love creates new life
# ---------------------------------------------------------------------------
def process_love_generation(
    tick: int, loka: LokaState, souls: list[SoulState], all_souls: dict[str, SoulState],
) -> list[Event]:
    """Deeply bonded soul pairs can create new souls (next generation).
    Love is the ticket to continuation — not Brahma's arbitrary spawning.
    """
    events = []
    if len(souls) < 2:
        return events

    # Find bonded pairs (mutual affinity > 20)
    bonded_pairs = []
    checked = set()
    for soul in souls:
        for other_id, affinity in soul.relationships.items():
            pair = tuple(sorted([soul.id, other_id]))
            if pair in checked or other_id not in all_souls:
                continue
            checked.add(pair)
            other = all_souls[other_id]
            if not other.alive or other.loka != soul.loka:
                continue
            mutual = other.relationships.get(soul.id, 0)
            if affinity > LAWS["atman_love_bond_threshold"] and mutual > LAWS["atman_love_bond_threshold"]:
                bonded_pairs.append((soul, other))

    # Sristi Niyama — propagation is conditional on souls proving themselves
    avg_knowledge = sum(
        maya_loka.knowledge for maya_loka in [loka]
    ) / 1.0  # single loka context
    propagation_factor = compute_propagation_factor(all_souls, avg_knowledge)
    effective_birth_chance = LAWS["atman_birth_chance"] * propagation_factor

    for parent_a, parent_b in bonded_pairs:
        # Birth chance modulated by propagation factor (decays as souls "make their name")
        if random.random() > effective_birth_chance:
            continue

        # Resource check — need enough resources to sustain a new soul
        if loka.resources < LAWS["atman_birth_resource_req"]:
            continue

        # Create child with inherited traits
        child = _create_child(parent_a, parent_b, loka)
        all_souls[child.id] = child
        loka.population.append(child.id)

        # Parent → Child memory inheritance (family wisdom)
        parent_wisdom = []
        for parent in (parent_a, parent_b):
            if parent.memories:
                # Pick the most meaningful memory from each parent
                teachings = [m for m in parent.memories if any(kw in m.lower() for kw in
                            ("taught", "discovered", "truth", "learned", "founded", "invented"))]
                if teachings:
                    parent_wisdom.append(f"My parent {parent.name} said: '{teachings[-1][:60]}'")
                elif len(parent.memories) > 2:
                    parent_wisdom.append(f"Family memory from {parent.name}: '{parent.memories[-1][:60]}'")
        child.memories = parent_wisdom + child.memories

        # Also inject Akashic Memory from birth loka
        akashic = [m for m in loka.akashic_memory if m not in child.memories]
        if akashic:
            child.memories = random.sample(akashic, min(2, len(akashic))) + child.memories

        # Parents invest resources
        parent_a.resources = max(0, parent_a.resources - 5)
        parent_b.resources = max(0, parent_b.resources - 5)

        # Strengthen parent bond through shared creation
        _update_rel(parent_a, parent_b.id, 5)
        _update_rel(parent_b, parent_a.id, 5)

        # Child starts with relationships to parents
        child.relationships[parent_a.id] = 15
        child.relationships[parent_b.id] = 15
        parent_a.relationships[child.id] = 20
        parent_b.relationships[child.id] = 20

        events.append(Event(
            tick=tick, event_type="birth_from_love", loka=loka.id,
            data={
                "child": child.name, "parent_a": parent_a.name,
                "parent_b": parent_b.name, "potential": child.potential,
                "dominant_vice": child.klesha.dominant,
                "propagation_factor": round(propagation_factor, 3),
            },
            description=f"♥ New soul born: {child.name} — child of {parent_a.name} and {parent_b.name} "
                        f"(potential={child.potential:+.3f}, propagation={propagation_factor:.2f})",
        ))

    return events


def _create_child(parent_a: SoulState, parent_b: SoulState, loka: LokaState) -> SoulState:
    """Create a child soul inheriting traits from both parents + mutation."""
    # Name: combine parent names
    names_pool = [
        "Priya", "Dhruv", "Aanya", "Veer", "Isha", "Rohan", "Kavya", "Aarav",
        "Meera", "Aryan", "Ananya", "Vivaan", "Diya", "Reyansh", "Saanvi",
        "Aditya", "Kiara", "Rudra", "Avni", "Shaurya", "Tara", "Ojas",
        "Nila", "Agni", "Lakshya", "Jaya", "Surya", "Aditi", "Viraj", "Uma",
    ]
    name = random.choice(names_pool)

    # Inherit vices from parents (average + mutation)
    def _inherit_vice(va: float, vb: float) -> float:
        avg = (va + vb) / 2
        mutation = random.uniform(-0.15, 0.15)
        return max(0.05, min(1.0, avg + mutation))

    klesha = Klesha(
        kama=_inherit_vice(parent_a.klesha.kama, parent_b.klesha.kama),
        krodha=_inherit_vice(parent_a.klesha.krodha, parent_b.klesha.krodha),
        lobha=_inherit_vice(parent_a.klesha.lobha, parent_b.klesha.lobha),
        moha=_inherit_vice(parent_a.klesha.moha, parent_b.klesha.moha),
        ahamkara=_inherit_vice(parent_a.klesha.ahamkara, parent_b.klesha.ahamkara),
    )

    # Inherit some desires from parents, mutate others
    parent_desires = list(set(parent_a.desires + parent_b.desires))
    child_desires = random.sample(parent_desires, min(2, len(parent_desires)))

    # Inherit one skill from a parent
    parent_skills = list(set(parent_a.skills + parent_b.skills))
    child_skills = random.sample(parent_skills, min(1, len(parent_skills))) if parent_skills else []

    hope_inherited = (parent_a.hope + parent_b.hope) / 2 + random.uniform(-0.1, 0.1)
    hope_inherited = max(-1.0, min(1.0, hope_inherited))

    return SoulState(
        id=_uid(),
        name=name,
        karma=0,  # children start neutral
        loka=loka.id,
        alive=True,
        resources=5,
        prana=100.0,
        potential=assign_potential(),
        desires=child_desires,
        skills=child_skills,
        klesha=klesha,
        hope=hope_inherited,
    )


# ---------------------------------------------------------------------------
# Alienation — when existential needs fail, souls turn against society
# ---------------------------------------------------------------------------
def check_alienation(tick: int, soul: SoulState, fulfillment: dict) -> list[Event]:
    """When all three needs are unmet, the soul becomes alienated.
    Alienation amplifies vices and drives conflict against society.
    """
    events = []
    total = fulfillment["total"]

    if total > LAWS["atman_alienation_threshold"]:
        return events  # needs are sufficiently met

    # Soul is alienated — vices intensify
    alienation_severity = max(0, LAWS["atman_alienation_threshold"] - total) * 3  # 0-1 scale

    # Small vice boost from alienation each tick
    boost = alienation_severity * 0.01
    soul.klesha = type(soul.klesha)(
        kama=min(1.0, soul.klesha.kama + boost * 0.5),
        krodha=min(1.0, soul.klesha.krodha + boost * LAWS["atman_vice_boost_krodha"]),  # anger grows fastest
        lobha=min(1.0, soul.klesha.lobha + boost),
        moha=min(1.0, soul.klesha.moha + boost * 0.3),
        ahamkara=min(1.0, soul.klesha.ahamkara + boost * LAWS["atman_vice_boost_ahamkara"]),
    )

    # Alienation drives despair; fulfillment generates hope
    if total < 0.1:
        soul.hope = max(-1.0, soul.hope * 0.9 - 0.03)  # despair accumulates
    elif total > LAWS["atman_alienation_threshold"]:
        # Mild hope boost from fulfillment
        soul.hope = min(1.0, soul.hope + (total - LAWS["atman_alienation_threshold"]) * 0.02)

    # Severe alienation events (rare but impactful)
    if total < 0.1 and random.random() < LAWS["atman_alienation_crisis_chance"]:
        events.append(Event(
            tick=tick, event_type="alienation_crisis", loka=soul.loka,
            data={"soul": soul.name, "fulfillment": fulfillment,
                  "severity": round(alienation_severity, 2)},
            description=f"☠ {soul.name} is deeply alienated — "
                        f"moksha={fulfillment['moksha']}, belonging={fulfillment['belonging']}, "
                        f"purpose={fulfillment['purpose']}. Vices intensify.",
        ))

    return events


# ---------------------------------------------------------------------------
# Main process function
# ---------------------------------------------------------------------------
def process_atman(
    tick: int, loka: LokaState, souls: list[SoulState], all_souls: dict[str, SoulState],
) -> list[Event]:
    """Run all soul-needs systems for a loka."""
    events = []

    # Random encounters (destiny)
    events.extend(process_encounters(tick, loka, souls))

    # Love and generation
    events.extend(process_love_generation(tick, loka, souls, all_souls))

    # Fulfillment check + alienation + propagation name tracking
    for soul in souls:
        fulfillment = calculate_fulfillment(soul, loka, all_souls)
        events.extend(check_alienation(tick, soul, fulfillment))
        # Sristi Niyama: check if this soul has "made their name"
        evaluate_name_made(soul)

    # Hope group correction — prevent runaway spirals
    if souls:
        avg_hope = sum(s.hope for s in souls) / len(souls)
        threshold = LAWS["hope_group_correction_threshold"]
        correction_rate = LAWS["hope_group_correction_rate"]
        if abs(avg_hope) > threshold:
            correction = correction_rate * (0 - avg_hope)
            for soul in souls:
                soul.hope = max(-1.0, min(1.0, soul.hope + correction))

    return events


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _update_rel(soul: SoulState, other_id: str, delta: int) -> None:
    current = soul.relationships.get(other_id, 0)
    soul.relationships[other_id] = max(-100, min(100, current + delta))
