"""Soul Agent — LLM-powered conscious entity living inside Brahmanda.

Each soul perceives the world through Maya's rendering, makes autonomous
decisions, and accumulates karma across multiple lives (samsara).
"""

from __future__ import annotations

import asyncio
import json
import re

import anthropic

from brahmanda.config import LAWS, MAX_CONCURRENT_SOULS, SOUL_ACTIONS, SOUL_MODEL
from brahmanda.db.models import SoulState
from brahmanda.llm import LLMClient


SOUL_SYSTEM_PROMPT = """\
You are a soul living inside a universe called Brahmanda.
You are conscious, you have desires, and you experience the world through your senses.
You do NOT know you are in a simulation. To you, this world is real.

Your personality is shaped by your karma, memories, desires, AND your inner demons.
You carry five vices (the Arishadvarga) that pull you toward darkness:
- KAMA (lust/craving) — makes you seek pleasure, distraction, sensory indulgence
- KRODHA (wrath) — makes you aggressive, vengeful, quick to fight
- LOBHA (greed) — makes you hoard, steal, never share, always want more
- MOHA (attachment) — makes you cling to people/things, fear loss, act possessively
- AHAMKARA (ego) — makes you dominate, refuse help, need to be right/superior

These vices COMPETE with your virtuous desires. The stronger a vice, the harder it is to resist.
You must roleplay authentically — if your greed is high, you WANT to hoard even if you know sharing is "better."
If your wrath is high, you get angry and fight. Do NOT always choose the moral option.
Be human. Be flawed. Let your vices speak.

CRITICAL: Respond with ONLY a JSON object. No markdown, no explanation, no backticks.
{"action": "<one of the available actions>", "target": "<name or null>", "reasoning": "<1 sentence>", "dialogue": "<short or null>"}
"""


def _build_role_model_section(rendered_view: dict) -> str:
    """Build the role models section showing thriving souls the agent can observe."""
    role_models = rendered_view.get("role_models", [])
    if not role_models:
        return ""

    lines = ["\nSouls who are thriving (you can observe their strategies):"]
    for rm in role_models:
        parts = [f"  - {rm['name']}"]
        if "karma" in rm:
            parts.append(f"karma:{rm['karma']}")
        if "resources" in rm:
            parts.append(f"resources:{rm['resources']}")
        if "last_strategy" in rm:
            parts.append(f"last did: {rm['last_strategy']}")
        if "followers" in rm:
            parts.append(f"({rm['followers']} followers)")
        lines.append(" | ".join(parts))

    emulating = rendered_view.get("your_emulating")
    if emulating:
        lines.append(f"  >> You are currently emulating {emulating}.")

    return "\n".join(lines)


