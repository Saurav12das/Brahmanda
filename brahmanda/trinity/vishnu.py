"""Vishnu — The Maintainer, The Admin who keeps the server running.

Vishnu monitors the universe's health and intervenes when critical
thresholds are breached. His intervention takes the form of Avatars —
special souls deployed with a specific mission to restore balance.
"""

from __future__ import annotations

import json
import re

from brahmanda.config import (
    AVATAR_DEPLOY_THRESHOLD,
    TRINITY_MODEL,
    VISHNU_CHECK_INTERVAL,
    LokaID,
)
from brahmanda.db.models import Event, SoulState, _uid
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
    """Monitors universe health and deploys avatars when needed."""

    def __init__(self, client: LLMClient) -> None:
        self.client = client
        self.avatars_deployed: int = 0

    def should_check(self, tick: int) -> bool:
        return tick > 0 and tick % VISHNU_CHECK_INTERVAL == 0

    async def evaluate(self, maya: Maya) -> list[Event]:
        """Evaluate universe health and potentially deploy an avatar."""
        events = []
        snapshot = maya.snapshot()

        # Quick heuristic check first
        living_souls = [s for s in maya.souls.values() if s.alive]
        if not living_souls:
            return events

        avg_karma = sum(s.karma for s in living_souls) / len(living_souls)
        max_entropy = max(l.entropy for l in maya.loka_manager.lokas.values())

        # Only call LLM if things look concerning
        if max_entropy < AVATAR_DEPLOY_THRESHOLD and avg_karma > -30:
            return events

        try:
            state_summary = (
                f"Tick: {snapshot.tick}, Yuga: {snapshot.yuga.value}\n"
                f"Living souls: {len(living_souls)}, Avg karma: {avg_karma:.1f}\n"
                f"Global entropy: {snapshot.global_entropy:.2f}\n"
                f"Lokas:\n"
            )
            for lid, loka in snapshot.lokas.items():
                state_summary += f"  {loka.name}: pop={len(loka.population)}, resources={loka.resources}, entropy={loka.entropy:.2f}\n"

            response = await self.client.generate(
                model=TRINITY_MODEL,
                system=VISHNU_SYSTEM,
                prompt=state_summary,
                max_tokens=500,
            )
            raw = response.text
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                return events

            result = json.loads(match.group())

            events.append(Event(
                tick=maya.tick,
                event_type="vishnu_assessment",
                data={"assessment": result.get("assessment", ""), "entropy": max_entropy},
                description=f"Vishnu assesses: {result.get('assessment', 'stable')[:100]}",
            ))

            if result.get("intervention_needed") and result.get("avatar"):
                avatar_data = result["avatar"]
                avatar = SoulState(
                    id=_uid(),
                    name=avatar_data.get("name", f"Avatar-{self.avatars_deployed + 1}"),
                    karma=100,
                    loka=LokaID(avatar_data.get("target_loka", 7)),
                    desires=["restore balance", avatar_data.get("mission", "preserve dharma")],
                    skills=["divine_power", "wisdom", "compassion"],
                    resources=50,
                    is_avatar=True,
                    avatar_mission=avatar_data.get("mission"),
                )
                maya.register_soul(avatar)
                self.avatars_deployed += 1

                events.append(Event(
                    tick=maya.tick,
                    event_type="avatar_deploy",
                    loka=avatar.loka,
                    data={"avatar_name": avatar.name, "mission": avatar.avatar_mission},
                    description=f"AVATAR DEPLOYED: {avatar.name} descends to {maya.loka_manager.get_loka(avatar.loka).name} — Mission: {avatar.avatar_mission}",
                ))

        except Exception:
            pass

        return events
