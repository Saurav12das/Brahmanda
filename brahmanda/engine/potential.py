"""Potential Engine — the innate spark that makes a soul extraordinary.

Every soul is born with a random potential value. Most are near zero
(ordinary). A rare few have high potential — positive or negative.
Whether that potential manifests, and in what direction, depends
entirely on environment: society (loka culture/knowledge), peers
(nearby souls' karma/actions), and family (relationships).

The same high-potential soul can become a great sage or a great tyrant.
The environment decides.
"""

from __future__ import annotations

import random

from brahmanda.db.models import Event, LokaState, SoulState


# What a soul can become when their potential activates
POSITIVE_MANIFESTATIONS = [
    {"title": "Rishi (Great Sage)", "effect": "knowledge", "magnitude": 3.0,
     "desc": "achieves deep spiritual insight, knowledge radiates to all"},
    {"title": "Vaidya (Healer)", "effect": "prana_boost", "magnitude": 15.0,
     "desc": "discovers the art of healing, restores life force to the weak"},
    {"title": "Acharya (Master Teacher)", "effect": "ideology_spread", "magnitude": 1.0,
     "desc": "becomes a legendary teacher, ideas spread across the realm"},
    {"title": "Shilpi (Master Artisan)", "effect": "resources", "magnitude": 20,
     "desc": "creates works of extraordinary beauty and utility"},
    {"title": "Kavi (Great Poet)", "effect": "culture", "magnitude": 0.15,
     "desc": "produces art that elevates the soul of civilization"},
    {"title": "Ganita (Mathematician)", "effect": "innovation", "magnitude": 1.0,
     "desc": "unlocks patterns in nature that accelerate all knowledge"},
    {"title": "Dharmarakshak (Protector)", "effect": "entropy_reduce", "magnitude": 0.1,
     "desc": "brings order and justice, reducing chaos in the realm"},
    {"title": "Vanijya (Trade Master)", "effect": "resources_all", "magnitude": 5,
     "desc": "creates trade networks that enrich everyone"},
]

NEGATIVE_MANIFESTATIONS = [
    {"title": "Asura Raja (Demon King)", "effect": "entropy_increase", "magnitude": 0.2,
     "desc": "spreads chaos and destruction across the realm"},
    {"title": "Chora (Master Thief)", "effect": "drain_others", "magnitude": 5,
     "desc": "drains resources from the weak with cunning efficiency"},
    {"title": "Mayavi (Grand Deceiver)", "effect": "false_ideology", "magnitude": 1.0,
     "desc": "spreads corrupted beliefs that poison minds"},
    {"title": "Krodhi (Wrath Incarnate)", "effect": "prana_damage", "magnitude": 10.0,
     "desc": "unleashes violence that weakens all nearby souls"},
    {"title": "Lobhi (Hoarder Supreme)", "effect": "resource_drain", "magnitude": 30,
     "desc": "concentrates all wealth, starving the community"},
    {"title": "Viplava (Revolutionary)", "effect": "knowledge_destroy", "magnitude": 2.0,
     "desc": "burns the old order — including its knowledge"},
    {"title": "Mrityudoot (Death Bringer)", "effect": "prana_mass_drain", "magnitude": 5.0,
     "desc": "brings plague and suffering to the realm"},
]


def assign_potential() -> float:
    """Assign innate potential at birth/rebirth.

    Distribution: most souls near 0 (ordinary).
    ~5% have notable potential (|p| > 0.3)
    ~1% have high potential (|p| > 0.6)
    ~0.1% have extraordinary potential (|p| > 0.9)

    Sign is random — positive or negative potential equally likely.
    """
    # Exponential distribution creates the long tail — very rare high values
    magnitude = random.expovariate(8.0)  # steeper curve = rarer outliers
    magnitude = min(1.0, magnitude)
    sign = random.choice([-1, 1])
    return round(sign * magnitude, 3)


def evaluate_environment(soul: SoulState, loka: LokaState, all_souls: dict[str, SoulState]) -> float:
    """Evaluate the environmental pressure on a soul's potential.

    Returns a value from -1.0 (hostile, pushes toward negative manifestation)
    to +1.0 (nurturing, pushes toward positive manifestation).

    Factors:
    - Society: loka culture level, knowledge level, entropy
    - Peers: average karma of nearby souls
    - Relationships: net affinity (supportive vs hostile)
    """
    # Society factor (-0.5 to +0.5)
    society = (loka.culture * 0.3 + min(1.0, loka.knowledge / 20) * 0.3 - loka.entropy * 0.4)

    # Peer factor (-0.3 to +0.3)
    peer_souls = [all_souls[sid] for sid in loka.population
                  if sid in all_souls and sid != soul.id and all_souls[sid].alive]
    if peer_souls:
        avg_peer_karma = sum(s.karma for s in peer_souls) / len(peer_souls)
        peer = max(-0.3, min(0.3, avg_peer_karma / 200))
    else:
        peer = 0.0

    # Relationship factor (-0.3 to +0.3)
    if soul.relationships:
        avg_affinity = sum(soul.relationships.values()) / len(soul.relationships)
        relationship = max(-0.3, min(0.3, avg_affinity / 100))
    else:
        relationship = 0.0

    return max(-1.0, min(1.0, society + peer + relationship))