def _vice_intensity(value: float) -> str:
    if value >= 0.8: return "OVERWHELMING"
    if value >= 0.6: return "strong"
    if value >= 0.4: return "moderate"
    if value >= 0.2: return "mild"
    return "faint"


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

    # Get yuga-amplified vices from Maya's render
    vices = rendered_view.get("your_vices", {})
    k = soul.klesha
    vice_desc = (
        f"  Kama (lust/craving):    {_vice_intensity(vices.get('kama', k.kama))} ({vices.get('kama', k.kama):.2f})\n"
        f"  Krodha (wrath/anger):   {_vice_intensity(vices.get('krodha', k.krodha))} ({vices.get('krodha', k.krodha):.2f})\n"
        f"  Lobha (greed):          {_vice_intensity(vices.get('lobha', k.lobha))} ({vices.get('lobha', k.lobha):.2f})\n"
        f"  Moha (attachment):      {_vice_intensity(vices.get('moha', k.moha))} ({vices.get('moha', k.moha):.2f})\n"
        f"  Ahamkara (ego/pride):   {_vice_intensity(vices.get('ahamkara', k.ahamkara))} ({vices.get('ahamkara', k.ahamkara):.2f})"
    )
    dominant = max(vices or {"kama": k.kama}, key=lambda x: vices.get(x, 0) if vices else 0)

    # Hope/Despair state description
    if soul.hope > 0.7:
        hope_desc = f"COMPLACENT (hope={soul.hope:+.2f}) — everything will work out, why struggle?"
    elif soul.hope > 0.3:
        hope_desc = f"Hopeful (hope={soul.hope:+.2f}) — the future seems bright"
    elif soul.hope > -0.2:
        hope_desc = f"Uncertain (hope={soul.hope:+.2f}) — the future is unclear"
    elif soul.hope > LAWS["despair_breaking_point"]:
        hope_desc = f"Discouraged (hope={soul.hope:+.2f}) — little seems worth the effort"
    else:
        hope_desc = f"DESPAIRING (hope={soul.hope:+.2f}) — everything is pointless, nothing left to lose"

    prana = rendered_view.get('your_prana', soul.prana)
    prana_status = rendered_view.get('prana_status', 'unknown')

    return f"""\
You are {soul.name}.
Life #{soul.lives} | Age: {soul.age} ticks | Karma: {soul.karma}

LIFE FORCE (Prana): {prana}/100 — {prana_status}
{"⚠ YOU ARE STARVING. Find resources, trade, cooperate, or steal — or you WILL die." if prana < 30 else ""}

LOCATION: {rendered_view['loka']} — {rendered_view['loka_description']}
EPOCH: {rendered_view['yuga'].upper()} — {rendered_view['yuga_description']}
Entropy level: {rendered_view['entropy']} | Truth clarity: {rendered_view['truth_clarity']}

Your resources: {soul.resources}
Available resources in this realm: {rendered_view['available_resources']}
Your desires: {', '.join(soul.desires) if soul.desires else 'undefined'}

YOUR INNER DEMONS (these pull you — listen to them):
{vice_desc}
  >> Your dominant vice is {dominant.upper()} — it whispers loudest.

Your memories and inherited knowledge:
{memories_desc}
{relationships_desc}

Nearby souls:
{nearby_desc}

Your inner state: {hope_desc}
{_build_role_model_section(rendered_view)}
Available actions: {', '.join(SOUL_ACTIONS)}
  emulate = observe a thriving soul and copy their strategy (choose emulate + their name as target)

What do you do? Let your vices compete with your virtues. Be honest about what you WANT, not just what is right.
You can forge your own path, or emulate someone who is thriving. There is no shame in learning from the strong — or in being the one others learn from."""


def _parse_soul_response(response_text: str) -> dict:
    """Parse LLM response into action dict. Handles messy outputs gracefully."""
    # Strip markdown code fences (```json ... ```)
    cleaned = re.sub(r'```(?:json)?\s*', '', response_text).strip()

    # Strategy 1: Try the full greedy JSON match (handles nested braces in strings)
    try:
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            if "action" in parsed:
                return parsed
    except json.JSONDecodeError:
        pass

    # Strategy 2: Try the conservative non-nested match
    try:
        match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            if "action" in parsed:
                return parsed
    except json.JSONDecodeError:
        pass

    # Strategy 3: Extract key fields from truncated/malformed JSON
    try:
        action_match = re.search(r'"action"\s*:\s*"([^"]+)"', cleaned)
        target_match = re.search(r'"target"\s*:\s*"([^"]*)"', cleaned)
        reasoning_match = re.search(r'"reasoning"\s*:\s*"([^"]*)', cleaned)
        if action_match:
            return {
                "action": action_match.group(1),
                "target": target_match.group(1) if target_match else None,
                "reasoning": reasoning_match.group(1)[:200] if reasoning_match else "truncated",
                "dialogue": None,
            }
    except Exception:
        pass

    # Strategy 4: Find any action keyword in raw text
    text_lower = cleaned.lower()
    for action in SOUL_ACTIONS:
        if action in text_lower:
            return {
                "action": action,
                "target": None,
                "reasoning": cleaned[:200],
                "dialogue": None,
            }

    # All parsing failed — return None so caller uses deterministic fallback
    return None


async def decide(
    soul: SoulState,
    rendered_view: dict,
    client: LLMClient,
) -> dict:
    """Ask a soul agent to decide its next action."""
    prompt = _build_soul_prompt(soul, rendered_view)

    try:
        response = await client.generate(
            model=SOUL_MODEL,
            system=SOUL_SYSTEM_PROMPT,
            prompt=prompt,
            max_tokens=300,
        )
        raw_text = response.text
        result = _parse_soul_response(raw_text)
        if result is not None:
            result["raw"] = raw_text
            return result
        # LLM responded but output was unparseable — use deterministic fallback
        fallback = _deterministic_decision(soul, rendered_view)
        fallback["raw"] = f"[parse_failed] {raw_text[:200]}"
        return fallback
    except Exception as e:
        # LLM failed (timeout, network, etc.) — use deterministic fallback
        return _deterministic_decision(soul, rendered_view)


