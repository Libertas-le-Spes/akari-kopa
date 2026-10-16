import unittest

from akari_kopa.attention.conversation.conversation import QUIET, Conversation
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES
from tests.fakes import OPENED, on_day

DAYS = (1, 2, 3, 4, 4.5, 5, 6, 7, 10, 14, 20, 21, 28, 29.9, 30, 30.9, 31, 40)


def shown_on(comment_day: float | None) -> list[float]:
    def conversation_on(day: float) -> Conversation:
        posted = comment_day is not None and comment_day <= day
        return Conversation(comments=(on_day(comment_day),)) if posted else QUIET
    return [day for day in DAYS if SOMEONE_ELSES.keeps_on_the_bar(OPENED, conversation_on(day), on_day(day))]


class FollowingSomeoneElsesRepository(unittest.TestCase):
    def test_it_shows_for_three_days_and_then_rests_when_nobody_comments(self):
        self.assertEqual(shown_on(None), [1, 2])

    def test_a_comment_during_the_first_days_keeps_it_until_day_31(self):
        self.assertEqual(shown_on(1), [1, 2, 3, 4, 4.5, 5, 6, 7, 10, 14, 20, 21, 28, 29.9, 30, 30.9])

    def test_a_comment_is_found_on_days_5_and_7_then_weekly(self):
        self.assertEqual(shown_on(4)[:3], [1, 2, 5])
        self.assertEqual(shown_on(6)[:3], [1, 2, 7])
        self.assertEqual(shown_on(9)[:3], [1, 2, 14])
        self.assertEqual(shown_on(22)[:3], [1, 2, 28])

    def test_a_comment_after_the_last_check_is_never_shown(self):
        self.assertEqual(shown_on(29), [1, 2])

    def test_my_own_repository_is_always_shown(self):
        self.assertTrue(all(OWN.keeps_on_the_bar(OPENED, QUIET, on_day(day)) for day in DAYS))
