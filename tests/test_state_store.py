import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from deployment_agent.models import RunState
from deployment_agent.state import StateStore

class StateStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_directory = TemporaryDirectory()
        database_path = Path(self.temp_directory.name) / "state.db"
        self.store = StateStore(database_path)

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_create_and_get_run(self):
        self.store.create_run(
            run_id="run-001",
            project_name="my-web-app",
        )

        run = self.store.get_run("run-001")

        self.assertIsNotNone(run)
        self.assertEqual(run["id"], "run-001")
        self.assertEqual(run["project_name"], "my-web-app")
        self.assertEqual(run["state"], "DRAFT")
        self.assertEqual(run["error"],"")

    def test_unknown_run_returns_none(self):
        run = self.store.get_run("missing-run")

        self.assertIsNone(run)

    def test_valid_transactions_is_saved(self):
        self.store.create_run(
            run_id="run-002",
            project_name="shop-app",
        )

        updated_run = self.store.transition_run(
            "run-002",
            RunState.ANALYZING
        )

        self.assertEqual(updated_run["state"], "ANALYZING")

        saved_run = self.store.get_run("run-002")
        self.assertEqual(saved_run["state"], "ANALYZING")
    
    def test_invalid_transition_does_not_change_database(self):
        self.store.create_run (
            run_id="run-003",
            project_name="blog-app",
        )

        with self.assertRaisesRegex(
            ValueError,
            "DRAFT -> LIVE",
        ):
            self.store.transition_run(
                "run-003",
                RunState.LIVE,
            )

        saved_run = self.store.get_run("run-003")
        self.assertEqual(saved_run["state"], "DRAFT")

    def test_transitioning_unknown_run_raises_error(self):
        with self.assertRaisesRegex(
            ValueError,
            "Run not found: missing-run",
        ):
            self.store.transition_run(
                "missing-run",
                RunState.ANALYZING,
            )

if __name__ == "__main__":
    unittest.main()