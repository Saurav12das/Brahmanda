"""Asuras — chaos/glitch agents that try to hack the simulation.

Asuras are not simply "evil." They are entropy vectors — glitch entities
that stress-test the simulation's integrity, corrupt data, and create
the kind of anomalies a real simulation might produce.
"""

from __future__ import annotations

import random

from brahmanda.config import LokaID, YugaType, YUGA_PARAMS
from brahmanda.db.models import Event, LokaState, SoulState


class AsuraEvent:
    """Represents a chaos injection by an Asura."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description


class AsuraEngine:
    """Spawns and executes Asura chaos events based on yuga and entropy."""

    CHAOS_TYPES = [
        "resource_corruption",   # resources vanish or duplicate (glitch)
        "memory_injection",      # false memories planted in souls
        "karma_fluctuation",     # random karma spikes (simulation noise)
        "relationship_scramble", # trust values randomly shift
        "perception_fog",        # truth_visibility temporarily drops
    ]

    def should_spawn(self, tick: int, yuga: YugaType) -> bool:
        """Determine if an asura event triggers this tick."""
        rate = YUGA_PARAMS[yuga]["asura_spawn_rate"]
        return random.random() < rate

    def execute(
        self,
        tick: int,
        loka: LokaState,
        souls: dict[str, SoulState],
        yuga: YugaType,
    ) -> list[Event]:
        """Inject chaos into a loka. Returns events for the observer."""
        if not self.should_spawn(tick, yuga):
            return []

        chaos_type = random.choice(self.CHAOS_TYPES)
        events = []
        loka_souls = [s for s in souls.values() if s.loka == loka.id and s.alive]

        if chaos_type == "resource_corruption" and loka_souls:
            # Resources randomly appear or vanish
            delta = random.choice([-20, -10, 10, 20])
            loka.resources = max(0, loka.resources + delta)
            events.append(Event(
                tick=tick, event_type="asura_glitch", loka=loka.id,
                data={"chaos_type": chaos_type, "delta": delta},
                description=f"GLITCH: Resources in {loka.name} {'surge' if delta > 0 else 'vanish'} by {abs(delta)}",
            ))

        elif chaos_type == "memory_injection" and loka_souls:
            victim = random.choice(loka_souls)
            false_memories = [
                "I remember a great betrayal that never happened",
                "I recall a golden age that may not have existed",
                "A voice whispered that this world is not real",
                "I dreamed of beings watching us from outside",
                "I felt the ground flicker, as if the world reset for an instant",
            ]
            injected = random.choice(false_memories)
            victim.memories.append(f"Tick {tick}: {injected}")
            events.append(Event(
                tick=tick, event_type="asura_glitch", loka=loka.id,
                data={"chaos_type": chaos_type, "victim": victim.name, "memory": injected},
                description=f"GLITCH: False memory planted in {victim.name}",
            ))

        elif chaos_type == "karma_fluctuation" and loka_souls:
            victim = random.choice(loka_souls)
            noise = random.randint(-15, 15)
            victim.karma = max(-200, min(200, victim.karma + noise))
            events.append(Event(
                tick=tick, event_type="asura_glitch", loka=loka.id,
                data={"chaos_type": chaos_type, "victim": victim.name, "noise": noise},
                description=f"GLITCH: {victim.name}'s karma fluctuates by {noise:+d} (simulation noise)",
            ))

        elif chaos_type == "relationship_scramble" and len(loka_souls) >= 2:
            a, b = random.sample(loka_souls, 2)
            shift = random.randint(-10, 10)
            a.relationships[b.id] = a.relationships.get(b.id, 0) + shift
            events.append(Event(
                tick=tick, event_type="asura_glitch", loka=loka.id,
                data={"chaos_type": chaos_type, "souls": [a.name, b.name], "shift": shift},
                description=f"GLITCH: Relationship between {a.name} and {b.name} shifts by {shift:+d}",
            ))

        elif chaos_type == "perception_fog":
            loka.entropy = min(1.0, loka.entropy + 0.15)
            events.append(Event(
                tick=tick, event_type="asura_glitch", loka=loka.id,
                data={"chaos_type": chaos_type, "entropy_added": 0.15},
                description=f"GLITCH: Perception fog descends on {loka.name} — entropy spikes",
            ))

        return events
