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
        """Add a soul to the universe."""
        self.souls[soul.id] = soul
        self.loka_manager.place_soul(soul)

    def remove_soul(self, soul_id: str) -> None:
        """Remove a soul from the universe entirely."""
        if soul_id in self.souls:
            soul = self.souls[soul_id]
            self.loka_manager.remove_soul(soul)
            del self.souls[soul_id]

    def render(self, soul: SoulState) -> dict:
        """Render what a soul can perceive — the core of Maya.

        Perception is filtered by:
        - Loka: only see souls/resources in your dimension
        - Karma: higher karma = broader perception
        - Yuga: truth_visibility degrades in darker ages
        - Avatar status: avatars see more
        """
        loka_state = self.loka_manager.get_loka(soul.loka)
        loka_cfg = LOKA_CONFIG[soul.loka]
        yuga_params = YUGA_PARAMS[self.yuga]

        visible_souls = self.loka_manager.get_visible_souls(soul, self.souls)
        truth_vis = yuga_params["truth_visibility"]

        # Karma-based perception boost
        if soul.karma > 50:
            truth_vis = min(1.0, truth_vis + 0.2)
        if soul.is_avatar:
            truth_vis = 1.0

        # Render soul descriptions based on visibility
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

        # Resource visibility
        resource_view = loka_state.resources if truth_vis > 0.3 else "unknown"

        return {
            "loka": loka_cfg["name"],
            "loka_description": loka_cfg["description"],
            "physics": loka_cfg["physics"],
            "yuga": self.yuga.value,
            "yuga_description": self._yuga_description(),
            "tick": self.tick,
            "your_karma": soul.karma,
            "your_resources": soul.resources,
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
        """Apply a soul's action to the world state."""
        action = self.karma_engine.create_action_record(
            tick=self.tick, soul=soul, action_type=action_type,
            target_id=target_id, description=description, yuga=self.yuga,
        )

        # Apply resource effects
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
            amount = min(5, self.souls[target_id].resources)
            self.souls[target_id].resources -= amount
            soul.resources += amount
            self._update_relationship(soul, target_id, -5)
            self._update_relationship(self.souls[target_id], soul.id, -5)

        elif action_type == "cooperate" and target_id and target_id in self.souls:
            soul.resources += 2
            self.souls[target_id].resources += 2
            self._update_relationship(soul, target_id, 3)
            self._update_relationship(self.souls[target_id], soul.id, 3)

        elif action_type == "create":
            soul.resources += 3

        elif action_type == "meditate":
            pass  # karma already applied

        elif action_type in ("fight_justified", "fight_unjustified"):
            if target_id and target_id in self.souls:
                self.souls[target_id].resources = max(0, self.souls[target_id].resources - 3)
                self._update_relationship(soul, target_id, -4)
                self._update_relationship(self.souls[target_id], soul.id, -4)

        elif action_type == "hoard":
            soul.resources += 1

        elif action_type == "deceive" and target_id and target_id in self.souls:
            soul.resources += 4
            self.souls[target_id].resources = max(0, self.souls[target_id].resources - 4)
            # Victim doesn't know yet (low truth visibility helps the deceiver)
            if YUGA_PARAMS[self.yuga]["truth_visibility"] > 0.5:
                self._update_relationship(self.souls[target_id], soul.id, -6)

        # Add to soul memory
        memory = f"Tick {self.tick}: I chose to {action_type}"
        if target_id and target_id in self.souls:
            memory += f" with {self.souls[target_id].name}"
        soul.memories.append(memory)
        if len(soul.memories) > 10:
            soul.memories = soul.memories[-10:]

        # Create event
        event = Event(
            tick=self.tick,
            event_type="action",
            loka=soul.loka,
            data=action.model_dump(),
            description=description,
        )
        self.events.append(event)
        return event

    def _update_relationship(self, soul: SoulState, other_id: str, delta: int) -> None:
        current = soul.relationships.get(other_id, 0)
        soul.relationships[other_id] = max(-100, min(100, current + delta))

    def advance_tick(self) -> dict:
        """Advance the cosmic clock by one tick."""
        result = self.yuga_clock.tick()

        # Age all living souls
        for soul in self.souls.values():
            if soul.alive:
                soul.age += 1
                soul.lifetime += 1

        return result

    def snapshot(self) -> UniverseSnapshot:
        """Capture a full universe snapshot."""
        total_karma = sum(s.karma for s in self.souls.values())
        global_entropy = sum(
            self.loka_manager.lokas[lid].entropy for lid in self.loka_manager.lokas
        ) / len(self.loka_manager.lokas)

        return UniverseSnapshot(
            tick=self.tick,
            yuga=self.yuga,
            yuga_tick=self.yuga_clock.yuga_tick,
            lokas=dict(self.loka_manager.lokas),
            souls=dict(self.souls),
            total_karma=total_karma,
            global_entropy=global_entropy,
            events=self.events[-20:],
        )
