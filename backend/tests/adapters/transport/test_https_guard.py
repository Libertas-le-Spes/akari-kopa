import unittest
import urllib.request
from unittest import mock

from akari_kopa.adapters.transport.https_guard import RedirectRefused, without_redirects
from akari_kopa.use_cases.listing.ports import ServiceError


class Redirects(unittest.TestCase):
    def test_a_redirect_is_refused_rather_than_followed(self):
        request = urllib.request.Request("https://api.example/things")
        with self.assertRaises(ServiceError) as refused:
            RedirectRefused().redirect_request(request, None, 302, "Found", {}, "https://elsewhere.example/")
        self.assertEqual(refused.exception.reason, "api.example sent the request elsewhere (302); it was not followed")

    def test_the_opener_is_built_with_the_refusing_redirect_handler_only(self):
        with mock.patch("urllib.request.build_opener") as build_opener:
            without_redirects()
        build_opener.assert_called_once_with(RedirectRefused)
