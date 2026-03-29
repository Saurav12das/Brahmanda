"""Yuga Clock — the cosmic time engine of Brahmanda.

Manages the four epochs (Satya → Treta → Dvapara → Kali) and their
effect on global simulation parameters.
"""

from __future__ import annotations

from brahmanda.config import TICKS_PER_YUGA, YUGA_ORDER, YUGA_PARAMS, YugaType


class YugaClock:
    """Tracks cosmic time across the four yugas of a Mahayuga cycle."""

    def __init__(self) -> None:
        self.current_yuga: YugaType = YUGA_ORDER[0]
        self.yuga_index: int = 0
        self.yuga_tick: int = 0           # ticks elapsed in current yuga
        self.global_tick: int = 0         # total ticks since creation
        self.mahayuga_complete: bool = False

    @property
    def params(self) -> dict:
        return YUGA_PARAMS[self.current_yuga]

    @property
    def yuga_progress(self) -> float:
        """0.0 → 1.0 progress through current yuga."""
        total = TICKS_PER_YUGA[self.current_yuga.value]
        return self.yuga_tick / total

    @property
    def cosmic_progress(self) -> float:
        """0.0 → 1.0 progress through entire Mahayuga."""
        from brahmanda.config import TOTAL_TICKS_PER_MAHAYUGA
        return self.global_tick / TOTAL_TICKS_PER_MAHAYUGA

    def tick(self) -> dict:
        """Advance one tick. Returns transition info if yuga changed."""
        self.global_tick += 1
        self.yuga_tick += 1

        total_for_yuga = TICKS_PER_YUGA[self.current_yuga.value]

        if self.yuga_tick >= total_for_yuga:
            return self._transition_yuga()

        return {"transitioned": False, "yuga": self.current_yuga}

    def _transition_yuga(self) -> dict:
        """Move to the next yuga, or signal Mahayuga completion."""
        old_yuga = self.current_yuga
        self.yuga_index += 1

        if self.yuga_index >= len(YUGA_ORDER):
            self.mahayuga_complete = True
            return {
                "transitioned": True,
                "from": old_yuga,
                "to": None,
                "pralaya": True,
            }

        self.current_yuga = YUGA_ORDER[self.yuga_index]
        self.yuga_tick = 0

        return {
            "transitioned": True,
            "from": old_yuga,
            "to": self.current_yuga,
            "pralaya": False,
        }
