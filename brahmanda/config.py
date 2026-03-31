"""Universe constants and configuration — the fundamental laws of Brahmanda."""

from __future__ import annotations

import os
from enum import Enum, IntEnum


# ---------------------------------------------------------------------------
# API / LLM Backend
# ---------------------------------------------------------------------------
LLM_BACKEND: str = os.environ.get("BRAHMANDA_BACKEND", "ollama")

ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_SOUL_MODEL: str = "claude-haiku-4-5-20251001"
CLAUDE_TRINITY_MODEL: str = "claude-haiku-4-5-20251001"

OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_SOUL_MODEL: str = os.environ.get("OLLAMA_SOUL_MODEL", "qwen2.5:14b")
OLLAMA_TRINITY_MODEL: str = os.environ.get("OLLAMA_TRINITY_MODEL", "qwen2.5:14b")

SOUL_MODEL: str = OLLAMA_SOUL_MODEL if LLM_BACKEND == "ollama" else CLAUDE_SOUL_MODEL
TRINITY_MODEL: str = OLLAMA_TRINITY_MODEL if LLM_BACKEND == "ollama" else CLAUDE_TRINITY_MODEL
MAX_CONCURRENT_SOULS: int = 3 if LLM_BACKEND == "ollama" else 10

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
TICKS_PER_YUGA: dict[str, int] = {
    "satya": 40,
    "treta": 30,
    "dvapara": 20,
    "kali": 10,
}
TOTAL_TICKS_PER_MAHAYUGA: int = sum(TICKS_PER_YUGA.values())

INITIAL_SOUL_COUNT: int = 12
SOUL_MEMORY_SIZE: int = 10

# ---------------------------------------------------------------------------
# Prana (Life Force) — the core survival mechanic
# ---------------------------------------------------------------------------
PRANA_MAX: float = 100.0
PRANA_BASE_DRAIN: float = 1.0                # base prana cost per tick
PRANA_VICE_DRAIN_FACTOR: float = 1.5         # total_darkness * this = extra drain
PRANA_ENTROPY_DRAIN_FACTOR: float = 1.0      # loka_entropy * this = extra drain
PRANA_AGE_DRAIN_ONSET: int = 80              # age at which aging adds drain
PRANA_AGE_DRAIN_RATE: float = 0.02           # per-tick drain increase past onset
PRANA_REPLENISH_RATE: float = 5.0            # max prana replenished per tick
PRANA_RESOURCE_CONVERSION: float = 2.0       # prana gained per 1 loka resource

# ---------------------------------------------------------------------------
# Yugas
# ---------------------------------------------------------------------------
class YugaType(str, Enum):
    SATYA = "satya"
    TRETA = "treta"
    DVAPARA = "dvapara"
    KALI = "kali"


YUGA_ORDER: list[YugaType] = [
    YugaType.SATYA,
    YugaType.TRETA,
    YugaType.DVAPARA,
    YugaType.KALI,
]

YUGA_PARAMS: dict[YugaType, dict] = {
    YugaType.SATYA: {
        "resource_multiplier": 2.0,
        "karma_multiplier": 1.5,
        "truth_visibility": 1.0,
        "asura_spawn_rate": 0.05,
        "entropy_rate": 0.01,
        "cooperation_bias": 0.8,
    },
    YugaType.TRETA: {
        "resource_multiplier": 1.5,
        "karma_multiplier": 1.2,
        "truth_visibility": 0.75,
        "asura_spawn_rate": 0.10,
        "entropy_rate": 0.03,
        "cooperation_bias": 0.6,
    },
    YugaType.DVAPARA: {
        "resource_multiplier": 1.0,
        "karma_multiplier": 1.0,
        "truth_visibility": 0.50,
        "asura_spawn_rate": 0.20,
        "entropy_rate": 0.06,
        "cooperation_bias": 0.4,
    },
    YugaType.KALI: {
        "resource_multiplier": 0.5,
        "karma_multiplier": 0.8,
        "truth_visibility": 0.25,
        "asura_spawn_rate": 0.35,
        "entropy_rate": 0.10,
        "cooperation_bias": 0.2,
    },
}

# ---------------------------------------------------------------------------
# Lokas — no max_population caps, carrying capacity is resource-driven
# ---------------------------------------------------------------------------
class LokaID(IntEnum):
    PATALA = 1
    BHU = 7
    SVARGA = 8


LOKA_CONFIG: dict[LokaID, dict] = {
    LokaID.PATALA: {
        "name": "Patala",
        "description": "Subterranean realm — technologically advanced, dharma-poor",
        "time_multiplier": 0.5,
        "base_resources": 200,
        "karma_threshold": (-200, 0),
        "physics": "high_tech_low_dharma",
    },
    LokaID.BHU: {
        "name": "Bhu-loka",
        "description": "The physical world — where most souls incarnate",
        "time_multiplier": 1.0,
        "base_resources": 100,
        "karma_threshold": (-50, 50),
        "physics": "standard",
    },
    LokaID.SVARGA: {
        "name": "Svarga-loka",
        "description": "Celestial realm — subtle matter, higher frequencies",
        "time_multiplier": 2.0,
        "base_resources": 300,
        "karma_threshold": (50, 200),
        "physics": "subtle_matter",
    },
}

ACTIVE_LOKAS: list[LokaID] = [LokaID.PATALA, LokaID.BHU, LokaID.SVARGA]
DEFAULT_LOKA: LokaID = LokaID.BHU

# ---------------------------------------------------------------------------
# Karma
# ---------------------------------------------------------------------------
KARMA_ACTIONS: dict[str, int] = {
    "cooperate": 3,
    "trade": 1,
    "create": 2,
    "meditate": 3,
    "share": 3,
    "teach": 2,
    "fight_justified": -2,
    "fight_unjustified": -12,
    "deceive": -15,
    "steal": -10,
    "hoard": -5,
    "destroy": -8,
    "neutral": 0,
}

KARMA_DECAY_BASE_RATE: float = 0.02  # baseline, scaled by entropy/yuga/vices

SAMSARA_KARMA_RANGES: dict[LokaID, tuple[int, int]] = {
    LokaID.PATALA: (-200, -20),
    LokaID.BHU: (-20, 60),
    LokaID.SVARGA: (60, 200),
}

# ---------------------------------------------------------------------------
# Actions available to soul agents
# ---------------------------------------------------------------------------
SOUL_ACTIONS: list[str] = [
    "cooperate", "trade", "create", "meditate", "share", "teach",
    "fight", "deceive", "steal", "hoard", "explore", "neutral",
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_PATH: str = os.environ.get("BRAHMANDA_DB", "brahmanda.db")
