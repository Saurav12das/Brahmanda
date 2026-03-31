"""Pydantic models — the data fabric of Brahmanda."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from brahmanda.config import LokaID, YugaType


def _uid() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Soul
# ---------------------------------------------------------------------------
class Klesha(BaseModel):
    """The five inner enemies — Arishadvarga.

    Each value ranges 0.0 (absent) to 1.0 (overwhelming).
    These compete against virtuous desires and drive souls toward darkness.
    """
    kama: float = 0.3       # lust / craving for pleasure
    krodha: float = 0.3     # wrath / anger / aggression
    lobha: float = 0.3      # greed / never enough
    moha: float = 0.3       # attachment / clinging / fear of loss
    ahamkara: float = 0.3   # ego / pride / need to dominate

    @property
    def total_darkness(self) -> float:
        """0.0 → 1.0 aggregate darkness level."""
        return (self.kama + self.krodha + self.lobha + self.moha + self.ahamkara) / 5.0

    @property
    def dominant(self) -> str:
        """The strongest vice."""
        vices = {"kama": self.kama, "krodha": self.krodha, "lobha": self.lobha,
                 "moha": self.moha, "ahamkara": self.ahamkara}
        return max(vices, key=vices.get)


class SoulState(BaseModel):
    id: str = Field(default_factory=_uid)
    name: str
    karma: int = 0
    loka: LokaID = LokaID.BHU
    alive: bool = True
    age: int = 0                          # ticks alive in current life
    lifetime: int = 0                     # total ticks across all lives
    lives: int = 1                        # samsara counter
    memories: list[str] = Field(default_factory=list)
    desires: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    resources: int = 10
    prana: float = 100.0                  # life force — 0.0 = death
    relationships: dict[str, int] = Field(default_factory=dict)  # soul_id → affinity
    klesha: Klesha = Field(default_factory=Klesha)  # the five inner enemies
    is_avatar: bool = False
    avatar_mission: str | None = None


# ---------------------------------------------------------------------------
# Action / Event
# ---------------------------------------------------------------------------
class Action(BaseModel):
    tick: int
    soul_id: str
    action_type: str
    target_id: str | None = None
    description: str = ""
    karma_delta: int = 0
    loka: LokaID = LokaID.BHU


class Event(BaseModel):
    tick: int
    event_type: str       # "birth", "death", "yuga_shift", "avatar_deploy", "pralaya", "action", ...
    loka: LokaID | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    description: str = ""


# ---------------------------------------------------------------------------
# Loka
# ---------------------------------------------------------------------------
class LokaState(BaseModel):
    id: LokaID
    name: str
    resources: int
    population: list[str] = Field(default_factory=list)   # soul IDs
    entropy: float = 0.0
    tick_accumulator: float = 0.0   # for time dilation tracking


# ---------------------------------------------------------------------------
# Universe snapshot
# ---------------------------------------------------------------------------
class UniverseSnapshot(BaseModel):
    tick: int
    yuga: YugaType
    yuga_tick: int                     # ticks elapsed in current yuga
    lokas: dict[LokaID, LokaState]
    souls: dict[str, SoulState]
    total_karma: int = 0
    global_entropy: float = 0.0
    avatars_deployed: int = 0
    events: list[Event] = Field(default_factory=list)
