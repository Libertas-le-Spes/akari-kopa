import io
import unittest
from email.message import Message
from unittest import mock

from akari_kopa.adapters.transport.https import Https
from akari_kopa.adapters.transport.https_guard import Destinations
from akari_kopa.use_cases.listing.ports import ServiceError

ALLOWED = frozenset({"api.example"})


def answer(content_type: str, body: bytes) -> mock.MagicMock:
    headers = Message()
    headers["Content-Type"] = content_type
    opened = mock.MagicMock()
    opened.__enter__.return_value.headers = headers
    opened.__enter__.return_value.read = io.BytesIO(body).read
    return opened


class HttpsTest(unittest.TestCase):
    def setUp(self):
        self.opener = mock.Mock()
        self.opener.open.return_value = answer("application/json", b'{"value": []}')
        self.https = Https("made-up-token", Destinations(ALLOWED), self.opener)

    def sent(self):
        self.assertEqual(self.opener.open.call_count, 1)
        return self.opener.open.call_args.args[0]

    def test_the_token_goes_in_a_header_that_is_never_copied_to_a_redirect(self):
        self.https.get("https://api.example/things", top="1")
        request = self.sent()
        self.assertEqual(request.unredirected_hdrs, {"Authorization": "Bearer made-up-token"})
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(request.full_url, "https://api.example/things?top=1")

    def test_a_body_is_posted_as_json(self):
        self.https.post("https://api.example/things", {"a": 1})
        self.assertEqual(self.sent().data, b'{"a": 1}')

    def test_nothing_is_sent_anywhere_but_https_to_an_allowed_host(self):
        for address in ("http://api.example/things", "https://elsewhere.example/things", "https://api.example:8443/things",
                        "https://someone@api.example/things"):
            with self.subTest(address), self.assertRaises(ServiceError):
                self.https.get(address)
        self.opener.open.assert_not_called()

    def test_an_answer_that_is_a_web_page_says_the_login_may_be_wrong(self):
        self.opener.open.return_value = answer("text/html", b"<html></html>")
        with self.assertRaises(ServiceError) as refused:
            self.https.get("https://api.example/things")
        self.assertIn("login may be wrong", refused.exception.reason)
