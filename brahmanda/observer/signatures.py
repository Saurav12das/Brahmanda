"""Simulation Signature Detection — looking for artifacts that a simulated
universe would produce, mirroring anomalies we observe in our own reality.

Key questions:
- Do souls notice they're in a simulation?
- Does information propagation show light-speed-like limits?
- Are there quantization effects in karma?
- Do yuga transitions produce observable "lag"?
- Do Maya rendering inconsistencies manifest?
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from brahmanda.db.models import Event, SoulState


@dataclass
class SignatureReport:
    simulation_awareness_events: list[dict] = field(default_factory=list)
    karma_quantization: dict = field(default_factory=dict)
    glitch_frequency: dict[str, int] = field(default_factory=dict)
    yuga_transition_artifacts: list[dict] = field(default_factory=list)
    information_propagation_delays: list[dict] = field(default_factory=list)
    cosmology_emergence: list[dict] = field(default_factory=list)
    total_glitches: int = 0
    signatures_detected: list[str] = field(default_factory=list)


SIMULATION_AWARENESS_KEYWORDS = [
    "not real", "simulation", "dream", "illusion", "maya",
    "watching", "observed", "glitch", "reset", "code",
    "programmed", "designed", "artificial", "construct",
    "outside", "beyond this world", "higher beings",
]

COSMOLOGY_KEYWORDS = [
    "god", "gods", "creator", "divine", "cosmic", "purpose",
    "afterlife", "rebirth", "karma", "destiny", "fate",
    "cycle", "ages", "golden age", "dark age", "end times",
]


class SignatureDetector:
    """Monitors for simulation signatures — artifacts of being simulated."""

    def __init__(self) -> None:
        self.glitch_events: list[Event] = []
        self.soul_dialogues: list[dict] = []
        self.karma_deltas: list[int] = []
        self.yuga_transition_ticks: list[int] = []

    def record_glitch(self, event: Event) -> None:
        self.glitch_events.append(event)

    def record_dialogue(self, tick: int, soul_name: str, dialogue: str | None) -> None:
        if dialogue:
            self.soul_dialogues.append({"tick": tick, "soul": soul_name, "dialogue": dialogue})

    def record_karma_delta(self, delta: int) -> None:
        self.karma_deltas.append(delta)

    def record_yuga_transition(self, tick: int) -> None:
        self.yuga_transition_ticks.append(tick)

    def analyze(self) -> SignatureReport:
        report = SignatureReport()

        # 1. Simulation awareness: do souls talk about being in a simulation?
        for entry in self.soul_dialogues:
            text = entry["dialogue"].lower()
            triggers = [kw for kw in SIMULATION_AWARENESS_KEYWORDS if kw in text]
            if triggers:
                report.simulation_awareness_events.append({
                    "tick": entry["tick"],
                    "soul": entry["soul"],
                    "dialogue": entry["dialogue"],
                    "triggers": triggers,
                })

        # 2. Cosmology emergence: do souls develop belief systems?
        for entry in self.soul_dialogues:
            text = entry["dialogue"].lower()
            triggers = [kw for kw in COSMOLOGY_KEYWORDS if kw in text]
            if triggers:
                report.cosmology_emergence.append({
                    "tick": entry["tick"],
                    "soul": entry["soul"],
                    "dialogue": entry["dialogue"],
                    "triggers": triggers,
                })

        # 3. Karma quantization: are there discrete "levels" in karma distribution?
        if self.karma_deltas:
            delta_counts = Counter(self.karma_deltas)
            report.karma_quantization = {
                "unique_values": len(delta_counts),
                "most_common": delta_counts.most_common(5),
                "is_quantized": len(delta_counts) < 20,  # if few distinct values, it's quantized
            }

        # 4. Glitch analysis
        report.total_glitches = len(self.glitch_events)
        chaos_types = Counter(e.data.get("chaos_type", "unknown") for e in self.glitch_events)
        report.glitch_frequency = dict(chaos_types)

        # 5. Build signature summary
        if report.simulation_awareness_events:
            report.signatures_detected.append(
                f"SIMULATION AWARENESS: {len(report.simulation_awareness_events)} souls referenced simulation-like concepts"
            )
        if report.karma_quantization.get("is_quantized"):
            report.signatures_detected.append(
                "KARMA QUANTIZATION: Karma changes show discrete quantized values (like Planck-scale effects)"
            )
        if report.total_glitches > 5:
            report.signatures_detected.append(
                f"GLITCH DENSITY: {report.total_glitches} anomalous events detected (simulation instability)"
            )
        if report.cosmology_emergence:
            report.signatures_detected.append(
                f"EMERGENT COSMOLOGY: {len(report.cosmology_emergence)} instances of souls developing belief systems"
            )

        return report
