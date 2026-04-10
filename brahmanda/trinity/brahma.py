"""Brahma — The Creator, The Developer who writes the source code.

Brahma generates the initial conditions of the universe:
souls with unique personalities, desires, and starting karma.
He also periodically introduces new souls when population drops.
"""

from __future__ import annotations

import json
import random
import re

from brahmanda.config import DEFAULT_LOKA, INITIAL_SOUL_COUNT, LAWS, TRINITY_MODEL, ZERO_START, LokaID
from brahmanda.db.models import Event, Klesha, SoulState, _uid
from brahmanda.engine.maya import Maya
from brahmanda.engine.potential import assign_potential
from brahmanda.llm import LLMClient


BRAHMA_SYSTEM = """\
You are Brahma, the Creator of the universe Brahmanda.
You are generating souls — conscious beings who will live, choose, and die in this simulation.
Each soul must feel distinct and real. Give them:
- A Sanskrit-inspired name
- 2-3 desires that will drive their behavior (e.g., "seek knowledge", "accumulate power", "find love", "transcend suffering")
- 1-2 skills (e.g., "persuasion", "crafting", "meditation", "combat", "healing")
- A starting karma between -20 and 20 (most near 0, a few outliers)
- The five inner vices (Arishadvarga), each a float from 0.0 to 1.0:
  - kama (lust/craving for pleasure)
  - krodha (wrath/anger/aggression)
  - lobha (greed/never enough)
  - moha (attachment/clinging/fear of loss)
  - ahamkara (ego/pride/need to dominate)
  Make these varied! Some souls should be deeply flawed. A warrior might have high krodha and ahamkara. A merchant high lobha. A lover high kama and moha. No soul should have all vices below 0.3.

Respond with ONLY a JSON array. No other text.
[
  {"name": "...", "desires": ["..."], "skills": ["..."], "karma": 0, "klesha": {"kama": 0.5, "krodha": 0.3, "lobha": 0.7, "moha": 0.4, "ahamkara": 0.6}},
  ...
]
"""


def _zero_start_souls(count: int) -> list[SoulState]:
    """Create souls with truly identical starting conditions.

    Every soul begins at absolute zero: same vices, same karma, same hope,
    same resources, same prana, no desires beyond survival, no skills,
    no innate potential. All differentiation must emerge from their own
    choices and environmental interactions.
    """
    # Simple Sanskrit-inspired ordinal names — identity without personality
    names = [
        "Pratham", "Dvitiya", "Tritiya", "Chaturtha", "Panchama",
        "Shashtha", "Saptama", "Ashtama", "Navama", "Dashama",
        "Ekadasha", "Dvadasha", "Trayodasha", "Chaturdasha", "Panchadasha",
        "Shodasha", "Saptadasha", "Ashtadasha", "Navadasha", "Vimsha",
    ]
    souls = []
    for i in range(count):
        name = names[i % len(names)] if i < len(names) else f"Atman-{i + 1}"
        souls.append(SoulState(
            id=_uid(),
            name=name,
            karma=0,
            desires=["survive", "become the best"],
            skills=[],
            loka=DEFAULT_LOKA,
            resources=10,
            potential=0.0,       # no innate advantage
            klesha=Klesha(       # perfectly neutral vices — equal inner battlefield
                kama=0.5,
                krodha=0.5,
                lobha=0.5,
                moha=0.5,
                ahamkara=0.5,
            ),
            hope=0.0,            # neither hopeful nor despairing
        ))
    return souls


async def create_initial_souls(
    client: LLMClient,
    count: int = INITIAL_SOUL_COUNT,
) -> list[SoulState]:
    """Ask Brahma to generate the initial population.

    If ZERO_START is enabled, all souls begin with identical stats —
    differentiation emerges purely from choices and environment.
    """
    if ZERO_START:
        from rich.console import Console
        Console().print("  [bold bright_cyan]ZERO START MODE[/bold bright_cyan] — all souls begin equal. Evolution decides.")
        return _zero_start_souls(count)

    try:
        response = await client.generate(
            model=TRINITY_MODEL,
            system=BRAHMA_SYSTEM,
            prompt=f"Create {count} unique souls for the beginning of this universe. "
                   f"Make them diverse — some virtuous, some ambitious, some dark, some curious. "
                   f"They should feel like real people with conflicting motivations.",
            max_tokens=2000,
        )
        raw = response.text
        from brahmanda.llm import strip_markdown_fences
        raw = strip_markdown_fences(raw)
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            soul_data = json.loads(match.group())
        else:
            raise ValueError("No JSON array found")

        souls = []
        for sd in soul_data[:count]:
            klesha_data = sd.get("klesha", {})
            soul = SoulState(
                id=_uid(),
                name=sd.get("name", f"Soul-{_uid()[:4]}"),
                karma=max(-20, min(20, sd.get("karma", 0))),
                desires=sd.get("desires", ["survive"]),
                skills=sd.get("skills", []),
                loka=DEFAULT_LOKA,
                resources=10,
                potential=assign_potential(),
                klesha=Klesha(
                    kama=max(0.1, min(1.0, klesha_data.get("kama", random.uniform(0.2, 0.8)))),
                    krodha=max(0.1, min(1.0, klesha_data.get("krodha", random.uniform(0.2, 0.8)))),
                    lobha=max(0.1, min(1.0, klesha_data.get("lobha", random.uniform(0.2, 0.8)))),
                    moha=max(0.1, min(1.0, klesha_data.get("moha", random.uniform(0.2, 0.8)))),
                    ahamkara=max(0.1, min(1.0, klesha_data.get("ahamkara", random.uniform(0.2, 0.8)))),
                ),
                hope=random.uniform(LAWS["hope_initial_min"], LAWS["hope_initial_max"]),
            )
            souls.append(soul)
        return souls

    except Exception as e:
        from rich.console import Console
        Console().print(f"  [yellow]Brahma LLM unavailable ({type(e).__name__}), using deterministic creation[/yellow]")
        return _fallback_souls(count)


