"""Sristi Niyama — The Law of Soul Propagation.

Like all mythology, it started with two — one Purusha (cosmic masculine)
and one Prakriti (cosmic feminine). From that primordial pair, all souls
descend through love.

But propagation is CONDITIONAL. It serves a higher goal: knowledge,
proving oneself, making your name in the world. Every soul wants to
show they are the best. Once enough souls have "made their name"
(manifested potential, gained influence, accumulated karma), the
cosmic drive to create new life diminishes.

This creates a natural population arc:
  - Early universe: few proven souls → high birth rate
  - Mid universe: some proven → moderate births
  - Late universe: threshold met → propagation slows to a trickle

The higher goal is probably knowledge — but showing a soul is the best
is how that knowledge manifests. The propagation gate tracks this
collectively without any extra LLM calls.

Design: a pure math layer that modulates the existing atman_birth_chance.
"""

from __future__ import annotations

import math

from brahmanda.config import LAWS
from brahmanda.db.models import SoulState


def evaluate_name_made(soul: SoulState) -> bool:
    """Has this soul "proved itself" — made their name in the world?

    A soul counts as proven if ANY of these hold:
    - Manifested their innate potential (became a Rishi, Tyrant, Healer, etc.)
    - Accumulated significant karma (positive OR negative — notoriety counts)
    - Achieved notable influence over others
    """
    if soul.name_made:
        return True  # already proven, stays proven

    proven = False

    # Manifested potential — the clearest sign of "showing you're the best"
    if LAWS["propagation_potential_counts"] and soul.potential_manifested:
        proven = True

    # High |karma| — you've made a mark, for good or evil
    if abs(soul.karma) >= LAWS["propagation_karma_threshold"]:
        proven = True

    # High influence — you dominate or inspire others
    if soul.influence >= LAWS["propagation_influence_threshold"]:
        proven = True

    if proven:
        soul.name_made = True

    return proven


def compute_propagation_factor(
    all_souls: dict[str, SoulState],
    loka_knowledge: float = 1.0,
) -> float:
    """Compute the propagation multiplier (0.0 to 1.0) that gates birth chance.

    As more souls "make their name", this factor decays toward the minimum.
    Knowledge accumulation also dampens it — the higher goal is being met.

    Uses a sigmoid decay so the transition is smooth, not a cliff.

    Returns:
        Float between propagation_min_factor and 1.0.
        Multiply this with atman_birth_chance to get effective birth rate.
    """
    if not all_souls:
        return 1.0

    # Count all souls that ever existed (alive or dead, current or past lives)
    total_souls = len(all_souls)
    proven_count = sum(1 for s in all_souls.values() if s.name_made)

    if total_souls == 0:
        return 1.0

    proven_ratio = proven_count / total_souls
    threshold = LAWS["propagation_proven_threshold"]
    steepness = LAWS["propagation_decay_steepness"]
    min_factor = LAWS["propagation_min_factor"]

    # Sigmoid decay: 1.0 when proven_ratio << threshold,
    # drops toward min_factor as proven_ratio approaches/exceeds threshold
    # f(x) = 1 / (1 + e^(steepness * (x - threshold)))
    exponent = steepness * (proven_ratio - threshold)
    # Clamp exponent to avoid overflow
    exponent = max(-20.0, min(20.0, exponent))
    sigmoid = 1.0 / (1.0 + math.exp(exponent))

    # Scale sigmoid (which goes 0-1) to range [min_factor, 1.0]
    factor = min_factor + (1.0 - min_factor) * sigmoid

    # Knowledge dampening — as collective knowledge grows, propagation need fades
    knowledge_ceiling = LAWS["propagation_knowledge_ceiling"]
    if loka_knowledge > 1.0 and knowledge_ceiling > 0:
        knowledge_dampening = max(0.5, 1.0 - (loka_knowledge / knowledge_ceiling) * 0.3)
        factor *= knowledge_dampening

    return max(min_factor, min(1.0, factor))


def get_propagation_stats(all_souls: dict[str, SoulState]) -> dict:
    """Return propagation statistics for observer/logging."""
    total = len(all_souls)
    proven = sum(1 for s in all_souls.values() if s.name_made)
    alive = sum(1 for s in all_souls.values() if s.alive)
    primordial = sum(1 for s in all_souls.values() if s.is_primordial)
    generations = max((s.lives for s in all_souls.values()), default=1)

    return {
        "total_souls_ever": total,
        "proven_souls": proven,
        "proven_ratio": round(proven / total, 3) if total > 0 else 0.0,
        "alive_souls": alive,
        "primordial_count": primordial,
        "max_samsara_cycle": generations,
        "threshold": LAWS["propagation_proven_threshold"],
    }
