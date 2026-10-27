import unittest

from tests.source_files import PACKAGE, files_saying

SENDERS = ["backend/akari_kopa/adapters/transport/https.py", "backend/akari_kopa/adapters/transport/https_guard.py"]


class Network(unittest.TestCase):
    def test_only_the_guarded_transport_sends_requests_itself(self):
        self.assertEqual(files_saying("urllib.request", PACKAGE, "*.py"), SENDERS)

    def test_the_token_is_only_ever_set_as_a_header_kept_from_redirects(self):
        self.assertEqual(files_saying("Authorization", PACKAGE, "*.py"), ["backend/akari_kopa/adapters/transport/https.py"])
        self.assertEqual(files_saying("add_unredirected_header", PACKAGE, "*.py"), ["backend/akari_kopa/adapters/transport/https.py"])
