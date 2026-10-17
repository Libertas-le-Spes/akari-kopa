import unittest

from akari_kopa.adapters.transport.https import Https


class HttpsTest(unittest.TestCase):
    def test_a_login_token_is_sent_as_a_bearer_token(self):
        self.assertEqual(Https("", "token").authorization, "Bearer token")
