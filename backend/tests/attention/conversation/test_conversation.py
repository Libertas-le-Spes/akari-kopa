import unittest

from merge_requests.attention.conversation.conversation import QUIET, Conversation
from tests.fakes import on_day


class WaitingSince(unittest.TestCase):
    def test_nobody_said_anything(self):
        self.assertIsNone(QUIET.waiting_since())

    def test_a_comment_after_my_last_answer_waits_for_me(self):
        self.assertEqual(Conversation(comments=(on_day(2),), last_answer=on_day(1)).waiting_since(), on_day(2))

    def test_a_comment_i_answered_waits_no_longer(self):
        self.assertIsNone(Conversation(comments=(on_day(2),), last_answer=on_day(3)).waiting_since())

    def test_an_unresolved_thread_waits_until_it_is_resolved_however_i_answered(self):
        self.assertEqual(Conversation(unresolved_threads=(on_day(2),), last_answer=on_day(3)).waiting_since(), on_day(2))

    def test_it_waits_since_the_oldest_thing_still_open(self):
        conversation = Conversation(unresolved_threads=(on_day(5),), comments=(on_day(1), on_day(4)), last_answer=on_day(3))
        self.assertEqual(conversation.waiting_since(), on_day(4))
