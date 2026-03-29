"""SQLite persistence layer — Akashic Records of Brahmanda."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from brahmanda.config import DB_PATH
from brahmanda.db.models import Action, Event, SoulState, UniverseSnapshot


class AkashicRecords:
    """Persistent storage for the universe's history."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                loka INTEGER,
                data TEXT NOT NULL DEFAULT '{}',
                description TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                soul_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_id TEXT,
                description TEXT NOT NULL DEFAULT '',
                karma_delta INTEGER NOT NULL DEFAULT 0,
                loka INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS soul_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                soul_id TEXT NOT NULL,
                soul_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER NOT NULL,
                snapshot_json TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_events_tick ON events(tick);
            CREATE INDEX IF NOT EXISTS idx_actions_soul ON actions(soul_id);
            CREATE INDEX IF NOT EXISTS idx_soul_history_id ON soul_history(soul_id);
        """)
        self.conn.commit()

    def log_event(self, event: Event) -> None:
        self.conn.execute(
            "INSERT INTO events (tick, event_type, loka, data, description) VALUES (?, ?, ?, ?, ?)",
            (event.tick, event.event_type, event.loka, json.dumps(event.data), event.description),
        )
        self.conn.commit()

    def log_action(self, action: Action) -> None:
        self.conn.execute(
            "INSERT INTO actions (tick, soul_id, action_type, target_id, description, karma_delta, loka) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (action.tick, action.soul_id, action.action_type, action.target_id,
             action.description, action.karma_delta, action.loka),
        )
        self.conn.commit()

    def log_soul_state(self, tick: int, soul: SoulState) -> None:
        self.conn.execute(
            "INSERT INTO soul_history (tick, soul_id, soul_json) VALUES (?, ?, ?)",
            (tick, soul.id, soul.model_dump_json()),
        )
        self.conn.commit()

    def save_snapshot(self, snapshot: UniverseSnapshot) -> None:
        self.conn.execute(
            "INSERT INTO snapshots (tick, snapshot_json) VALUES (?, ?)",
            (snapshot.tick, snapshot.model_dump_json()),
        )
        self.conn.commit()

    def get_soul_karma_trajectory(self, soul_id: str) -> list[tuple[int, int]]:
        rows = self.conn.execute(
            "SELECT tick, json_extract(soul_json, '$.karma') as karma "
            "FROM soul_history WHERE soul_id = ? ORDER BY tick",
            (soul_id,),
        ).fetchall()
        return [(r["tick"], r["karma"]) for r in rows]

    def get_events_by_type(self, event_type: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM events WHERE event_type = ? ORDER BY tick",
            (event_type,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_actions(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM actions ORDER BY tick").fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        self.conn.close()
