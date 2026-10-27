import unittest
from unittest import mock

from akari_kopa.adapters.services.azure_devops.connection import azure_connection
from akari_kopa.adapters.services.azure_devops.places import pull_request_api

PLACE = "akari_kopa.adapters.services.azure_devops.connection"


class Connection(unittest.TestCase):
    def test_the_token_may_go_only_to_the_two_azure_devops_hosts_and_never_follows_a_redirect(self):
        with mock.patch(f"{PLACE}.Https") as https, mock.patch(f"{PLACE}.Destinations") as destinations, \
                mock.patch(f"{PLACE}.without_redirects") as without_redirects:
            azure_connection("made-up-token")
        destinations.assert_called_once_with(frozenset({"dev.azure.com", "app.vssps.visualstudio.com"}))
        https.assert_called_once_with("made-up-token", destinations.return_value, without_redirects.return_value)


class Places(unittest.TestCase):
    def test_every_part_the_server_gave_is_escaped_so_it_cannot_change_the_path(self):
        pull_request = {"pullRequestId": 7, "repository": {"id": "../../x?y", "project": {"id": "p/1#"}}}
        self.assertEqual(pull_request_api("con toso", pull_request),
                         "https://dev.azure.com/con%20toso/p%2F1%23/_apis/git/repositories/..%2F..%2Fx%3Fy/pullRequests/7")