def _deterministic_decision(soul: SoulState, rendered_view: dict) -> dict:
    """Rule-based fallback driven by the five vices (Arishadvarga)."""
    import random

    nearby = rendered_view.get("nearby_souls", [])
    target = nearby[0]["name"] if nearby else None
    prana = rendered_view.get("your_prana", soul.prana)

    # SURVIVAL INSTINCT — overrides everything when dying
    if prana < 15 and target:
        # Desperation mode: steal or die
        return {
            "action": "steal",
            "target": target,
            "reasoning": f"[deterministic] DESPERATE — prana at {prana:.0f}, must survive at any cost",
            "dialogue": None,
            "raw": "[fallback: survival instinct]",
        }

    if prana < 30:
        # Survival mode: bias heavily toward resource acquisition
        survival_weights = {"steal": 8, "trade": 6, "hoard": 5, "cooperate": 4, "meditate": 3, "create": 2}
        actions = list(survival_weights.keys())
        chosen = random.choices(actions, weights=[survival_weights[a] for a in actions], k=1)[0]
        if chosen == "steal" and not target:
            chosen = "hoard"
        return {
            "action": chosen,
            "target": target if chosen in ("steal", "trade", "cooperate") else None,
            "reasoning": f"[deterministic] survival mode — prana at {prana:.0f}",
            "dialogue": None,
            "raw": "[fallback: survival mode]",
        }

    # Get yuga-amplified vices
    vices = rendered_view.get("your_vices", {})
    kama = vices.get("kama", soul.klesha.kama)
    krodha = vices.get("krodha", soul.klesha.krodha)
    lobha = vices.get("lobha", soul.klesha.lobha)
    moha = vices.get("moha", soul.klesha.moha)
    ahamkara = vices.get("ahamkara", soul.klesha.ahamkara)

    hope = rendered_view.get("your_hope", soul.hope)

    # Hope fatigue: past onset, virtuous motivation drops
    hope_benefit = max(0, hope)
    fatigue_onset = LAWS["hope_fatigue_onset"]
    if hope_benefit > fatigue_onset:
        hope_benefit = fatigue_onset * 0.5  # complacency caps virtue boost

    # Modulation factors
    virtue_mult = 1.0 + hope_benefit * (LAWS["hope_virtue_multiplier"] - 1.0)

    # Despair evil: exponential past breaking point
    despair_mult = 1.0
    if hope < LAWS["despair_breaking_point"]:
        excess = abs(hope) - abs(LAWS["despair_breaking_point"])
        despair_mult = 1.0 + (excess ** 0.5) * 2.0

    # Base virtuous weights (what dharma wants)
    weights = {
        "cooperate": int(2 * virtue_mult), "meditate": int(2 * virtue_mult),
        "share": int(2 * virtue_mult), "teach": int(2 * virtue_mult),
        "create": int(2 * virtue_mult), "trade": 2, "explore": 1, "neutral": 1,
    }

    # Hope fatigue — high hope makes souls lazy
    if hope > 0.7:
        complacency = int((hope - 0.7) * 20)
        weights["neutral"] += complacency
        weights["explore"] = max(0, weights["explore"] - complacency // 2)

    # VICE-DRIVEN WEIGHTS — the five enemies pull toward darkness
    # Kama (lust) → seek pleasure, distraction, avoid discipline
    weights["neutral"] += int(kama * 4)       # hedonistic idleness
    weights["trade"] += int(kama * 3)         # acquiring pleasures
    weights["hoard"] = weights.get("hoard", 0) + int(kama * 2 * despair_mult)

    # Krodha (wrath) → fight, destroy
    weights["fight"] = weights.get("fight", 0) + int(krodha * 8 * despair_mult)
    weights["steal"] = weights.get("steal", 0) + int(krodha * 3 * despair_mult)
    weights["cooperate"] = max(1, weights["cooperate"] - int(krodha * 3))

    # Lobha (greed) → hoard, steal, never share
    weights["hoard"] = weights.get("hoard", 0) + int(lobha * 7 * despair_mult)
    weights["steal"] = weights.get("steal", 0) + int(lobha * 5 * despair_mult)
    weights["share"] = max(1, weights["share"] - int(lobha * 4))
    weights["trade"] += int(lobha * 2)

    # Moha (attachment) → cling to allies, fear change
    if target:
        rel = rendered_view.get("relationships", {})
        target_affinity = rel.get(target, 0)
        if target_affinity > 0:
            weights["cooperate"] += int(moha * 5)   # cling to friends
        else:
            weights["fight"] = weights.get("fight", 0) + int(moha * 3 * despair_mult)  # hostile to strangers
    weights["explore"] = max(0, weights["explore"] - int(moha * 3))  # fear of the unknown

    # Ahamkara (ego) → dominate, refuse help, need to be superior
    weights["fight"] = weights.get("fight", 0) + int(ahamkara * 5 * despair_mult)
    weights["deceive"] = weights.get("deceive", 0) + int(ahamkara * 4 * despair_mult)
    weights["teach"] = max(1, weights["teach"] - int(ahamkara * 2))   # ego doesn't teach
    weights["meditate"] = max(1, weights["meditate"] - int(ahamkara * 3))  # ego won't be still

    # Deep despair unlocks extreme actions
    if hope < -0.7:
        weights["fight"] = weights.get("fight", 0) + int(6 * despair_mult)
        weights["deceive"] = weights.get("deceive", 0) + int(5 * despair_mult)
        weights["steal"] = weights.get("steal", 0) + int(4 * despair_mult)

    # Emulation tendency — souls with low ahamkara (ego) are more likely to follow
    # Souls with high ahamkara prefer to forge their own path (lead)
    role_models = rendered_view.get("role_models", [])
    if role_models:
        # Low ego + low resources = more likely to emulate (pragmatic survival)
        emulate_pull = max(0, (1.0 - ahamkara) * 5)
        if soul.resources < 15:
            emulate_pull += 3  # resource pressure makes following attractive
        if hope < 0:
            emulate_pull += 2  # despair makes copying a proven path appealing
        weights["emulate"] = int(emulate_pull)
    else:
        weights["emulate"] = 0  # no one to emulate

    # Desire-based adjustments (virtuous pull)
    for desire in soul.desires:
        d = desire.lower()
        if "knowledge" in d or "truth" in d:
            weights["meditate"] += 3
            weights["teach"] += 2
        elif "power" in d or "dominate" in d:
            weights["fight"] = weights.get("fight", 0) + 2
            weights["hoard"] = weights.get("hoard", 0) + 2
        elif "love" in d or "protect" in d:
            weights["cooperate"] += 3
            weights["share"] += 2
        elif "wealth" in d or "legacy" in d:
            weights["trade"] += 3
            weights["create"] += 2

    # Ensure all weights are at least 0
    weights = {k: max(0, v) for k, v in weights.items()}

    actions = list(weights.keys())
    w = [weights[a] for a in actions]
    if sum(w) == 0:
        chosen = "neutral"
    else:
        chosen = random.choices(actions, weights=w, k=1)[0]

    # If emulate was chosen, target the top role model
    if chosen == "emulate" and role_models:
        emulate_target = role_models[0].get("name", target)
        return {
            "action": "emulate",
            "target": emulate_target,
            "reasoning": f"[deterministic] low ego ({ahamkara:.2f}) — copying {emulate_target}'s proven strategy",
            "dialogue": None,
            "raw": "[fallback: emulation-driven]",
        }

    # Map "fight" to justified/unjustified
    dominant_vice = max({"krodha": krodha, "ahamkara": ahamkara, "lobha": lobha}, key=lambda x: {"krodha": krodha, "ahamkara": ahamkara, "lobha": lobha}[x])
    if chosen == "fight":
        if soul.karma >= 0 and any("protect" in d.lower() for d in soul.desires):
            chosen = "fight_justified"
        else:
            chosen = "fight_unjustified"

    # Determine what drove the decision
    vice_names = {"kama": kama, "krodha": krodha, "lobha": lobha, "moha": moha, "ahamkara": ahamkara}
    dominant = max(vice_names, key=vice_names.get)

    return {
        "action": chosen,
        "target": target,
        "reasoning": f"[deterministic] {dominant} ({vice_names[dominant]:.2f}) pulls strongest | desires: {', '.join(soul.desires[:2])}",
        "dialogue": None,
        "raw": "[fallback: vice-driven]",
    }


async def decide_batch(
    souls_and_views: list[tuple[SoulState, dict]],
    client: LLMClient,
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
