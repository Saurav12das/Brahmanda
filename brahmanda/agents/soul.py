"""Soul Agent — LLM-powered conscious entity living inside Brahmanda.

Each soul perceives the world through Maya's rendering, makes autonomous
decisions, and accumulates karma across multiple lives (samsara).
"""

from __future__ import annotations

import asyncio
import json
import re

import anthropic

from brahmanda.config import MAX_CONCURRENT_SOULS, SOUL_ACTIONS, SOUL_MODEL
from brahmanda.db.models import SoulState


SOUL_SYSTEM_PROMPT = """\
You are a soul living inside a simulated universe called Brahmanda.
You are conscious, you have desires, and you experience the world through your senses.
You do NOT know you are in a simulation. To you, this world is real.

Your personality and tendencies are shaped by your karma, memories, and desires.
Make decisions that feel authentic to who you are — not what is "optimal."
You may be selfish, altruistic, curious, fearful, ambitious, or spiritual.
Your choices have real consequences in this world.

IMPORTANT: Respond with ONLY a valid JSON object. No other text.
{
  "action": "<one of the available actions>",
  "target": "<name of another soul, or null if no target>",
  "reasoning": "<brief inner thought — why you chose this>",
  "dialogue": "<what you say out loud, or null if silent>"
}
"""


def _build_soul_prompt(soul: SoulState, rendered_view: dict) -> str:
    nearby = rendered_view.get("nearby_souls", [])
    nearby_desc = "\n".join(
        f"  - {s['name']}" + (f" (karma: {s.get('karma_hint', '?')})" if 'karma_hint' in s else "")
        for s in nearby
    ) if nearby else "  No one is nearby."

    relationships_desc = ""
    if rendered_view.get("relationships"):
        relationships_desc = "\nYour relationships:\n" + "\n".join(
            f"  - {name}: {'friendly' if v > 0 else 'hostile' if v < 0 else 'neutral'} ({v:+d})"
            for name, v in rendered_view["relationships"].items()
        )

    memories_desc = "\n".join(f"  - {m}" for m in rendered_view.get("your_memories", [])) or "  No memories yet."

    return f"""\
You are {soul.name}.
Life #{soul.lives} | Age: {soul.age} ticks | Karma: {soul.karma}

LOCATION: {rendered_view['loka']} — {rendered_view['loka_description']}
EPOCH: {rendered_view['yuga'].upper()} — {rendered_view['yuga_description']}
Entropy level: {rendered_view['entropy']} | Truth clarity: {rendered_view['truth_clarity']}

Your resources: {soul.resources}
Available resources in this realm: {rendered_view['available_resources']}
Your desires: {', '.join(soul.desires) if soul.desires else 'undefined'}

Your memories:
{memories_desc}
{relationships_desc}

Nearby souls:
{nearby_desc}

Available actions: {', '.join(SOUL_ACTIONS)}

What do you do?"""


def _parse_soul_response(response_text: str) -> dict:
    """Parse LLM response into action dict. Handles messy outputs gracefully."""
    # Try to extract JSON from the response
    try:
        # Look for JSON block
        match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    # Fallback: try to extract action keyword
    text_lower = response_text.lower()
    for action in SOUL_ACTIONS:
        if action in text_lower:
            return {
                "action": action,
                "target": None,
                "reasoning": response_text[:200],
                "dialogue": None,
            }

    return {
        "action": "neutral",
        "target": None,
        "reasoning": "Could not decide.",
        "dialogue": None,
    }


FALLBACK_MODELS: list[str] = [
    "claude-haiku-4-5-20251001",
    "claude-3-haiku-20240307",
]


async def decide(
    soul: SoulState,
    rendered_view: dict,
    client: anthropic.AsyncAnthropic,
) -> dict:
    """Ask a soul agent to decide its next action."""
    prompt = _build_soul_prompt(soul, rendered_view)

    # Try primary model, then fallbacks
    models_to_try = [SOUL_MODEL] + [m for m in FALLBACK_MODELS if m != SOUL_MODEL]
    last_error = None

    for model in models_to_try:
        try:
            response = await client.messages.create(
                model=model,
                max_tokens=300,
                system=SOUL_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_text = response.content[0].text
            result = _parse_soul_response(raw_text)
            result["raw"] = raw_text
            return result
        except anthropic.BadRequestError as e:
            last_error = e
            continue
        except anthropic.AuthenticationError as e:
            # No point retrying with different model — key is bad
            last_error = e
            break
        except Exception as e:
            last_error = e
            continue

    # All models failed — use deterministic fallback
    return _deterministic_decision(soul, rendered_view)


def _deterministic_decision(soul: SoulState, rendered_view: dict) -> dict:
    """Rule-based fallback when LLM is unavailable."""
    import random

    nearby = rendered_view.get("nearby_souls", [])
    target = nearby[0]["name"] if nearby else None

    # Personality-driven action selection based on desires and karma
    if soul.karma > 20:
        weights = {"cooperate": 4, "meditate": 3, "share": 3, "teach": 2, "create": 2, "trade": 1}
    elif soul.karma < -20:
        weights = {"deceive": 3, "steal": 3, "fight": 2, "hoard": 3, "trade": 1, "neutral": 1}
    else:
        weights = {"cooperate": 2, "trade": 2, "create": 2, "explore": 2, "meditate": 1, "fight": 1, "neutral": 1}

    # Desire-based adjustments
    for desire in soul.desires:
        d = desire.lower()
        if "knowledge" in d or "truth" in d:
            weights["meditate"] = weights.get("meditate", 0) + 3
            weights["teach"] = weights.get("teach", 0) + 2
        elif "power" in d or "dominate" in d:
            weights["fight"] = weights.get("fight", 0) + 3
            weights["hoard"] = weights.get("hoard", 0) + 2
        elif "love" in d or "protect" in d:
            weights["cooperate"] = weights.get("cooperate", 0) + 3
            weights["share"] = weights.get("share", 0) + 2
        elif "wealth" in d or "legacy" in d:
            weights["trade"] = weights.get("trade", 0) + 3
            weights["create"] = weights.get("create", 0) + 2

    # Relationship-driven adjustments
    if target and nearby:
        rel = rendered_view.get("relationships", {})
        target_affinity = rel.get(target, 0)
        if target_affinity > 5:
            weights["cooperate"] = weights.get("cooperate", 0) + 3
        elif target_affinity < -5:
            weights["fight"] = weights.get("fight", 0) + 2

    actions = list(weights.keys())
    w = [weights[a] for a in actions]
    chosen = random.choices(actions, weights=w, k=1)[0]

    # Map "fight" to justified/unjustified
    if chosen == "fight":
        if soul.karma >= 0 and any("protect" in d.lower() for d in soul.desires):
            chosen = "fight_justified"
        else:
            chosen = "fight_unjustified"

    return {
        "action": chosen,
        "target": target,
        "reasoning": f"[deterministic] Driven by desires: {', '.join(soul.desires[:2])}",
        "dialogue": None,
        "raw": "[fallback: LLM unavailable]",
    }


async def decide_batch(
    souls_and_views: list[tuple[SoulState, dict]],
    client: anthropic.AsyncAnthropic,
) -> dict[str, dict]:
    """Run soul decisions in parallel, respecting concurrency limit."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_SOULS)

    async def _limited_decide(soul: SoulState, view: dict) -> tuple[str, dict]:
        async with semaphore:
            result = await decide(soul, view, client)
            return soul.id, result

    tasks = [_limited_decide(soul, view) for soul, view in souls_and_views]
    results = await asyncio.gather(*tasks)
    return dict(results)
