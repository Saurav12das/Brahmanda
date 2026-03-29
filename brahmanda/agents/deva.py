"""Devas — automated scripts that enforce natural laws in Brahmanda.

Devas are not conscious agents. They are deterministic processes that
maintain the simulation's physics: weather, resource regeneration,
natural disasters, and cosmic order.
"""

from __future__ import annotations

import random

from brahmanda.config import LokaID, YugaType, YUGA_PARAMS
from brahmanda.db.models import Event, LokaState


class Deva:
    """Base class for all automated natural law scripts."""

    def __init__(self, name: str, domain: str) -> None:
        self.name = name
        self.domain = domain

    def execute(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        raise NotImplementedError


class SuryaDeva(Deva):
    """Sun god — drives resource regeneration cycles."""

    def __init__(self) -> None:
        super().__init__("Surya", "energy")

    def execute(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        params = YUGA_PARAMS[yuga]
        regen = int(5 * params["resource_multiplier"])
        loka.resources += regen
        return [Event(
            tick=tick, event_type="deva_action", loka=loka.id,
            data={"deva": self.name, "effect": "resource_regen", "amount": regen},
            description=f"Surya radiates energy — {loka.name} gains {regen} resources",
        )]


class VarunaDeva(Deva):
    """Water god — controls entropy through cleansing cycles."""

    def __init__(self) -> None:
        super().__init__("Varuna", "entropy")

    def execute(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        events = []
        # Periodic cleansing reduces entropy
        if tick % 7 == 0:
            reduction = 0.05
            loka.entropy = max(0.0, loka.entropy - reduction)
            events.append(Event(
                tick=tick, event_type="deva_action", loka=loka.id,
                data={"deva": self.name, "effect": "entropy_cleanse", "amount": reduction},
                description=f"Varuna's waters cleanse {loka.name} — entropy reduced",
            ))
        return events


class YamaDeva(Deva):
    """Death god — enforces mortality and population balance."""

    def __init__(self) -> None:
        super().__init__("Yama", "death")

    def execute(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        # Yama doesn't directly act here — mortality is handled by KarmaEngine.should_die
        # But he triggers natural disasters when entropy is too high
        events = []
        if loka.entropy > 0.8 and random.random() < 0.3:
            damage = int(loka.resources * 0.2)
            loka.resources = max(0, loka.resources - damage)
            events.append(Event(
                tick=tick, event_type="natural_disaster", loka=loka.id,
                data={"deva": self.name, "effect": "disaster", "resource_loss": damage},
                description=f"Yama's judgment: calamity strikes {loka.name}, {damage} resources lost",
            ))
        return events


class DevaCouncil:
    """Runs all devas each tick for a given loka."""

    def __init__(self) -> None:
        self.devas: list[Deva] = [
            SuryaDeva(),
            VarunaDeva(),
            YamaDeva(),
        ]

    def execute_all(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        events = []
        for deva in self.devas:
            events.extend(deva.execute(tick, loka, yuga))
        return events
