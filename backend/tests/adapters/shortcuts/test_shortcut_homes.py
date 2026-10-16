import tempfile
import unittest
from pathlib import Path

from akari_kopa.adapters.shortcuts.cinnamon import Cinnamon
from akari_kopa.adapters.shortcuts.environment import Environment
from akari_kopa.adapters.shortcuts.gnome import PATH, Gnome
from akari_kopa.adapters.shortcuts.gsettings import GSettings
from akari_kopa.adapters.shortcuts.hyprland import HyprlandConf, HyprlandLua, Omarchy
from akari_kopa.adapters.shortcuts.kde import Kde
from akari_kopa.adapters.shortcuts.mate import Mate
from akari_kopa.adapters.shortcuts.sway import Sway
from akari_kopa.adapters.shortcuts.xfce import Xfce
from tests.fakes import FakeCommandLine

CHOOSE = "/opt/akari-kopa/backend/bin/akari-kopa choose"


def environment(*desktops: str) -> Environment:
    home = Path(tempfile.mkdtemp())
    return Environment(frozenset(desktops), home / ".config", home / ".local" / "share")


def config(environment: Environment, relative: str, text: str = "existing = true\n") -> Path:
    path = environment.config_home / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


class ConfigFileDesktops(unittest.TestCase):
    def test_each_writes_its_own_line_once_reloads_and_takes_it_out_again(self):
        cases = [
            (Omarchy, "hypr/bindings.lua", 'o.bind("SUPER + CTRL + M", "Akari Kopa", "omarchy-shell kayu.akari-kopa toggle")', ("hyprctl", "reload")),
            (HyprlandLua, "hypr/hyprland.lua", f'hl.bind("SUPER + CTRL + M", hl.dsp.exec_cmd("{CHOOSE}"), {{ description = "Akari Kopa" }})', ("hyprctl", "reload")),
            (HyprlandConf, "hypr/hyprland.conf", f"bind = SUPER CTRL, M, exec, {CHOOSE}", ("hyprctl", "reload")),
            (Sway, "sway/config", f"bindsym Mod4+Ctrl+m exec {CHOOSE}", ("swaymsg", "reload")),
        ]
        for kind, relative, line, reload in cases:
            with self.subTest(kind.__name__):
                session = environment("hyprland", "sway")
                path = config(session, relative)
                command_line = FakeCommandLine({"omarchy-shell"})
                home = kind(session, command_line, CHOOSE)
                self.assertTrue(home.here())
                home.add()
                self.assertEqual(path.read_text(), f"existing = true\n{line}\n")
                self.assertTrue(home.has_it())
                self.assertIn(reload, command_line.asked)
                home.remove()
                self.assertEqual(path.read_text(), "existing = true\n")

    def test_hyprland_without_omarchy_is_not_omarchy(self):
        session = environment("hyprland")
        config(session, "hypr/bindings.lua")
        self.assertFalse(Omarchy(session, FakeCommandLine(set()), CHOOSE).here())

    def test_a_desktop_without_its_config_file_is_not_here(self):
        self.assertFalse(Sway(environment("sway"), FakeCommandLine(set()), CHOOSE).here())

    def test_another_desktop_is_not_here(self):
        session = environment("gnome")
        config(session, "sway/config")
        self.assertFalse(Sway(session, FakeCommandLine(set()), CHOOSE).here())


class SettingsDesktops(unittest.TestCase):
    def test_gnome_adds_a_custom_shortcut_beside_the_ones_already_there(self):
        command_line = FakeCommandLine({"gsettings"}, said={
            ("gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"): "['/custom0/']"})
        home = Gnome(environment("ubuntu", "gnome"), GSettings(command_line), CHOOSE)
        self.assertTrue(home.here())
        home.add()
        self.assertIn(("gsettings", "set", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings", str(["/custom0/", PATH])), command_line.asked)
        self.assertTrue(home.has_it())
        home.remove()
        self.assertFalse(home.has_it())

    def test_gnome_with_no_custom_shortcuts_yet(self):
        command_line = FakeCommandLine({"gsettings"}, said={
            ("gsettings", "get", "org.gnome.settings-daemon.plugins.media-keys", "custom-keybindings"): "@as []"})
        home = Gnome(environment("budgie"), GSettings(command_line), CHOOSE)
        self.assertFalse(home.has_it())
        home.add()
        self.assertTrue(home.has_it())

    def test_cinnamon_lists_it_by_name_and_binds_a_list_of_keys(self):
        command_line = FakeCommandLine({"gsettings"})
        home = Cinnamon(environment("x-cinnamon"), GSettings(command_line), CHOOSE)
        home.add()
        self.assertTrue(home.has_it())
        self.assertIn("['<Super><Control>m']", [asked[-1] for asked in command_line.asked])

    def test_mate_keeps_its_shortcut_in_its_own_keybinding_folder(self):
        command_line = FakeCommandLine({"gsettings"})
        home = Mate(environment("mate"), GSettings(command_line), CHOOSE)
        home.add()
        self.assertTrue(home.has_it())
        home.remove()
        self.assertFalse(home.has_it())

    def test_xfce_sets_a_custom_command(self):
        command_line = FakeCommandLine({"xfconf-query"})
        Xfce(environment("xfce"), command_line, CHOOSE).add()
        self.assertIn(("xfconf-query", "-c", "xfce4-keyboard-shortcuts", "-p", "/commands/custom/<Super><Primary>m", "-n", "-t", "string", "-s", CHOOSE),
                      command_line.asked)

    def test_kde_launches_a_hidden_entry_bound_in_global_shortcuts(self):
        session = environment("kde")
        command_line = FakeCommandLine({"kwriteconfig6"})
        home = Kde(session, command_line, CHOOSE)
        home.add()
        launcher = (session.data_home / "applications" / "akari-kopa-choose.desktop").read_text()
        self.assertIn(f"Exec={CHOOSE}\n", launcher)
        self.assertIn(("kwriteconfig6", "--file", "kglobalshortcutsrc", "--group", "services", "--group", "akari-kopa-choose.desktop",
                       "--key", "_launch", "Meta+Ctrl+M"), command_line.asked)
        home.remove()
        self.assertFalse(home.has_it())
