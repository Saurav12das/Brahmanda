"""Cosmic Logger — records the history of Brahmanda with Rich formatting."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from brahmanda.config import YugaType
from brahmanda.db.models import Event, SoulState, UniverseSnapshot


console = Console()

YUGA_COLORS = {
    YugaType.SATYA: "bright_yellow",
    YugaType.TRETA: "bright_white",
    YugaType.DVAPARA: "bright_cyan",
    YugaType.KALI: "bright_red",
}

EVENT_STYLES = {
    "action": "green",
    "death": "red",
    "rebirth": "bright_magenta",
    "yuga_shift": "bold bright_yellow",
    "avatar_deploy": "bold bright_cyan",
    "pralaya": "bold bright_red",
    "asura_glitch": "yellow",
    "deva_action": "blue",
    "natural_disaster": "red",
    "vishnu_assessment": "bright_cyan",
    "shiva_decay": "dim red",
}


def log_event(event: Event) -> None:
    style = EVENT_STYLES.get(event.event_type, "white")
    prefix = f"[dim]T{event.tick:03d}[/dim]"
    loka_tag = f"[dim]@{event.loka.name if event.loka else '???'}[/dim] " if event.loka is not None else ""
    console.print(f"  {prefix} {loka_tag}[{style}]{event.description}[/{style}]")


def log_soul_action(tick: int, soul_name: str, decision: dict) -> None:
    action = decision.get("action", "?")
    target = decision.get("target", "")
    reasoning = decision.get("reasoning", "")[:80]
    dialogue = decision.get("dialogue")

    line = f"  [dim]T{tick:03d}[/dim] [bold]{soul_name}[/bold] → [green]{action}[/green]"
    if target:
        line += f" [dim]→ {target}[/dim]"
    console.print(line)
    if reasoning:
        console.print(f"        [dim italic]{reasoning}[/dim italic]")
    if dialogue:
        console.print(f'        [bright_white]"{dialogue}"[/bright_white]')


def log_tick_header(tick: int, yuga: YugaType, yuga_tick: int) -> None:
    color = YUGA_COLORS[yuga]
    console.print()
    console.rule(f"[{color}]Tick {tick} — {yuga.value.upper()} Yuga (t={yuga_tick})[/{color}]")


def log_yuga_transition(from_yuga: YugaType, to_yuga: YugaType | None) -> None:
    if to_yuga is None:
        console.print(Panel(
            "[bold bright_red]The Mahayuga cycle is complete.\nShiva prepares the Tandava — PRALAYA begins.[/bold bright_red]",
            title="END OF TIME",
            border_style="bright_red",
        ))
    else:
        console.print(Panel(
            f"[bold]The age shifts: {from_yuga.value.upper()} → {to_yuga.value.upper()}[/bold]\n"
            f"The laws of the universe transform.",
            title="YUGA TRANSITION",
            border_style=YUGA_COLORS[to_yuga],
        ))


def log_universe_status(snapshot: UniverseSnapshot) -> None:
    living = [s for s in snapshot.souls.values() if s.alive]

    table = Table(title=f"Universe Status — Tick {snapshot.tick}", show_lines=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Yuga", f"{snapshot.yuga.value.upper()}")
    table.add_row("Living Souls", str(len(living)))
    table.add_row("Total Karma", str(snapshot.total_karma))
    table.add_row("Avg Karma", f"{snapshot.total_karma / max(1, len(living)):.1f}")
    table.add_row("Global Entropy", f"{snapshot.global_entropy:.2f}")
    table.add_row("Avatars Deployed", str(snapshot.avatars_deployed))

    for lid, loka in snapshot.lokas.items():
        table.add_row(
            f"  {loka.name}",
            f"pop={len(loka.population)}, res={loka.resources}, entropy={loka.entropy:.2f}",
        )

    console.print(table)


def log_creation_banner(soul_count: int) -> None:
    console.print(Panel(
        f"[bold bright_yellow]Brahma exhales — the universe is born.[/bold bright_yellow]\n"
        f"{soul_count} souls awaken in Bhu-loka.\n"
        f"The Satya Yuga begins — the age of truth.",
        title="CREATION",
        border_style="bright_yellow",
    ))


def log_pralaya_banner() -> None:
    console.print(Panel(
        "[bold bright_red]Vishnu inhales — the universe collapses.[/bold bright_red]\n"
        "All form returns to the void.\n"
        "Only karma seeds remain for the next cycle.",
        title="DISSOLUTION — PRALAYA",
        border_style="bright_red",
    ))


def log_final_report(souls: dict[str, SoulState]) -> None:
    console.print()
    console.print(Panel("[bold]FINAL SOUL REPORT[/bold]", border_style="bright_white"))

    table = Table(show_lines=True)
    table.add_column("Name", style="bold")
    table.add_column("Final Karma", justify="right")
    table.add_column("Lives", justify="right")
    table.add_column("Lifetime", justify="right")
    table.add_column("Last Loka")
    table.add_column("Avatar?")

    for soul in sorted(souls.values(), key=lambda s: s.karma, reverse=True):
        karma_style = "green" if soul.karma > 0 else "red" if soul.karma < 0 else "white"
        table.add_row(
            soul.name,
            f"[{karma_style}]{soul.karma}[/{karma_style}]",
            str(soul.lives),
            str(soul.lifetime),
            str(soul.loka.name),
            "Yes" if soul.is_avatar else "",
        )

    console.print(table)
