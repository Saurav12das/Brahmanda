"""Maya — the Rendering Engine of Brahmanda.

Maya is not illusion — it is the measurement system that processes
consciousness into perceived reality. Each soul sees a filtered view
of the universe based on their loka, karma, and the current yuga.
"""

from __future__ import annotations

from brahmanda.config import LOKA_CONFIG, LokaID, YugaType, YUGA_PARAMS
from brahmanda.db.models import Event, LokaState, SoulState, UniverseSnapshot
from brahmanda.engine.karma import KarmaEngine
from brahmanda.engine.loka import LokaManager
from brahmanda.engine.yuga import YugaClock


class Maya:
    """The world state manager — controls what exists and what is perceived."""

    def __init__(self) -> None:
        self.yuga_clock = YugaClock()
        self.loka_manager = LokaManager()
        self.karma_engine = KarmaEngine()
        self.souls: dict[str, SoulState] = {}
        self.events: list[Event] = []

    @property
    def tick(self) -> int:
        return self.yuga_clock.global_tick

    @property
    def yuga(self) -> YugaType:
        return self.yuga_clock.current_yuga

    def register_soul(self, soul: SoulState) -> None:
        self.souls[soul.id] = soul
        self.loka_manager.place_soul(soul)

    def remove_soul(self, soul_id: str) -> None:
        if soul_id in self.souls:
            soul = self.souls[soul_id]
            self.loka_manager.remove_soul(soul)
            del self.souls[soul_id]

    def render(self, soul: SoulState) -> dict:
        """Render what a soul can perceive — the core of Maya."""
        loka_state = self.loka_manager.get_loka(soul.loka)
        loka_cfg = LOKA_CONFIG[soul.loka]
        yuga_params = YUGA_PARAMS[self.yuga]

        visible_souls = self.loka_manager.get_visible_souls(soul, self.souls)
        truth_vis = yuga_params["truth_visibility"]

        if soul.karma > 50:
            truth_vis = min(1.0, truth_vis + 0.2)
        if soul.is_avatar:
            truth_vis = 1.0

        soul_views = []
        for other in visible_souls:
            view = {"name": other.name, "id": other.id}
            if truth_vis > 0.5:
                view["karma_hint"] = "positive" if other.karma > 0 else "negative" if other.karma < 0 else "neutral"
                view["resources"] = other.resources
            if truth_vis > 0.75:
                view["desires"] = other.desires[:2]
                view["karma"] = other.karma
            soul_views.append(view)

        resource_view = loka_state.resources if truth_vis > 0.3 else "unknown"

        # Yuga-amplified vices
        vice_amplifier = {
            YugaType.SATYA: 0.5, YugaType.TRETA: 0.8,
            YugaType.DVAPARA: 1.2, YugaType.KALI: 1.5,
        }[self.yuga]
        entropy_boost = loka_state.entropy * 0.3

        amplified_vices = {
            "kama": min(1.0, soul.klesha.kama * vice_amplifier + entropy_boost * 0.5),
            "krodha": min(1.0, soul.klesha.krodha * vice_amplifier + entropy_boost * 0.7),
            "lobha": min(1.0, soul.klesha.lobha * vice_amplifier + entropy_boost * 0.6),
            "moha": min(1.0, soul.klesha.moha * vice_amplifier + entropy_boost * 0.3),
            "ahamkara": min(1.0, soul.klesha.ahamkara * vice_amplifier + entropy_boost * 0.5),
        }
        if soul.is_avatar:
            amplified_vices = {k: v * 0.2 for k, v in amplified_vices.items()}

        # Prana urgency
        if soul.prana > 70:
            prana_status = "healthy"
        elif soul.prana > 40:
            prana_status = "weakening"
        elif soul.prana > 15:
            prana_status = "CRITICAL — you feel your life force fading"
        else:
            prana_status = "DYING — every moment could be your last"

        return {
            "loka": loka_cfg["name"],
            "loka_description": loka_cfg["description"],
            "physics": loka_cfg["physics"],
            "yuga": self.yuga.value,
            "yuga_description": self._yuga_description(),
            "tick": self.tick,
            "your_karma": soul.karma,
            "your_resources": soul.resources,
            "your_prana": round(soul.prana, 1),
            "prana_status": prana_status,
            "your_desires": soul.desires,
            "your_memories": soul.memories[-5:],
            "nearby_souls": soul_views,
            "available_resources": resource_view,
            "entropy": round(loka_state.entropy, 2),
            "truth_clarity": round(truth_vis, 2),
            "population": len(loka_state.population),
            "relationships": {
                self.souls[sid].name: affinity
                for sid, affinity in soul.relationships.items()
                if sid in self.souls
            },
            "your_vices": amplified_vices,
        }

    def _yuga_description(self) -> str:
        descs = {
            YugaType.SATYA: "The Golden Age — truth and dharma prevail, resources are abundant",
            YugaType.TRETA: "The Silver Age — dharma weakens, first conflicts emerge",
            YugaType.DVAPARA: "The Bronze Age — balance tips, alliances and wars define the era",
            YugaType.KALI: "The Dark Age — deception thrives, scarcity reigns, but small virtues shine brightest",
        }
        return descs[self.yuga]

    def apply_soul_action(
        self, soul: SoulState, action_type: str, target_id: str | None, description: str,
    ) -> Event:
        """Apply a soul's action to the world state — including prana effects."""
        action = self.karma_engine.create_action_record(
            tick=self.tick, soul=soul, action_type=action_type,
            target_id=target_id, description=description, yuga=self.yuga,
        )
        loka_state = self.loka_manager.get_loka(soul.loka)

        if action_type == "trade" and target_id and target_id in self.souls:
            amount = min(3, soul.resources)
            soul.resources -= amount
            self.souls[target_id].resources += amount
            self._update_relationship(soul, target_id, 2)
            self._update_relationship(self.souls[target_id], soul.id, 2)

        elif action_type == "share" and target_id and target_id in self.souls:
            amount = min(5, soul.resources)
            soul.resources -= amount
            self.souls[target_id].resources += amount
            self._update_relationship(soul, target_id, 3)

        elif action_type == "steal" and target_id and target_id in self.souls:
            target = self.souls[target_id]
            amount = min(5, target.resources)
            target.resources -= amount
            soul.resources += amount
            # Vampiric: steal prana too
            prana_stolen = min(2.0, target.prana * 0.1)
            target.prana = max(0.0, target.prana - prana_stolen)
            soul.prana = min(100.0, soul.prana + prana_stolen)
            self._update_relationship(soul, target_id, -5)
            self._update_relationship(target, soul.id, -5)

        elif action_type == "cooperate" and target_id and target_id in self.souls:
            soul.resources += 2
            self.souls[target_id].resources += 2
            # Mutual prana bonus
            soul.prana = min(100.0, soul.prana + 1.0)
            self.souls[target_id].prana = min(100.0, self.souls[target_id].prana + 1.0)
            self._update_relationship(soul, target_id, 3)
            self._update_relationship(self.souls[target_id], soul.id, 3)

        elif action_type == "create":
            soul.resources += 3
            # Creating adds to the commons
            loka_state.resources += 2

        elif action_type == "meditate":
            # Free prana replenishment — no resource cost
            soul.prana = min(100.0, soul.prana + 2.0)

        elif action_type in ("fight_justified", "fight_unjustified"):
            if target_id and target_id in self.souls:
                target = self.souls[target_id]
                # Combat costs prana for both — fighting is lethal
                soul.prana = max(0.0, soul.prana - 2.0)
                target.prana = max(0.0, target.prana - 5.0)
                target.resources = max(0, target.resources - 3)
                self._update_relationship(soul, target_id, -4)
                self._update_relationship(target, soul.id, -4)

        elif action_type == "hoard":
            soul.resources += 1

        elif action_type == "deceive" and target_id and target_id in self.souls:
            target = self.souls[target_id]
            soul.resources += 4
            target.resources = max(0, target.resources - 4)
            # Vampiric prana drain
            prana_stolen = min(2.0, target.prana * 0.1)
            target.prana = max(0.0, target.prana - prana_stolen)
            soul.prana = min(100.0, soul.prana + prana_stolen)
            if YUGA_PARAMS[self.yuga]["truth_visibility"] > 0.5:
                self._update_relationship(target, soul.id, -6)

        # Add to soul memory
        memory = f"Tick {self.tick}: I chose to {action_type}"
        if target_id and target_id in self.souls:
            memory += f" with {self.souls[target_id].name}"
        soul.memories.append(memory)
        if len(soul.memories) > 10:
            soul.memories = soul.memories[-10:]

        event = Event(
            tick=self.tick, event_type="action", loka=soul.loka,
            data=action.model_dump(), description=description,
        )
        self.events.append(event)
        return event

    def _update_relationship(self, soul: SoulState, other_id: str, delta: int) -> None:
        current = soul.relationships.get(other_id, 0)
        soul.relationships[other_id] = max(-100, min(100, current + delta))

    def advance_tick(self) -> dict:
        """Advance the cosmic clock — age souls, drain/replenish prana, decay karma."""
        result = self.yuga_clock.tick()

        for soul in self.souls.values():
            if soul.alive:
                soul.age += 1
                soul.lifetime += 1

                # Dynamic karma decay
                loka_state = self.loka_manager.get_loka(soul.loka)
                self.karma_engine.decay_karma(soul, loka_state.entropy, self.yuga)

                # Prana drain then replenish — the heartbeat of survival
                self.karma_engine.drain_prana(soul, loka_state.entropy, self.yuga)
                self.karma_engine.replenish_prana(soul, loka_state)

        return result

    def snapshot(self) -> UniverseSnapshot:
        total_karma = sum(s.karma for s in self.souls.values())
        global_entropy = sum(
            self.loka_manager.lokas[lid].entropy for lid in self.loka_manager.lokas
        ) / len(self.loka_manager.lokas)

        return UniverseSnapshot(
            tick=self.tick, yuga=self.yuga,
            yuga_tick=self.yuga_clock.yuga_tick,
            lokas=dict(self.loka_manager.lokas),
            souls=dict(self.souls),
            total_karma=total_karma,
            global_entropy=global_entropy,
            events=self.events[-20:],
        )
