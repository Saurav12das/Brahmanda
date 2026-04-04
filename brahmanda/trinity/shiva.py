"""Shiva — The Destroyer, The Hard Reset.

Shiva is entropy itself. He breaks down what is corrupt, recycles
what is stale, and when the Mahayuga ends, triggers Pralaya.
Entropy now scales with population density — more souls = more chaos.
"""

from __future__ import annotations

from brahmanda.config import ACTIVE_LOKAS, LOKA_CONFIG, LAWS, YUGA_PARAMS, LokaID, YugaType
from brahmanda.db.models import Event, SoulState
from brahmanda.engine.maya import Maya


class ShivaProtocol:
    """Manages entropy, decay, and dissolution."""

    def apply_entropy(self, maya: Maya) -> list[Event]:
        """Apply entropy — scales with population density, not just yuga rate."""
        events = []
        base_entropy_rate = YUGA_PARAMS[maya.yuga]["entropy_rate"]

        for loka_id in ACTIVE_LOKAS:
            loka = maya.loka_manager.get_loka(loka_id)
            base_resources = LOKA_CONFIG[loka_id]["base_resources"]

            # Population density drives entropy (thermodynamics)
            population = len(loka.population)
            density_factor = population / max(1, base_resources / LAWS["shiva_entropy_density_divisor"])
            entropy_increase = base_entropy_rate * (1.0 + density_factor)

            maya.loka_manager.apply_entropy(loka_id, entropy_increase)

            # High entropy degrades resources (chaos destroys infrastructure)
            if loka.entropy > LAWS["shiva_decay_threshold"]:
                decay = int(loka.resources * LAWS["shiva_decay_rate"] * loka.entropy)
                loka.resources = max(0, loka.resources - decay)
                if decay > 0:
                    events.append(Event(
                        tick=maya.tick, event_type="shiva_decay", loka=loka_id,
                        data={"entropy": loka.entropy, "resource_decay": decay, "population": population},
                        description=f"Shiva's entropy erodes {loka.name}: {decay} resources decay (pop={population})",
                    ))

        return events

    def process_deaths(self, maya: Maya) -> list[Event]:
        """Check all living souls — death comes when prana is depleted."""
        events = []
        for soul in list(maya.souls.values()):
            if not soul.alive:
                continue
            if not maya.karma_engine.is_dead(soul):
                continue

            soul.alive = False
            maya.loka_manager.remove_soul(soul)

            cause = "starvation" if soul.resources <= 0 else "prana_depletion"
            events.append(Event(
                tick=maya.tick, event_type="death", loka=soul.loka,
                data={"soul_name": soul.name, "karma": soul.karma, "age": soul.age,
                      "cause": cause, "final_prana": 0.0},
                description=f"{soul.name} dies at age {soul.age} ({cause}, karma {soul.karma})",
            ))

            # Samsara: rebirth with mutation
            old_loka = soul.loka
            old_klesha = soul.klesha.model_dump()
            old_desires = list(soul.desires)
            old_skills = list(soul.skills)

            maya.karma_engine.rebirth(soul)
            soul.alive = True
            maya.loka_manager.place_soul(soul)

            # Inject cultural memory from birth loka (Akashic inheritance)
            birth_loka = maya.loka_manager.get_loka(soul.loka)
            maya.karma_engine.inject_akashic_memory(soul, birth_loka)

            new_klesha = soul.klesha.model_dump()
            vice_changes = {k: round(new_klesha[k] - old_klesha[k], 3)
                            for k in old_klesha if abs(new_klesha[k] - old_klesha[k]) > 0.001}
            desire_changes = set(soul.desires) != set(old_desires)
            skill_changes = set(soul.skills) != set(old_skills)

            mutation_desc = ""
            if vice_changes:
                mutations = [f"{k}:{d:+.2f}" for k, d in vice_changes.items()]
                mutation_desc += f" vices[{', '.join(mutations)}]"
            if desire_changes:
                new_d = set(soul.desires) - set(old_desires)
                lost_d = set(old_desires) - set(soul.desires)
                if new_d: mutation_desc += f" +desire:{list(new_d)[0]}"
                if lost_d: mutation_desc += f" -desire:{list(lost_d)[0]}"
            if skill_changes:
                new_s = set(soul.skills) - set(old_skills)
                lost_s = set(old_skills) - set(soul.skills)
                if new_s: mutation_desc += f" +skill:{list(new_s)[0]}"
                if lost_s: mutation_desc += f" -skill:{list(lost_s)[0]}"

            events.append(Event(
                tick=maya.tick, event_type="rebirth", loka=soul.loka,
                data={
                    "soul_name": soul.name, "new_karma": soul.karma,
                    "life_number": soul.lives, "from_loka": old_loka, "to_loka": soul.loka,
                    "vice_changes": vice_changes,
                    "desires_mutated": desire_changes, "skills_mutated": skill_changes,
                },
                description=f"{soul.name} is reborn in {maya.loka_manager.get_loka(soul.loka).name} "
                            f"(life #{soul.lives}, karma: {soul.karma})"
                            f"{' | MUTATION:' + mutation_desc if mutation_desc else ''}",
            ))

        return events

    def pralaya(self, maya: Maya) -> list[Event]:
        """The great dissolution — end of a Mahayuga cycle."""
        events = [Event(
            tick=maya.tick, event_type="pralaya",
            data={"total_souls": len(maya.souls), "final_yuga": maya.yuga.value},
            description="PRALAYA: Shiva dances the Tandava — the universe dissolves",
        )]
        for soul in maya.souls.values():
            events.append(Event(
                tick=maya.tick, event_type="pralaya_soul_record", loka=soul.loka,
                data={
                    "soul_name": soul.name, "final_karma": soul.karma,
                    "total_lives": soul.lives, "total_age": soul.lifetime,
                    "final_prana": round(soul.prana, 1),
                    "final_darkness": round(soul.klesha.total_darkness, 2),
                    "final_hope": round(soul.hope, 2),
                },
                description=f"  {soul.name}: karma={soul.karma}, lives={soul.lives}, "
                            f"prana={soul.prana:.0f}, darkness={soul.klesha.total_darkness:.2f}, "
                            f"hope={soul.hope:+.2f}",
            ))
        return events
