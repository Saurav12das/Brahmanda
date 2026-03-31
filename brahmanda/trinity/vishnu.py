"""Vishnu — The Maintainer, The Admin who keeps the server running.

Vishnu monitors the universe's health and intervenes when conditions
demand it — not on a fixed schedule. Avatar deployment is governed
by resource availability, not arbitrary caps.
"""

from __future__ import annotations

import json
import re

from brahmanda.config import LOKA_CONFIG, TRINITY_MODEL, LokaID
from brahmanda.db.models import Event, Klesha, SoulState, _uid
from brahmanda.engine.maya import Maya
from brahmanda.llm import LLMClient


VISHNU_SYSTEM = """\
You are Vishnu, the Preserver of the universe Brahmanda.
You monitor the simulation for instability and decide whether intervention is needed.

When you deploy an Avatar, it is a soul with extraordinary karma and a clear mission.
The Avatar Protocol is a last resort — you prefer the universe to self-correct.

Analyze the universe state and respond with ONLY valid JSON:
{
  "assessment": "<brief diagnosis of universe health>",
  "intervention_needed": true/false,
  "avatar": {
    "name": "<avatar name>",
    "mission": "<what the avatar must accomplish>",
    "target_loka": 7
  } or null
}
"""


class VishnuProtocol:
    """Event-driven universe health monitor. No fixed intervals, no arbitrary caps."""

    def __init__(self, client: LLMClient) -> None:
        self.client = client
        self.avatars_deployed: int = 0
        self._last_check_tick: int = -100  # cooldown tracker

    def should_intervene(self, maya: Maya) -> bool:
        """Check based on CONDITIONS, not a timer."""
        # Cooldown: don't check more than once every 20 ticks
        if maya.tick - self._last_check_tick < 20:
            return False

        living = [s for s in maya.souls.values() if s.alive]
        if not living:
            return False

        # Condition 1: Any soul critically low on prana (starvation crisis)
        starving = any(s.prana < 10 for s in living)

        # Condition 2: Average karma below yuga-scaled threshold
        avg_karma = sum(s.karma for s in living) / len(living)
        karma_thresholds = {"satya": -10, "treta": -25, "dvapara": -40, "kali": -60}
        karma_crisis = avg_karma < karma_thresholds.get(maya.yuga.value, -30)

        # Condition 3: Any loka entropy dangerously high
        entropy_crisis = any(
            maya.loka_manager.get_loka(lid).entropy > 0.85
            for lid in maya.loka_manager.lokas
        )

        return starving or karma_crisis or entropy_crisis

    async def evaluate(self, maya: Maya) -> list[Event]:
        """Evaluate universe health and potentially deploy an avatar."""
        self._last_check_tick = maya.tick
        events = []
        snapshot = maya.snapshot()

        living_souls = [s for s in maya.souls.values() if s.alive]
        if not living_souls:
            return events

        avg_karma = sum(s.karma for s in living_souls) / len(living_souls)

        # Resource availability check — can the universe sustain another soul?
        total_resources = sum(l.resources for l in maya.loka_manager.lokas.values())
        resources_per_soul = total_resources / max(1, len(living_souls))
        can_sustain_more = resources_per_soul > 5

        try:
            state_summary = (
                f"Tick: {snapshot.tick}, Yuga: {snapshot.yuga.value}\n"
                f"Living souls: {len(living_souls)}, Avg karma: {avg_karma:.1f}\n"
                f"Resources per soul: {resources_per_soul:.1f}\n"
                f"Global entropy: {snapshot.global_entropy:.2f}\n"
                f"Lokas:\n"
            )
            for lid, loka in snapshot.lokas.items():
                avg_prana = sum(maya.souls[sid].prana for sid in loka.population if sid in maya.souls) / max(1, len(loka.population))
                state_summary += f"  {loka.name}: pop={len(loka.population)}, resources={loka.resources}, entropy={loka.entropy:.2f}, avg_prana={avg_prana:.0f}\n"

            if not can_sustain_more:
                state_summary += "\nWARNING: Resources too scarce to sustain another soul. Do NOT deploy an avatar.\n"

            response = await self.client.generate(
                model=TRINITY_MODEL, system=VISHNU_SYSTEM,
                prompt=state_summary, max_tokens=500,
            )
            raw = response.text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                return events

            result = json.loads(match.group())

            events.append(Event(
                tick=maya.tick, event_type="vishnu_assessment",
                data={"assessment": result.get("assessment", ""), "resources_per_soul": resources_per_soul},
                description=f"Vishnu assesses: {result.get('assessment', 'stable')[:100]}",
            ))

            # Deploy avatar only if resources can sustain it
            if result.get("intervention_needed") and result.get("avatar") and can_sustain_more:
                avatar_data = result["avatar"]
                avatar = SoulState(
                    id=_uid(),
                    name=avatar_data.get("name", f"Avatar-{self.avatars_deployed + 1}"),
                    karma=100,
                    loka=LokaID(avatar_data.get("target_loka", 7)),
                    desires=["restore balance", avatar_data.get("mission", "preserve dharma")],
                    skills=["divine_power", "wisdom", "compassion"],
                    resources=50,
                    prana=100.0,
                    klesha=Klesha(kama=0.1, krodha=0.1, lobha=0.1, moha=0.1, ahamkara=0.1),
                    is_avatar=True,
                    avatar_mission=avatar_data.get("mission"),
                )
                maya.register_soul(avatar)
                self.avatars_deployed += 1

                events.append(Event(
                    tick=maya.tick, event_type="avatar_deploy", loka=avatar.loka,
                    data={"avatar_name": avatar.name, "mission": avatar.avatar_mission,
                          "resources_per_soul": resources_per_soul},
                    description=f"AVATAR DEPLOYED: {avatar.name} descends — Mission: {avatar.avatar_mission}",
                ))

        except Exception:
            pass

        return events
