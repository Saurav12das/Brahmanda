"""Universe Randomizer — make every Brahmanda run unique.

Reads an optional seed from the BRAHMANDA_SEED environment variable
(or generates one from the current time) and applies controlled random
perturbations to every tunable constant in the simulation.

Call ``randomize_universe_laws(seed=None)`` once before the first tick.
"""

from __future__ import annotations

import math
import os
import random
import time
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import brahmanda.config as config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vary(value: float, pct: float) -> float:
    """Return *value* perturbed by a uniform factor in [1-pct, 1+pct]."""
    return value * random.uniform(1.0 - pct, 1.0 + pct)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def randomize_universe_laws(seed: int | None = None) -> int:
    """Randomize every tunable constant in Brahmanda and return the seed.

    Parameters
    ----------
    seed : int | None
        Explicit seed.  When *None* the function checks the
        ``BRAHMANDA_SEED`` environment variable first, then falls back
        to a time-based seed.

    Returns
    -------
    int
        The seed that was used (so it can be logged / reproduced).
    """
    # --- resolve seed ---------------------------------------------------
    if seed is None:
        env_seed = os.environ.get("BRAHMANDA_SEED")
        if env_seed is not None:
            seed = int(env_seed)
        else:
            seed = int(time.time() * 1000) & 0xFFFFFFFF
    random.seed(seed)

    # --- 1. TICKS_PER_YUGA  (+/-20%, total ~100, maintain ordering) -----
    _randomize_ticks()

    # --- 2. YUGA_PARAMS  (+/-30%, maintain ordering across yugas) -------
    _randomize_yuga_params()

    # --- 3. PRANA scalars  (+/-40%) -------------------------------------
    _randomize_prana()

    # --- 4. KARMA_ACTIONS  (+/-3, keep signs) ---------------------------
    _randomize_karma()

    # --- 5. LOKA_CONFIG base_resources  (+/-30%) ------------------------
    _randomize_loka_resources()

    # --- 6. LAWS dict  (+/-25%) -----------------------------------------
    _randomize_laws()

    # --- 7. TECH_TREE discovery_chance & effects  (+/-50% / +/-30%) -----
    _randomize_tech_tree()

    # --- 8. DISCOVERABLE_MECHANICS effects  (+/-30%) --------------------
    _randomize_discoverable_mechanics()

    # --- 9. Recalculate derived constants -------------------------------
    config.TOTAL_TICKS_PER_MAHAYUGA = sum(config.TICKS_PER_YUGA.values())

    # --- 10. Rich summary -----------------------------------------------
    _print_summary(seed)

    return seed


# ---------------------------------------------------------------------------
# Internal randomizers
# ---------------------------------------------------------------------------

def _randomize_ticks() -> None:
    """Perturb ticks +/-20%, re-scale so total stays ~100, maintain ordering."""
    raw: dict[str, float] = {}
    for yuga, ticks in config.TICKS_PER_YUGA.items():
        raw[yuga] = _vary(ticks, 0.20)

    # Maintain ordering: satya >= treta >= dvapara >= kali
    ordered_yugas = ["satya", "treta", "dvapara", "kali"]
    vals = sorted([raw[y] for y in ordered_yugas], reverse=True)

    # Re-scale so the sum is ~100
    total = sum(vals)
    scale = 100.0 / total if total > 0 else 1.0
    scaled = [max(1, round(v * scale)) for v in vals]

    # Adjust rounding error to keep sum == 100
    diff = 100 - sum(scaled)
    scaled[0] += diff  # adjust largest bucket

    for yuga, val in zip(ordered_yugas, scaled):
        config.TICKS_PER_YUGA[yuga] = val


def _randomize_yuga_params() -> None:
    """Perturb each param +/-30%, then sort across yugas to maintain ordering."""
    yuga_order = list(config.YUGA_ORDER)  # satya, treta, dvapara, kali
    param_names = list(next(iter(config.YUGA_PARAMS.values())).keys())

    # Parameters where satya should be HIGHEST
    higher_is_better = {"resource_multiplier", "karma_multiplier",
                        "truth_visibility", "cooperation_bias"}
    # Parameters where kali should be HIGHEST
    higher_is_worse = {"asura_spawn_rate", "entropy_rate"}

    for param in param_names:
        # Vary each yuga's value
        varied = []
        for yuga in yuga_order:
            original = config.YUGA_PARAMS[yuga][param]
            varied.append(_vary(original, 0.30))

        # Sort to maintain ordering
        if param in higher_is_better:
            varied.sort(reverse=True)  # satya highest -> kali lowest
        elif param in higher_is_worse:
            varied.sort()  # satya lowest -> kali highest
        else:
            varied.sort(reverse=True)  # default: satya highest

        for yuga, val in zip(yuga_order, varied):
            config.YUGA_PARAMS[yuga][param] = round(val, 4)


def _randomize_prana() -> None:
    """Perturb PRANA scalar module-level attributes +/-40%."""
    prana_attrs = [
        "PRANA_MAX", "PRANA_BASE_DRAIN", "PRANA_VICE_DRAIN_FACTOR",
        "PRANA_ENTROPY_DRAIN_FACTOR", "PRANA_AGE_DRAIN_ONSET",
        "PRANA_AGE_DRAIN_RATE", "PRANA_REPLENISH_RATE",
        "PRANA_RESOURCE_CONVERSION",
    ]
    for attr in prana_attrs:
        original = getattr(config, attr)
        new_val = _vary(float(original), 0.40)
        # Keep integer types as int where appropriate
        if isinstance(original, int):
            new_val = max(1, round(new_val))
        else:
            new_val = round(new_val, 4)
        setattr(config, attr, type(original)(new_val))


