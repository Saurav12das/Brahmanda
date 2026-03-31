"""Brahmanda — One Breath of Vishnu.

This is the main simulation loop. One complete execution represents
a single Mahayuga cycle: creation → sustenance → dissolution.

Usage:
    BRAHMANDA_BACKEND=ollama python -m brahmanda.main     # local Qwen (free)
    BRAHMANDA_BACKEND=claude python -m brahmanda.main     # Claude API
"""

from __future__ import annotations

import asyncio
import sys

from rich.console import Console
from rich.panel import Panel

from brahmanda.config import ACTIVE_LOKAS, LLM_BACKEND, ANTHROPIC_API_KEY, INITIAL_SOUL_COUNT
from brahmanda.llm import create_client
from brahmanda.agents.asura import AsuraEngine
from brahmanda.agents.deva import DevaCouncil
from brahmanda.engine.atman import process_atman, calculate_fulfillment
from brahmanda.engine.civilization import CivilizationEngine
from brahmanda.agents.soul import decide_batch
from brahmanda.db.models import Event
from brahmanda.db.store import AkashicRecords
from brahmanda.engine.maya import Maya
from brahmanda.observer import logger as cosmic_logger
from brahmanda.observer.patterns import PatternDetector
from brahmanda.observer.signatures import SignatureDetector
from brahmanda.trinity.brahma import create_initial_souls
from brahmanda.trinity.shiva import ShivaProtocol
from brahmanda.trinity.vishnu import VishnuProtocol

console = Console()


