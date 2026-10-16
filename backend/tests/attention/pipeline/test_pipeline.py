import unittest

from merge_requests.attention.pipeline.pipeline import FAILED, NO_PIPELINE, PASSED, RUNNING, PipelineWords

WORDS = PipelineWords(frozenset({"ok", "skipped"}), frozenset({"broken"}))


class ReadingAServicesWords(unittest.TestCase):
    def test_what_each_set_of_states_means(self):
        cases = {
            (): NO_PIPELINE,
            (None,): NO_PIPELINE,
            ("ok",): PASSED,
            ("ok", "skipped"): PASSED,
            ("ok", "broken"): FAILED,
            ("ok", "queued"): RUNNING,
            ("queued", "broken"): FAILED,
        }
        for states, pipeline in cases.items():
            with self.subTest(states=states):
                self.assertEqual(WORDS.read(states), pipeline)

    def test_only_a_running_pipeline_is_drawn_as_running(self):
        self.assertEqual([pipeline.running for pipeline in (PASSED, FAILED, RUNNING, NO_PIPELINE)], [False, False, True, False])
