"""Universe constants and configuration — the fundamental laws of Brahmanda."""

from __future__ import annotations

import os
from enum import Enum, IntEnum


# ---------------------------------------------------------------------------
# API / LLM Backend
# ---------------------------------------------------------------------------
# Backend: "claude" or "ollama"
LLM_BACKEND: str = os.environ.get("BRAHMANDA_BACKEND", "ollama")

# Claude settings
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_SOUL_MODEL: str = "claude-haiku-4-5-20251001"
CLAUDE_TRINITY_MODEL: str = "claude-haiku-4-5-20251001"

# Ollama settings
OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_SOUL_MODEL: str = os.environ.get("OLLAMA_SOUL_MODEL", "qwen2.5:14b")
OLLAMA_TRINITY_MODEL: str = os.environ.get("OLLAMA_TRINITY_MODEL", "qwen2.5:14b")

# Active model selection (resolved at import time)
SOUL_MODEL: str = OLLAMA_SOUL_MODEL if LLM_BACKEND == "ollama" else CLAUDE_SOUL_MODEL
TRINITY_MODEL: str = OLLAMA_TRINITY_MODEL if LLM_BACKEND == "ollama" else CLAUDE_TRINITY_MODEL
MAX_CONCURRENT_SOULS: int = 3 if LLM_BACKEND == "ollama" else 10  # local models need lower concurrency

# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
TICKS_PER_YUGA: dict[str, int] = {
    "satya": 400,
    "treta": 300,
    "dvapara": 200,
    "kali": 100,
}
TOTAL_TICKS_PER_MAHAYUGA: int = sum(TICKS_PER_YUGA.values())  # 100

INITIAL_SOUL_COUNT: int = 12
MAX_SOUL_COUNT: int = 20              # hard cap — prevents avatar flood
SOUL_MEMORY_SIZE: int = 10            # last N events a soul remembers
VISHNU_CHECK_INTERVAL: int = 50       # ticks between Vishnu health checks (was 5)
AVATAR_DEPLOY_THRESHOLD: float = 0.85 # entropy ratio that triggers avatar (was 0.7)
MAX_AVATARS_PER_YUGA: int = 2         # Vishnu can only deploy 2 avatars per yuga

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
        "truth_visibility": 1.0,    # souls can perceive full truth
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
# Lokas
# ---------------------------------------------------------------------------
class LokaID(IntEnum):
    """14 Lokas numbered bottom (1) to top (14). We activate 3 for v1."""
    PATALA = 1
    # ATALA = 2, VITALA = 3, SUTALA = 4, TALATALA = 5, MAHATALA = 6  (future)
    BHU = 7
    SVARGA = 8
    # MAHAR = 9, JANA = 10, TAPA = 11, SATYA_LOKA = 12, VAIKUNTHA = 13, BRAHMA_LOKA = 14  (future)


LOKA_CONFIG: dict[LokaID, dict] = {
    LokaID.PATALA: {
        "name": "Patala",
        "description": "Subterranean realm — technologically advanced, dharma-poor",
        "time_multiplier": 0.5,     # time moves slower (fewer ticks processed)
        "base_resources": 200,
        "max_population": 15,
        "karma_threshold": (-100, 0),  # negative karma range to enter
        "physics": "high_tech_low_dharma",
    },
    LokaID.BHU: {
        "name": "Bhu-loka",
        "description": "The physical world — where most souls incarnate",
        "time_multiplier": 1.0,     # baseline
        "base_resources": 100,
        "max_population": 30,
        "karma_threshold": (-50, 50),
        "physics": "standard",
    },
    LokaID.SVARGA: {
        "name": "Svarga-loka",
        "description": "Celestial realm — subtle matter, higher frequencies",
        "time_multiplier": 2.0,     # 1 tick here = 2 ticks in Bhu
        "base_resources": 300,
        "max_population": 10,
        "karma_threshold": (50, 100),
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

# Karma naturally decays toward 0 each tick (nothing is permanent)
KARMA_DECAY_RATE: float = 0.02  # lose 2% of karma per tick

SAMSARA_KARMA_RANGES: dict[LokaID, tuple[int, int]] = {
    LokaID.PATALA: (-200, -20),
    LokaID.BHU: (-20, 60),
    LokaID.SVARGA: (60, 200),
}

# ---------------------------------------------------------------------------
# Actions available to soul agents
# ---------------------------------------------------------------------------
SOUL_ACTIONS: list[str] = [
    "cooperate",   # work with nearby soul
    "trade",       # exchange resources
    "create",      # build something
    "meditate",    # increase perception, gain karma
    "share",       # give resources to another
    "teach",       # transfer knowledge
    "fight",       # conflict with another soul
    "deceive",     # manipulate another soul
    "steal",       # take resources
    "hoard",       # accumulate resources selfishly
    "explore",     # move to adjacent area
    "neutral",     # observe, do nothing
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DB_PATH: str = os.environ.get("BRAHMANDA_DB", "brahmanda.db")