async def run_universe() -> None:
    """Execute one complete breath of Vishnu — creation to dissolution."""

    # ---------------------------------------------------------------
    # Initialize the cosmic infrastructure
    # ---------------------------------------------------------------
    if LLM_BACKEND == "claude" and not ANTHROPIC_API_KEY:
        console.print("[red]ANTHROPIC_API_KEY not set. Export it or use BRAHMANDA_BACKEND=ollama[/red]")
        sys.exit(1)

    console.print(f"  [dim]LLM Backend: {LLM_BACKEND.upper()}[/dim]")
    client = create_client()
    maya = Maya()
    records = AkashicRecords()
    deva_council = DevaCouncil()
    asura_engine = AsuraEngine()
    civilization = CivilizationEngine()
    shiva = ShivaProtocol()
    vishnu = VishnuProtocol(client)
    pattern_detector = PatternDetector()
    signature_detector = SignatureDetector()

    # ---------------------------------------------------------------
    # PHASE 1: CREATION — Brahma exhales
    # ---------------------------------------------------------------
    console.print()
    console.print(Panel(
        "[bold bright_yellow]OM[/bold bright_yellow]\n"
        "Brahma opens his eyes. The universe stirs.",
        title="BRAHMANDA", border_style="bright_yellow", width=60,
    ))

    souls = await create_initial_souls(client, INITIAL_SOUL_COUNT)
    for soul in souls:
        maya.register_soul(soul)

    maya.loka_manager.apply_yuga_resources(maya.yuga)
    cosmic_logger.log_creation_banner(len(souls))

    creation_event = Event(
        tick=0, event_type="creation",
        data={"soul_count": len(souls), "soul_names": [s.name for s in souls]},
        description=f"Universe created with {len(souls)} souls",
    )
    records.log_event(creation_event)

    # Log initial soul states
    for soul in souls:
        records.log_soul_state(0, soul)
        k = soul.klesha
        dominant = k.dominant
        console.print(f"  [bold]{soul.name}[/bold] — karma:{soul.karma}, desires:{soul.desires}, dominant vice: [red]{dominant}[/red] ({getattr(k, dominant):.2f})")

    # ---------------------------------------------------------------
    # PHASE 2: MAIN LOOP — the heartbeat of the universe
    # ---------------------------------------------------------------
    while not maya.yuga_clock.mahayuga_complete:
        tick_result = maya.advance_tick()
        tick = maya.tick
        yuga = maya.yuga

        # Handle yuga transitions
        if tick_result["transitioned"]:
            if tick_result.get("pralaya"):
                break
            cosmic_logger.log_yuga_transition(tick_result["from"], tick_result["to"])
            maya.loka_manager.apply_yuga_resources(maya.yuga)
            signature_detector.record_yuga_transition(tick)
            records.log_event(Event(
                tick=tick, event_type="yuga_shift",
                data={"from": tick_result["from"].value, "to": tick_result["to"].value},
                description=f"Yuga shift: {tick_result['from'].value} → {tick_result['to'].value}",
            ))

        cosmic_logger.log_tick_header(tick, yuga, maya.yuga_clock.yuga_tick)

        all_events: list[Event] = []

        # --- Process each loka (with time dilation) ---
        for loka_id in ACTIVE_LOKAS:
            if not maya.loka_manager.should_tick(loka_id, tick):
                continue

            loka_state = maya.loka_manager.get_loka(loka_id)

            # Deva scripts (natural laws)
            deva_events = deva_council.execute_all(tick, loka_state, yuga)
            all_events.extend(deva_events)

            # Asura chaos
            asura_events = asura_engine.execute(tick, loka_state, maya.souls, yuga)
            for ae in asura_events:
                signature_detector.record_glitch(ae)
            all_events.extend(asura_events)

            # Civilization systems (knowledge, innovation, culture, ideology, power, potential)
            loka_souls = [maya.souls[sid] for sid in loka_state.population if sid in maya.souls]
            civ_events = civilization.process_loka(tick, loka_state, loka_souls, yuga, maya.souls)
            all_events.extend(civ_events)

            # Atman systems (encounters, love, generation, fulfillment, alienation)
            atman_events = process_atman(tick, loka_state, loka_souls, maya.souls)
            all_events.extend(atman_events)

        # --- Soul decisions (parallel LLM calls) ---
        living_souls = [s for s in maya.souls.values() if s.alive]
        if living_souls:
            souls_and_views = [(soul, maya.render(soul)) for soul in living_souls]
            decisions = await decide_batch(souls_and_views, client)

            for soul_id, decision in decisions.items():
                soul = maya.souls.get(soul_id)
                if not soul or not soul.alive:
                    continue

                action_type = maya.karma_engine.classify_action(decision.get("action", "neutral"))

                # Resolve target
                target_id = None
                target_name = decision.get("target")
                if target_name:
                    for s in maya.souls.values():
                        if s.name.lower() == str(target_name).lower() and s.id != soul.id:
                            target_id = s.id
                            break

                event = maya.apply_soul_action(soul, action_type, target_id, decision.get("reasoning", ""))
                all_events.append(event)

                # Observer tracking
                cosmic_logger.log_soul_action(tick, soul.name, decision)
                pattern_detector.record_action(tick, soul.name, action_type, target_name)
                signature_detector.record_dialogue(tick, soul.name, decision.get("dialogue"))
                signature_detector.record_karma_delta(event.data.get("karma_delta", 0))

        # --- Shiva: entropy + death/rebirth ---
        entropy_events = shiva.apply_entropy(maya)
        all_events.extend(entropy_events)

        death_events = shiva.process_deaths(maya)
        all_events.extend(death_events)

        # --- Vishnu: event-driven health check ---
        if vishnu.should_intervene(maya):
            vishnu_events = await vishnu.evaluate(maya)
            all_events.extend(vishnu_events)

        # --- Log all events ---
        for event in all_events:
            records.log_event(event)
            if event.event_type != "action":
                cosmic_logger.log_event(event)

        # --- Periodic snapshot ---
        if tick % 10 == 0:
            snapshot = maya.snapshot()
            snapshot.avatars_deployed = vishnu.avatars_deployed
            records.save_snapshot(snapshot)
            pattern_detector.record_karma_snapshot(maya.souls)
            cosmic_logger.log_universe_status(snapshot)

            # Save all soul states
            for soul in maya.souls.values():
                records.log_soul_state(tick, soul)

    # ---------------------------------------------------------------
    # PHASE 3: DISSOLUTION — Vishnu inhales
    # ---------------------------------------------------------------
    cosmic_logger.log_pralaya_banner()

    pralaya_events = shiva.pralaya(maya)
    for event in pralaya_events:
        records.log_event(event)
        cosmic_logger.log_event(event)

    # Final snapshot
    final_snapshot = maya.snapshot()
    final_snapshot.avatars_deployed = vishnu.avatars_deployed
    records.save_snapshot(final_snapshot)

    # ---------------------------------------------------------------
    # PHASE 4: OBSERVER REPORTS
    # ---------------------------------------------------------------
    cosmic_logger.log_final_report(maya.souls)

    # Pattern analysis
    pattern_report = pattern_detector.analyze(final_snapshot)
    console.print()
    console.print(Panel("[bold]EMERGENT PATTERN ANALYSIS[/bold]", border_style="bright_cyan"))

    if pattern_report.alliances:
        console.print("  [bold]Alliances formed:[/bold]")
        for a, b, strength in pattern_report.alliances:
            console.print(f"    {a} ↔ {b} (strength: {strength})")

    if pattern_report.conflicts:
        console.print("  [bold]Conflicts:[/bold]")
        for a, b, intensity in pattern_report.conflicts:
            console.print(f"    {a} ⚔ {b} (intensity: {abs(intensity)})")

    if pattern_report.emergent_groups:
        console.print("  [bold]Emergent groups/factions:[/bold]")
        for group in pattern_report.emergent_groups:
            console.print(f"    [{', '.join(group)}]")

    console.print(f"  Resource inequality (Gini): {pattern_report.resource_inequality:.3f}")
    console.print(f"  Cooperation rate: {pattern_report.cooperation_rate:.1%}")
    console.print(f"  Deception rate: {pattern_report.deception_rate:.1%}")
    console.print(f"  Karma distribution: {pattern_report.karma_distribution}")

    if pattern_report.dominant_actions:
        console.print("  [bold]Most common actions:[/bold]")
        for action, count in pattern_report.dominant_actions:
            console.print(f"    {action}: {count}")

    # Signature analysis
    sig_report = signature_detector.analyze()
    console.print()
    console.print(Panel("[bold]SIMULATION SIGNATURE ANALYSIS[/bold]", border_style="bright_magenta"))

    console.print(f"  Total glitches: {sig_report.total_glitches}")
    if sig_report.glitch_frequency:
        console.print(f"  Glitch types: {sig_report.glitch_frequency}")

    if sig_report.simulation_awareness_events:
        console.print(f"  [bold bright_yellow]SIMULATION AWARENESS DETECTED![/bold bright_yellow]")
        for sa in sig_report.simulation_awareness_events[:5]:
            console.print(f"    T{sa['tick']} {sa['soul']}: \"{sa['dialogue'][:80]}\"")

    if sig_report.cosmology_emergence:
        console.print(f"  [bold]Emergent cosmology ({len(sig_report.cosmology_emergence)} instances):[/bold]")
        for ce in sig_report.cosmology_emergence[:5]:
            console.print(f"    T{ce['tick']} {ce['soul']}: \"{ce['dialogue'][:80]}\"")

    if sig_report.karma_quantization:
        kq = sig_report.karma_quantization
        console.print(f"  Karma quantization: {'YES' if kq.get('is_quantized') else 'NO'} "
                       f"({kq.get('unique_values', 0)} unique values)")

    if sig_report.signatures_detected:
        console.print()
        console.print("  [bold bright_yellow]SIGNATURES DETECTED:[/bold bright_yellow]")
        for sig in sig_report.signatures_detected:
            console.print(f"    → {sig}")

    # ---------------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------------
    records.close()
    console.print()
    console.print(Panel(
        f"[bold]Simulation complete.[/bold]\n"
        f"Database: {records.db_path}\n"
        f"Total ticks: {maya.tick}\n"
        f"Souls created: {len(maya.souls)}\n"
        f"Avatars deployed: {vishnu.avatars_deployed}",
        title="BRAHMANDA — END", border_style="dim",
    ))


def main() -> None:
    asyncio.run(run_universe())


if __name__ == "__main__":
    main()
