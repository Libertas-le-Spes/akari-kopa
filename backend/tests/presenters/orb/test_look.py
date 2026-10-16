import unittest

from akari_kopa.attention.merge_request.role import MINE, REVIEWING
from akari_kopa.attention.pipeline.pipeline import FAILED, NO_PIPELINE, PASSED, RUNNING
from akari_kopa.presenters.orb.look import BLUE, GREEN, PURPLE, RED, YELLOW, look_of, word_of
from akari_kopa.presenters.orb.pixmap import pixmaps
from tests.fakes import a_merge_request, commented_on


class Looks(unittest.TestCase):
    def test_what_each_of_my_merge_requests_looks_like(self):
        cases = [
            (NO_PIPELINE, False, GREEN, False, "no pipeline"),
            (NO_PIPELINE, True, PURPLE, False, "comments to answer"),
            (PASSED, False, GREEN, False, "passing"),
            (PASSED, True, PURPLE, False, "comments to answer"),
            (RUNNING, False, GREEN, True, "running"),
            (RUNNING, True, PURPLE, True, "comments to answer"),
            (FAILED, True, RED, False, "failing"),
        ]
        for pipeline, commented, colour, ring, word in cases:
            with self.subTest(pipeline=pipeline.name, commented=commented):
                found = a_merge_request(pipeline=pipeline, conversation=commented_on(1) if commented else a_merge_request().conversation)
                self.assertEqual((look_of(found, False).colour, look_of(found, False).ring, word_of(found)), (colour, ring, word))

    def test_one_i_review_is_blue_or_yellow(self):
        self.assertEqual(look_of(a_merge_request(role=REVIEWING, pipeline=PASSED), False).colour, BLUE)
        self.assertEqual(look_of(a_merge_request(role=REVIEWING, pipeline=FAILED), False).colour, YELLOW)


class Pixmaps(unittest.TestCase):
    def test_a_ring_is_empty_in_the_middle_and_filled_at_the_edge(self):
        smallest = pixmaps(look_of(a_merge_request(pipeline=RUNNING, conversation=commented_on(1)), False))[0]
        middle, edge = (8 * 16 + 8) * 4, (8 * 16 + 3) * 4
        self.assertEqual(smallest.argb[middle], 0)
        self.assertEqual(smallest.argb[edge:edge + 4], bytes([255]) + bytes.fromhex(PURPLE[1:]))

    def test_a_faded_orb_is_see_through(self):
        faded = pixmaps(look_of(a_merge_request(), True))[0]
        self.assertLess(faded.argb[(8 * 16 + 8) * 4], 255)
