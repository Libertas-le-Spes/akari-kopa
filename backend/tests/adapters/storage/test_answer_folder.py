import tempfile
import unittest
from pathlib import Path

from merge_requests.adapters.storage.answer_folder import AnswerFolder
from merge_requests.attention.conversation.conversation import Conversation
from merge_requests.attention.merge_request.role import REVIEWING
from merge_requests.attention.pipeline.pipeline import RUNNING
from merge_requests.attention.repository.follow_up import SOMEONE_ELSES
from tests.fakes import a_merge_request, on_day


class AnswerFolderTest(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp()) / "answers"

    def test_an_answer_comes_back_as_it_was_kept(self):
        kept = a_merge_request(role=REVIEWING, pipeline=RUNNING, repository=SOMEONE_ELSES,
                               conversation=Conversation((on_day(1),), (on_day(2),), on_day(3)))
        AnswerFolder(self.folder).keep("forge", [kept], on_day(4))
        last = AnswerFolder(self.folder).last("forge")
        self.assertEqual((last.merge_requests, last.given), ([kept], on_day(4)))

    def test_nothing_kept_yet_or_a_damaged_file_means_no_answer(self):
        self.assertIsNone(AnswerFolder(self.folder).last("forge"))
        self.folder.mkdir(parents=True)
        (self.folder / "forge.json").write_text("{half")
        self.assertIsNone(AnswerFolder(self.folder).last("forge"))

    def test_only_i_can_read_what_is_kept(self):
        AnswerFolder(self.folder).keep("forge", [], on_day(1))
        self.assertEqual((self.folder / "forge.json").stat().st_mode & 0o777, 0o600)
