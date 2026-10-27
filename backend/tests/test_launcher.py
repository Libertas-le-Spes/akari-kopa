import unittest

from tests.source_files import read


class Launcher(unittest.TestCase):
    def test_python_starts_isolated_from_the_current_folder_and_the_environment(self):
        launcher = read("backend/bin/akari-kopa")
        self.assertIn('exec python3 -I "$(dirname "$(readlink -f "$0")")/start.py" "$@"', launcher)
        self.assertNotIn("PYTHONPATH", launcher)
        self.assertNotIn("-m akari_kopa", launcher)

    def test_the_installer_stops_the_tray_the_launcher_starts(self):
        self.assertIn('pkill -u "$(id -u)" -f "python3 -I [^ ]*/backend/bin/start.py tray"', read("install.sh"))