def _randomize_karma() -> None:
    """Perturb KARMA_ACTIONS by +/-3, keeping original sign (or zero)."""
    for action, base in config.KARMA_ACTIONS.items():
        if base == 0:
            continue
        delta = random.randint(-3, 3)
        new_val = base + delta
        # Preserve sign
        if base > 0:
            new_val = max(1, new_val)
        elif base < 0:
            new_val = min(-1, new_val)
        config.KARMA_ACTIONS[action] = new_val


def _randomize_loka_resources() -> None:
    """Perturb base_resources in LOKA_CONFIG +/-30%."""
    for loka_id, cfg in config.LOKA_CONFIG.items():
        original = cfg["base_resources"]
        cfg["base_resources"] = max(10, round(_vary(original, 0.30)))


def _randomize_laws() -> None:
    """Perturb every value in LAWS +/-25%."""
    for key, val in config.LAWS.items():
        config.LAWS[key] = round(_vary(val, 0.25), 6)


def _randomize_tech_tree() -> None:
    """Perturb TECH_TREE discovery_chance (+/-50%) and effects (+/-30%)."""
    try:
        from brahmanda.engine.tech_tree import TECH_TREE
    except ImportError:
        return

    for innovation in TECH_TREE:
        innovation.discovery_chance = round(
            _vary(innovation.discovery_chance, 0.50), 6
        )
        for effect_key, effect_val in innovation.effects.items():
            innovation.effects[effect_key] = round(
                _vary(effect_val, 0.30), 6
            )


def _randomize_discoverable_mechanics() -> None:
    """Perturb DISCOVERABLE_MECHANICS effect values +/-30%."""
    try:
        from brahmanda.engine.discovery import DISCOVERABLE_MECHANICS
    except ImportError:
        return

    for mechanic_name, mechanic in DISCOVERABLE_MECHANICS.items():
        effects = mechanic.get("effect", {})
        for key, val in effects.items():
            effects[key] = round(_vary(val, 0.30), 6)


# ---------------------------------------------------------------------------
# Rich summary
# ---------------------------------------------------------------------------

def _print_summary(seed: int) -> None:
    """Print a Rich panel summarising the key randomized values."""
    console = Console()

    # -- Ticks table --
    ticks_table = Table(title="Ticks per Yuga", show_header=True)
    ticks_table.add_column("Yuga", style="cyan")
    ticks_table.add_column("Ticks", justify="right", style="bold")
    for yuga in ("satya", "treta", "dvapara", "kali"):
        ticks_table.add_row(yuga.capitalize(), str(config.TICKS_PER_YUGA[yuga]))
    ticks_table.add_row("Total", str(config.TOTAL_TICKS_PER_MAHAYUGA), style="bold green")

    # -- Prana table --
    prana_table = Table(title="Prana Constants", show_header=True)
    prana_table.add_column("Parameter", style="cyan")
    prana_table.add_column("Value", justify="right", style="bold")
    for attr in ("PRANA_MAX", "PRANA_BASE_DRAIN", "PRANA_VICE_DRAIN_FACTOR",
                 "PRANA_REPLENISH_RATE", "PRANA_AGE_DRAIN_ONSET"):
        prana_table.add_row(attr, str(getattr(config, attr)))

    # -- Karma table --
    karma_table = Table(title="Karma Actions", show_header=True)
    karma_table.add_column("Action", style="cyan")
    karma_table.add_column("Karma", justify="right", style="bold")
    for action in sorted(config.KARMA_ACTIONS, key=lambda a: config.KARMA_ACTIONS[a], reverse=True):
        val = config.KARMA_ACTIONS[action]
        style = "green" if val > 0 else ("red" if val < 0 else "dim")
        karma_table.add_row(action, f"[{style}]{val}[/{style}]")

    # -- Loka resources table --
    loka_table = Table(title="Loka Base Resources", show_header=True)
    loka_table.add_column("Loka", style="cyan")
    loka_table.add_column("Resources", justify="right", style="bold")
    for loka_id, cfg in config.LOKA_CONFIG.items():
        loka_table.add_row(cfg["name"], str(cfg["base_resources"]))

    # -- Select LAWS samples --
    laws_table = Table(title="LAWS (sample)", show_header=True)
    laws_table.add_column("Law", style="cyan")
    laws_table.add_column("Value", justify="right", style="bold")
    sample_keys = [
        "hope_contagion_rate", "despair_breaking_point",
        "maya_entropy_boost", "atman_encounter_chance",
        "discovery_inquiry_chance", "vishnu_entropy_crisis",
        "shiva_decay_threshold", "deva_yama_trigger_chance",
    ]
    for key in sample_keys:
        if key in config.LAWS:
            laws_table.add_row(key, f"{config.LAWS[key]:.4f}")

    # -- Assemble panel --
    console.print()
    console.print(Panel(
        f"[bold]Seed:[/bold] {seed}\n"
        f"[bold]Total ticks:[/bold] {config.TOTAL_TICKS_PER_MAHAYUGA}",
        title="[bold magenta]Brahmanda Universe Randomizer[/bold magenta]",
        subtitle="every run is a new universe",
    ))
    console.print(ticks_table)
    console.print(prana_table)
    console.print(karma_table)
    console.print(loka_table)
    console.print(laws_table)
    console.print()
