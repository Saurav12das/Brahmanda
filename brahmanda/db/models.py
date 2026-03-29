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
    relationships: dict[str, int] = Field(default_factory=dict)  # soul_id → affinity
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
