from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import json

from .models import RunState, transition
from contextlib import contextmanager

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

class StateStore:
    def __init__(self, db_path: Path | str):
        self.db_path = str(db_path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        Connection = sqlite3.connect(self.db_path)
        Connection.row_factory = sqlite3.Row
        return Connection

    @contextmanager
    def _connection(self):
        Connection = self._connect()

        try:
            yield Connection
            Connection.commit()
        except Exception:
            Connection.rollback()
            raise
        finally:
            Connection.close()

    def _init_schema(self) -> None:
        with self._connection() as connection:
            connection.execute(

                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                    )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_run_id
                ON events(run_id, id)
                """
            )

    def create_run(
            self,
            run_id: str,
            project_name: str,
    ) -> None:
        now = utc_now()

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO runs (
                    id,
                    project_name,
                    state,
                    created_at,
                    updated_at
                )
                VALUES (?,?,?,?,?)
                """,

                (
                    run_id,
                    project_name,
                    RunState.DRAFT.value,
                    now,
                    now,
                ),
            )

    def get_run(self, run_id: str) -> dict | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM runs WHERE id = ?",
                (run_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)
            

    def transition_run(
            self,
            run_id: str,
            target: RunState,
    ) -> dict:
        run = self.get_run(run_id)

        if run is None:
            raise ValueError(f"Run not found: {run_id}")

        current = RunState(run["state"])
        next_state = transition(current, target)
        now = utc_now()

        with self._connection() as connection:
            connection.execute(
                """
                UPDATE runs
                SET state = ?, updated_at = ?
                WHERE id = ?

                """,
                (
                    next_state.value,
                    now,
                    run_id,
                ),
            )

        updated_run = self.get_run(run_id)

        if updated_run is None:
            raise RuntimeError(
                f"Run disappeared after transition: {run_id}"
            )

        return updated_run

    def add_event(
            self,
            run_id: str,
            event: dict,
    ) -> int:
        if self.get_run(run_id) is None:
            raise ValueError(f"Run not found: {run_id}")

        stored_event = dict(event)
        stored_event.setdefault("timestamp", utc_now())

        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO events (
                    run_id,
                    event_json,
                    created_at
                )
                VALUES (?, ?, ?)
                """,
                (
                    run_id,
                    json.dumps(stored_event),
                    utc_now(),
                ),
            )

            event_id = cursor.lastrowid

        return int(event_id)

    def get_events(
            self,
            run_id: str,
            after_id: int = 0,
    ) -> list[dict]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT id, event_json
                FROM events
                WHERE run_id = ? AND id > ?
                ORDER BY id
                """,
                (
                    run_id,
                    after_id,
                ),
            ).fetchall()

        events = []

        for row in rows:
            event = json.loads(row["event_json"])
            event["event_id"] = row["id"]
            events.append(event)

        return events