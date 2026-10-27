import json
import unittest
from unittest import mock

from akari_kopa.adapters.storage.answer_folder import AnswerFolder
from akari_kopa.adapters.storage.folder_check import FolderRefused
from akari_kopa.adapters.storage.merge_request_codec import encoded
from akari_kopa.attention.conversation.conversation import Conversation
from akari_kopa.attention.merge_request.role import REVIEWING
from akari_kopa.attention.merge_request.web_address import RefusedAddress
from akari_kopa.attention.pipeline.pipeline import RUNNING
from akari_kopa.attention.repository.follow_up import SOMEONE_ELSES
from tests.fakes import a_merge_request, on_day


def kept_text(*merge_requests) -> str:
    raw = []
    for merge_request in merge_requests:
        raw.append(encoded(merge_request))
    return json.dumps({"given": on_day(4).isoformat(), "mergeRequests": raw})


class AnswerFolderTest(unittest.TestCase):
    def setUp(self):
        self.folder = mock.Mock()

    def test_an_answer_is_written_whole_under_its_service_name(self):
        kept = a_merge_request(role=REVIEWING, pipeline=RUNNING, repository=SOMEONE_ELSES,
                               conversation=Conversation((on_day(1),), (on_day(2),), on_day(3)))
        AnswerFolder(self.folder).keep("forge", [kept], on_day(4))
        self.folder.write.assert_called_once_with("forge.json", kept_text(kept))

    def test_an_answer_comes_back_as_it_was_kept(self):
        kept = a_merge_request(conversation=Conversation((on_day(1),), (on_day(2),), on_day(3)))
        self.folder.read.return_value = kept_text(kept)
        last = AnswerFolder(self.folder).last("forge")
        self.folder.read.assert_called_once_with("forge.json")
        self.assertEqual((last.merge_requests, last.given), ([kept], on_day(4)))

    def test_a_hostile_address_planted_in_the_cache_is_checked_again_and_refused(self):
        raw = encoded(a_merge_request())
        raw["address"] = "file:///home/someone/.ssh/id_ed25519"
        self.folder.read.return_value = json.dumps({"given": on_day(4).isoformat(), "mergeRequests": [raw]})
        address = AnswerFolder(self.folder).last("forge").merge_requests[0].address
        self.assertEqual(address, RefusedAddress("only https addresses are opened", "forge.example"))

    def test_an_answer_kept_before_addresses_were_checked_is_not_used(self):
        raw = encoded(a_merge_request())
        raw["url"] = raw.pop("address")
        self.folder.read.return_value = json.dumps({"given": on_day(4).isoformat(), "mergeRequests": [raw]})
        self.assertIsNone(AnswerFolder(self.folder).last("forge"))

    def test_nothing_kept_a_damaged_file_or_a_refused_folder_means_no_answer(self):
        for problem in (FileNotFoundError(), FolderRefused("belongs to another account")):
            with self.subTest(type(problem).__name__):
                self.folder.read.side_effect = problem
                self.assertIsNone(AnswerFolder(self.folder).last("forge"))
        self.folder.read.side_effect = None
        self.folder.read.return_value = "{half"
        self.assertIsNone(AnswerFolder(self.folder).last("forge"))

    def test_a_refused_folder_keeps_nothing_and_the_board_goes_on(self):
        self.folder.write.side_effect = FolderRefused("belongs to another account")
        with mock.patch("sys.stderr"):
            AnswerFolder(self.folder).keep("forge", [], on_day(4))
        self.assertEqual(self.folder.write.call_count, 1)
