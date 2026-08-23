import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from deployment_agent.state import StateStore

class EventHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "state.db"
        self.store = StateStore(database_path)

        self.store.create_run(
            run_id="run-events",
            project_name="event-demo"
        )

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_events_are_returned_in_order(self):
        first_id = self.store.add_event(
            "run-events",
            {
                "stage": "analysis",
                "status": "running",
                "message": "Analysis started",
            },
        )

        second_id = self.store.add_event(
            "run-events",
            {
                "stage": "analysis",
                "status": "complete",
                "message": "Analysis completed",
            },
        )

        events = self.store.get_events("run-events")

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["event_id"], first_id)
        self.assertEqual(events[1]["event_id"], second_id)
        self.assertEqual(events[0]["status"], "running")
        self.assertEqual(events[1]["status"], "complete")
        self.assertIn("timestamp", events[0])

    def test_after_id_returns_only_new_events(self):
        first_id = self.store.add_event(
            "run-events",
            {
                "stage":"build",
                "status":"running",
                "message":"Build started",
            },
        )

        second_id = self.store.add_event(
            "run-events",
            {
                "stage":"build",
                "status":"complete",
                "message":"Build completed",
            },
        )

        events = self.store.get_events(
            "run-events",
            after_id= first_id,
        )

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_id"], second_id)

    def test_unknown_run_cannot_receive_event(self):
        with self.assertRaisesRegex(
            ValueError,
            "Run not found: missing-run",
        ):
            self.store.add_event(
                "missing-run",
                {
                    "stage": "analysis",
                    "status": "running",
                    "message": "Should not be stored",
                },
            )

    def test_after_latest_event_returns_empty_list(self):
        latest_id = self.store.add_event(
            "run-events",
            {
                "stage": "analysis",
                "status": "complete",
                "message": "Analysis completed",
            },
        )

        events = self.store.get_events(
            "run-events",
            after_id=latest_id,
        )

        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
