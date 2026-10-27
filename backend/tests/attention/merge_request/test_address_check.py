import unittest

from akari_kopa.attention.merge_request.address_check import address_of
from akari_kopa.attention.merge_request.web_address import RefusedAddress, WebAddress

HOST = "forge.example"

HOSTILE = {
    "file:///home/someone/.ssh/id_ed25519": "only https addresses are opened",
    "--help": "only https addresses are opened",
    "javascript:alert(1)": "only https addresses are opened",
    "smb://203.0.113.9/share": "only https addresses are opened",
    "example-scheme://do?x=1": "only https addresses are opened",
    "http://forge.example/team/app/1": "only https addresses are opened",
    "https://forge.example.attacker.example/team/app/1": "the address does not point to forge.example",
    "https://attacker.example/forge.example/1": "the address does not point to forge.example",
    "https://someone:secret@forge.example/1": "the address carries a user name or password",
    "https://forge.example/team app/1": "the address holds a space, a backslash or a hidden character",
    "https://forge.example/1\n": "the address holds a space, a backslash or a hidden character",
    "https:\\\\attacker.example/1": "the address holds a space, a backslash or a hidden character",
    "https://forge.example/‮exe.1": "the address holds a space, a backslash or a hidden character",
    "": "the forge gave no address that can be opened",
}


class AddressCheck(unittest.TestCase):
    def test_a_page_on_the_forge_asked_can_be_opened(self):
        self.assertEqual(address_of("https://forge.example/team/app/1", HOST), WebAddress("https://forge.example/team/app/1", HOST))

    def test_the_host_is_compared_without_regard_to_case(self):
        self.assertIsInstance(address_of("https://Forge.Example/team/app/1", HOST), WebAddress)

    def test_every_hostile_address_is_refused_and_says_why(self):
        for text, reason in HOSTILE.items():
            with self.subTest(text):
                self.assertEqual(address_of(text, HOST), RefusedAddress(reason, HOST))


class Opening(unittest.TestCase):
    def setUp(self):
        self.opened = []

    def test_an_address_that_was_checked_is_handed_to_the_opener(self):
        address = WebAddress("https://forge.example/1", HOST)
        address.open_with(self.opened.append)
        self.assertEqual(self.opened, [address])

    def test_a_refused_address_opens_nothing_and_its_note_says_why(self):
        refused = RefusedAddress("only https addresses are opened", HOST)
        refused.open_with(self.opened.append)
        self.assertEqual((self.opened, refused.notes()), ([], ["not opened: only https addresses are opened"]))

    def test_a_refused_address_keeps_no_text_that_could_be_opened(self):
        self.assertEqual(address_of("file:///etc/passwd", HOST).text, "")
