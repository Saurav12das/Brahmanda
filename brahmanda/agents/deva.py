"""Devas — automated scripts that enforce natural laws in Brahmanda.

Devas are deterministic processes: resource regeneration, entropy
cleansing, and natural disasters. All scale dynamically with
conditions — no fixed intervals.
"""

from __future__ import annotations

import random

from brahmanda.config import LOKA_CONFIG, LokaID, YugaType, YUGA_PARAMS
from brahmanda.db.models import Event, LokaState


class Deva:
    def __init__(self, name: str, domain: str) -> None:
        self.name = name
        self.domain = domain

    def execute(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        raise NotImplementedError


class SuryaDeva(Deva):
    """Sun god — resource regeneration with diminishing returns."""

    def __init__(self) -> None:
        super().__init__("Surya", "energy")

    def execute(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        params = YUGA_PARAMS[yuga]
        base_regen = int(5 * params["resource_multiplier"])
        base_resources = LOKA_CONFIG[loka.id]["base_resources"]

        # Diminishing returns — cap regen when resources exceed 2x yuga-adjusted base
        target = int(base_resources * params["resource_multiplier"])
        if loka.resources > target * 2:
            regen = max(1, base_regen // 4)
        elif loka.resources > target:
            regen = max(1, base_regen // 2)
        else:
            regen = base_regen

        loka.resources += regen
        return [Event(
            tick=tick, event_type="deva_action", loka=loka.id,
            data={"deva": self.name, "effect": "resource_regen", "amount": regen},
            description=f"Surya radiates energy — {loka.name} gains {regen} resources",
        )]


class VarunaDeva(Deva):
    """Water god — entropy cleansing, responsive to conditions."""

    def __init__(self) -> None:
        super().__init__("Varuna", "entropy")

    def execute(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        events = []
        # Cleanse when entropy exceeds threshold — scales with severity
        if loka.entropy > 0.3:
            reduction = min(0.1, loka.entropy * 0.08)
            loka.entropy = max(0.0, loka.entropy - reduction)
            events.append(Event(
                tick=tick, event_type="deva_action", loka=loka.id,
                data={"deva": self.name, "effect": "entropy_cleanse", "amount": round(reduction, 3)},
                description=f"Varuna's waters cleanse {loka.name} — entropy reduced by {reduction:.3f}",
            ))
        return events


class YamaDeva(Deva):
    """Death god — natural disasters scale with population density."""

    def __init__(self) -> None:
        super().__init__("Yama", "death")

    def execute(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        events = []
        population = len(loka.population)
        # Disasters when entropy high — damage scales with population
        if loka.entropy > 0.7 and random.random() < 0.3:
            density_factor = 1 + population / 10
            damage = int(loka.resources * 0.15 * density_factor)
            loka.resources = max(0, loka.resources - damage)
            events.append(Event(
                tick=tick, event_type="natural_disaster", loka=loka.id,
                data={"deva": self.name, "effect": "disaster", "resource_loss": damage, "population": population},
                description=f"Yama's judgment: calamity strikes {loka.name}, {damage} resources lost (pop={population})",
            ))
        return events


class DevaCouncil:
    def __init__(self) -> None:
        self.devas: list[Deva] = [SuryaDeva(), VarunaDeva(), YamaDeva()]

    def execute_all(self, tick: int, loka: LokaState, yuga: YugaType) -> list[Event]:
        events = []
        for deva in self.devas:
            events.extend(deva.execute(tick, loka, yuga))
        return events