def check_manifestation(
    tick: int,
    soul: SoulState,
    loka: LokaState,
    all_souls: dict[str, SoulState],
) -> list[Event]:
    """Check if a soul's potential manifests this tick.

    Manifestation probability:
    - Base: |potential| * 0.001 per tick (a soul with 0.5 potential has 0.05% chance/tick)
    - Age boost: higher after age 20 (maturity)
    - Already manifested souls don't manifest again in this life
    """
    events = []

    if soul.potential_manifested is not None:
        return events  # already manifested this life
    if abs(soul.potential) < 0.1:
        return events  # too ordinary
    if soul.age < 20:
        return events  # too young

    # Manifestation probability
    age_factor = min(2.0, soul.age / 40)  # peaks at age 80
    chance = abs(soul.potential) * 0.001 * age_factor

    if random.random() >= chance:
        return events

    # POTENTIAL ACTIVATES — which direction?
    env = evaluate_environment(soul, loka, all_souls)

    # The direction is: potential_sign * environment
    # High positive potential + good environment → positive manifestation
    # High positive potential + bad environment → could go either way
    # High negative potential + any environment → biased negative
    direction_score = soul.potential * 0.6 + env * 0.4

    if direction_score > 0:
        manifest = random.choice(POSITIVE_MANIFESTATIONS)
    else:
        manifest = random.choice(NEGATIVE_MANIFESTATIONS)

    soul.potential_manifested = manifest["title"]

    # Apply the manifestation effect
    effect = manifest["effect"]
    mag = manifest["magnitude"]

    if effect == "knowledge":
        loka.knowledge += mag
    elif effect == "prana_boost":
        # Heal nearby souls
        for sid in loka.population:
            if sid in all_souls and sid != soul.id:
                all_souls[sid].prana = min(100.0, all_souls[sid].prana + mag)
    elif effect == "culture":
        loka.culture = min(1.0, loka.culture + mag)
    elif effect == "resources":
        loka.resources += int(mag)
    elif effect == "resources_all":
        for sid in loka.population:
            if sid in all_souls:
                all_souls[sid].resources += int(mag)
    elif effect == "entropy_reduce":
        loka.entropy = max(0.0, loka.entropy - mag)
    elif effect == "innovation":
        loka.knowledge += mag * 5  # massive knowledge boost
    elif effect == "ideology_spread":
        if soul.ideology:
            for sid in loka.population:
                if sid in all_souls and sid != soul.id and not all_souls[sid].ideology:
                    all_souls[sid].ideology = soul.ideology
    elif effect == "entropy_increase":
        loka.entropy = min(1.0, loka.entropy + mag)
    elif effect == "drain_others":
        for sid in loka.population:
            if sid in all_souls and sid != soul.id:
                stolen = min(int(mag), all_souls[sid].resources)
                all_souls[sid].resources -= stolen
                soul.resources += stolen
    elif effect == "false_ideology":
        dark_ideologies = [
            "only the strong deserve to live",
            "trust no one — all beings are enemies",
            "hoard everything — scarcity is eternal",
            "power is the only truth",
        ]
        dark_ideo = random.choice(dark_ideologies)
        for sid in loka.population:
            if sid in all_souls and sid != soul.id and random.random() < 0.3:
                all_souls[sid].ideology = dark_ideo
    elif effect == "prana_damage":
        for sid in loka.population:
            if sid in all_souls and sid != soul.id:
                all_souls[sid].prana = max(0.0, all_souls[sid].prana - mag)
    elif effect == "resource_drain":
        for sid in loka.population:
            if sid in all_souls and sid != soul.id:
                drained = min(int(mag / max(1, len(loka.population))), all_souls[sid].resources)
                all_souls[sid].resources -= drained
                soul.resources += drained
    elif effect == "knowledge_destroy":
        loka.knowledge = max(0.1, loka.knowledge - mag)
    elif effect == "prana_mass_drain":
        for sid in loka.population:
            if sid in all_souls and sid != soul.id:
                all_souls[sid].prana = max(0.0, all_souls[sid].prana - mag)

    # The soul gains karma/skills from manifestation
    if direction_score > 0:
        soul.karma = min(200, soul.karma + 20)
        if manifest["title"] not in (soul.skills or []):
            soul.skills.append(manifest["title"].split("(")[1].rstrip(")").lower()
                               if "(" in manifest["title"] else "greatness")
    else:
        soul.karma = max(-200, soul.karma - 20)

    events.append(Event(
        tick=tick, event_type="potential_manifest", loka=loka.id,
        data={
            "soul": soul.name, "potential": soul.potential,
            "environment": round(env, 2), "direction": round(direction_score, 2),
            "manifestation": manifest["title"], "effect": effect,
            "positive": direction_score > 0,
        },
        description=f"{'✦' if direction_score > 0 else '☠'} {soul.name} becomes {manifest['title']} — "
                    f"{manifest['desc']} (potential={soul.potential:+.3f}, env={env:+.2f})",
    ))

    return events
