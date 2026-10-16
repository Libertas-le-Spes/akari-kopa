import unittest

from merge_requests.attention.merge_request.merge_request import COMMENTS
from merge_requests.attention.pipeline.pipeline import FAILED, NO_PIPELINE, PASSED, RUNNING
from tests.fakes import a_merge_request, commented_on


class Standing(unittest.TestCase):
    def test_comments_waiting_outrank_every_pipeline_but_a_failed_one(self):
        cases = {
            (NO_PIPELINE, False): NO_PIPELINE.name,
            (NO_PIPELINE, True): COMMENTS,
            (PASSED, False): PASSED.name,
            (PASSED, True): COMMENTS,
            (RUNNING, False): RUNNING.name,
            (RUNNING, True): COMMENTS,
            (FAILED, False): FAILED.name,
            (FAILED, True): FAILED.name,
        }
        for (pipeline, commented), standing in cases.items():
            with self.subTest(pipeline=pipeline.name, commented=commented):
                conversation = commented_on(1) if commented else a_merge_request().conversation
                self.assertEqual(a_merge_request(pipeline=pipeline, conversation=conversation).standing(), standing)
