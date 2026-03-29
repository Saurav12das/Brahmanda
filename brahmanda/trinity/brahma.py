"""Brahma — The Creator, The Developer who writes the source code.

Brahma generates the initial conditions of the universe:
souls with unique personalities, desires, and starting karma.
He also periodically introduces new souls when population drops.
"""

from __future__ import annotations

import json
import random
import re

import anthropic

from brahmanda.config import DEFAULT_LOKA, INITIAL_SOUL_COUNT, TRINITY_MODEL, LokaID
from brahmanda.db.models import Event, SoulState, _uid
from brahmanda.engine.maya import Maya


BRAHMA_SYSTEM = """\
You are Brahma, the Creator of the universe Brahmanda.
You are generating souls — conscious beings who will live, choose, and die in this simulation.
Each soul must feel distinct and real. Give them:
- A Sanskrit-inspired name
- 2-3 desires that will drive their behavior (e.g., "seek knowledge", "accumulate power", "find love", "transcend suffering")
- 1-2 skills (e.g., "persuasion", "crafting", "meditation", "combat", "healing")
- A starting karma between -20 and 20 (most near 0, a few outliers)

Respond with ONLY a JSON array. No other text.
[
  {"name": "...", "desires": ["..."], "skills": ["..."], "karma": 0},
  ...
]
"""


async def create_initial_souls(
    client: anthropic.AsyncAnthropic,
    count: int = INITIAL_SOUL_COUNT,
) -> list[SoulState]:
    """Ask Brahma to generate the initial population."""
    try:
        response = await client.messages.create(
            model=TRINITY_MODEL,
            max_tokens=2000,
            system=BRAHMA_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Create {count} unique souls for the beginning of this universe. "
                           f"Make them diverse — some virtuous, some ambitious, some dark, some curious. "
                           f"They should feel like real people with conflicting motivations.",
            }],
        )
        raw = response.content[0].text
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            soul_data = json.loads(match.group())
        else:
            raise ValueError("No JSON array found")

        souls = []
        for sd in soul_data[:count]:
            soul = SoulState(
                id=_uid(),
                name=sd.get("name", f"Soul-{_uid()[:4]}"),
                karma=max(-20, min(20, sd.get("karma", 0))),
                desires=sd.get("desires", ["survive"]),
                skills=sd.get("skills", []),
                loka=DEFAULT_LOKA,
                resources=10,
            )
            souls.append(soul)
        return souls

    except Exception:
        # Fallback: generate deterministic souls
        return _fallback_souls(count)


async def spawn_new_soul(
    client: anthropic.AsyncAnthropic,
    maya: Maya,
) -> SoulState | None:
    """Brahma creates a single new soul mid-simulation."""
    try:
        existing_names = [s.name for s in maya.souls.values()]
        response = await client.messages.create(
            model=TRINITY_MODEL,
            max_tokens=400,
            system=BRAHMA_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Create 1 new soul. The following names are already taken: {existing_names}. "
                           f"Current epoch: {maya.yuga.value}. Make this soul fit the era.",
            }],
        )
        raw = response.content[0].text
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

    souls = []
    for i in range(count):
        souls.append(SoulState(
            id=_uid(),
            name=names[i % len(names)],
            karma=random.randint(-15, 15),
            desires=random.sample(desire_pool, k=random.randint(2, 3)),
            skills=random.sample(skill_pool, k=random.randint(1, 2)),
            loka=DEFAULT_LOKA,
            resources=10,
        ))
    return souls
