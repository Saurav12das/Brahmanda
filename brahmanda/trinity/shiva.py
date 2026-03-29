"""Shiva — The Destroyer, The Hard Reset.

Shiva is not evil — he is entropy itself. He breaks down what is corrupt,
recycles what is stale, and when the Mahayuga ends, he triggers Pralaya:
the dissolution of the entire universe.
"""

from __future__ import annotations

from brahmanda.config import ACTIVE_LOKAS, YUGA_PARAMS, LokaID, YugaType
from brahmanda.db.models import Event, SoulState
from brahmanda.engine.maya import Maya


class ShivaProtocol:
    """Manages entropy, decay, and dissolution."""

    def apply_entropy(self, maya: Maya) -> list[Event]:
        """Apply yuga-appropriate entropy to all lokas."""
        events = []
        entropy_rate = YUGA_PARAMS[maya.yuga]["entropy_rate"]

        for loka_id in ACTIVE_LOKAS:
            maya.loka_manager.apply_entropy(loka_id, entropy_rate)
            loka = maya.loka_manager.get_loka(loka_id)

            # High entropy degrades resources
            if loka.entropy > 0.6:
                decay = int(loka.resources * 0.05)
                loka.resources = max(0, loka.resources - decay)
                if decay > 0:
                    events.append(Event(
                        tick=maya.tick,
                        event_type="shiva_decay",
                        loka=loka_id,
                        data={"entropy": loka.entropy, "resource_decay": decay},
                        description=f"Shiva's entropy erodes {loka.name}: {decay} resources decay",
                    ))

        return events

    def garbage_collect(self, maya: Maya) -> list[Event]:
        """Remove dead souls that have completed samsara processing."""
        events = []
        dead_ids = [sid for sid, s in maya.souls.items() if not s.alive]
        for sid in dead_ids:
            soul = maya.souls[sid]
            # Rebirth is handled by karma engine — here we just mark the death event
            events.append(Event(
                tick=maya.tick,
                event_type="death",
                loka=soul.loka,
                data={"soul_name": soul.name, "final_karma": soul.karma, "lives": soul.lives},
                description=f"{soul.name} dies with karma {soul.karma} after {soul.lives} lives",
            ))
        return events

    def process_deaths(self, maya: Maya) -> list[Event]:
        """Check all living souls for mortality, process deaths and rebirth."""
        events = []
        for soul in list(maya.souls.values()):
            if not soul.alive:
                continue
            if maya.karma_engine.should_die(soul, maya.tick):
                soul.alive = False
                maya.loka_manager.remove_soul(soul)

                events.append(Event(
                    tick=maya.tick,
                    event_type="death",
                    loka=soul.loka,
                    data={"soul_name": soul.name, "karma": soul.karma, "age": soul.age},
                    description=f"{soul.name} dies at age {soul.age} with karma {soul.karma}",
                ))

                # Samsara: rebirth
                old_loka = soul.loka
                maya.karma_engine.rebirth(soul)
                soul.alive = True
                maya.loka_manager.place_soul(soul)

                events.append(Event(
                    tick=maya.tick,
                    event_type="rebirth",
                    loka=soul.loka,
                    data={
                        "soul_name": soul.name, "new_karma": soul.karma,
                        "life_number": soul.lives, "from_loka": old_loka, "to_loka": soul.loka,
                    },
                    description=f"{soul.name} is reborn in {maya.loka_manager.get_loka(soul.loka).name} "
                                f"(life #{soul.lives}, karma: {soul.karma})",
                ))

        return events

    def pralaya(self, maya: Maya) -> list[Event]:
        """The great dissolution — end of a Mahayuga cycle."""
        events = [Event(
            tick=maya.tick,
            event_type="pralaya",
            data={"total_souls": len(maya.souls), "final_yuga": maya.yuga.value},
            description="PRALAYA: Shiva dances the Tandava — the universe dissolves",
        )]

        # Log final state of all souls
        for soul in maya.souls.values():
            events.append(Event(
                tick=maya.tick,
                event_type="pralaya_soul_record",
                loka=soul.loka,
                data={
                    "soul_name": soul.name, "final_karma": soul.karma,
                    "total_lives": soul.lives, "total_age": soul.lifetime,
                },
                description=f"  {soul.name}: karma={soul.karma}, lives={soul.lives}, lifetime={soul.lifetime}",
            ))

        return events
