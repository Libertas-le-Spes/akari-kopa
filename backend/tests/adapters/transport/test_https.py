import unittest

from akari_kopa.adapters.transport.https import Https


class HttpsTest(unittest.TestCase):
    def test_a_key_is_sent_as_basic_credentials(self):
        self.assertEqual(Https.basic("", "me@example.com:key").authorization, "Basic bWVAZXhhbXBsZS5jb206a2V5")

    def test_a_login_token_is_sent_as_a_bearer_token(self):
        self.assertEqual(Https.bearer("", "token").authorization, "Bearer token")
