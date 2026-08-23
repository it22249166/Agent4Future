import unittest

from deployment_agent.models import RunState, transition

class StateMachineTests(unittest.TestCase):

    def test_draft_can_start_analysis(self):
        result = transition(
            RunState.DRAFT,
            RunState.ANALYZING,
        )

        self.assertEqual(result, RunState.ANALYZING)

    def test_analysis_can_become_review_ready(self):
        result = transition(
            RunState.ANALYZING,
            RunState.REVIEW_READY,
        )
        self.assertEqual(result, RunState.REVIEW_READY)

    def test_draft_cannot_jump_directly_to_live(self):
        with self.assertRaisesRegex(
            ValueError,
            "DRAFT -> LIVE",
        ):
            transition(
                RunState.DRAFT,
                RunState.LIVE,
            )

    def test_destroyed_is_a_terminal_state(self):
        with self.assertRaises(ValueError):
            transition(
                RunState.DESTROYED,
                RunState.DRAFT,
            )

    def test_same_state_is_idempotent(self):
        result = transition(
            RunState.DEPLOYING,
            RunState.DEPLOYING,
        )
        self.assertEqual(result, RunState.DEPLOYING)

    def test_state_values_match_api_contract(self):
        expected = {
            "DRAFT": "DRAFT",
            "ANALYZING": "ANALYZING",
            "REVIEW_READY": "REVIEW_READY",
            "BOOTSTRAPPING": "BOOTSTRAPPING",
            "CI_RUNNING": "CI_RUNNING",
            "DEPLOYING": "DEPLOYING",
            "VALIDATING": "VALIDATING",
            "LIVE": "LIVE",
            "FAILED": "FAILED",
            "ROLLED_BACK": "ROLLED_BACK",
            "CANCELLED": "CANCELLED",
            "DESTROYED": "DESTROYED",
        }

        actual = {
            state.name: state.value
            for state in RunState
        }

        self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()