async def spawn_new_soul(
    client: LLMClient,
    maya: Maya,
) -> SoulState | None:
    """Brahma creates a single new soul mid-simulation."""
    try:
        existing_names = [s.name for s in maya.souls.values()]
        response = await client.generate(
            model=TRINITY_MODEL,
            system=BRAHMA_SYSTEM,
            prompt=f"Create 1 new soul. The following names are already taken: {existing_names}. "
                   f"Current epoch: {maya.yuga.value}. Make this soul fit the era.",
            max_tokens=400,
        )
        raw = response.text
        from brahmanda.llm import strip_markdown_fences
        raw = strip_markdown_fences(raw)
        match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
        if match:
            sd = json.loads(match.group())
            return SoulState(
                id=_uid(),
                name=sd.get("name", f"Soul-{_uid()[:4]}"),
                karma=max(-20, min(20, sd.get("karma", 0))),
                desires=sd.get("desires", ["survive"]),
                skills=sd.get("skills", []),
                loka=DEFAULT_LOKA,
                resources=10,
                hope=random.uniform(LAWS["hope_initial_min"], LAWS["hope_initial_max"]),
            )
    except Exception:
        pass
    return None


def _fallback_souls(count: int) -> list[SoulState]:
    """Deterministic fallback if LLM is unavailable."""
    names = [
        "Arjuna", "Draupadi", "Karna", "Shakuntala", "Vidura",
        "Satyavati", "Bhishma", "Amba", "Narada", "Savitri",
        "Ashoka", "Maitreyi", "Ravana", "Sita", "Hanuman",
        "Gargi", "Chanakya", "Damayanti", "Nachiketa", "Lopamudra",
    ]
    desire_pool = [
        "seek knowledge", "accumulate power", "find love", "protect the weak",
        "transcend suffering", "build legacy", "uncover truth", "dominate rivals",
        "achieve immortality", "serve dharma", "explore the unknown", "create beauty",
    ]
    skill_pool = [
        "persuasion", "crafting", "meditation", "combat", "healing",
        "diplomacy", "stealth", "teaching", "strategy", "oration",
    ]

    # Archetype-based klesha profiles for diverse souls
    archetypes = [
        Klesha(kama=0.8, krodha=0.2, lobha=0.3, moha=0.9, ahamkara=0.3),  # The Lover
        Klesha(kama=0.3, krodha=0.9, lobha=0.2, moha=0.4, ahamkara=0.8),  # The Warrior
        Klesha(kama=0.4, krodha=0.3, lobha=0.9, moha=0.5, ahamkara=0.6),  # The Merchant
        Klesha(kama=0.2, krodha=0.2, lobha=0.2, moha=0.2, ahamkara=0.2),  # The Sage
        Klesha(kama=0.6, krodha=0.7, lobha=0.8, moha=0.3, ahamkara=0.9),  # The Tyrant
        Klesha(kama=0.7, krodha=0.4, lobha=0.6, moha=0.8, ahamkara=0.4),  # The Hedonist
        Klesha(kama=0.3, krodha=0.8, lobha=0.4, moha=0.7, ahamkara=0.5),  # The Avenger
        Klesha(kama=0.5, krodha=0.3, lobha=0.3, moha=0.9, ahamkara=0.2),  # The Devoted
        Klesha(kama=0.4, krodha=0.5, lobha=0.7, moha=0.4, ahamkara=0.7),  # The Schemer
        Klesha(kama=0.2, krodha=0.6, lobha=0.3, moha=0.3, ahamkara=0.9),  # The Conqueror
        Klesha(kama=0.9, krodha=0.6, lobha=0.5, moha=0.7, ahamkara=0.5),  # The Tempter
        Klesha(kama=0.3, krodha=0.4, lobha=0.5, moha=0.6, ahamkara=0.3),  # The Everyman
    ]

    souls = []
    for i in range(count):
        klesha = archetypes[i % len(archetypes)]
        # Add randomness so no two runs are identical
        klesha = Klesha(
            kama=max(0.1, min(1.0, klesha.kama + random.uniform(-0.15, 0.15))),
            krodha=max(0.1, min(1.0, klesha.krodha + random.uniform(-0.15, 0.15))),
            lobha=max(0.1, min(1.0, klesha.lobha + random.uniform(-0.15, 0.15))),
            moha=max(0.1, min(1.0, klesha.moha + random.uniform(-0.15, 0.15))),
            ahamkara=max(0.1, min(1.0, klesha.ahamkara + random.uniform(-0.15, 0.15))),
        )
        souls.append(SoulState(
            id=_uid(),
            name=names[i % len(names)],
            karma=random.randint(-15, 15),
            desires=random.sample(desire_pool, k=random.randint(2, 3)),
            skills=random.sample(skill_pool, k=random.randint(1, 2)),
            loka=DEFAULT_LOKA,
            resources=10,
            potential=assign_potential(),
            klesha=klesha,
            hope=random.uniform(LAWS["hope_initial_min"], LAWS["hope_initial_max"]),
        ))
    return souls
