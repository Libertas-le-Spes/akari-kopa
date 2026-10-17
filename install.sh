#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
command_path="$HOME/.local/bin/akari-kopa"
short_path="$HOME/.local/bin/akari"
autostart="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/akari-kopa-tray.desktop"

declare -A packages=(
  [apt-get:python3]=python3 [apt-get:gi]=python3-gi [apt-get:secret-tool]=libsecret-tools
  [dnf:python3]=python3 [dnf:gi]=python3-gobject [dnf:secret-tool]=libsecret
  [pacman:python3]=python [pacman:gi]=python-gobject [pacman:secret-tool]=libsecret
  [zypper:python3]=python3 [zypper:gi]=python3-gobject [zypper:secret-tool]=libsecret-tools
)

declare -A services=(
  [glab]="GitLab (glab)" [gh]="GitHub (gh)" [tea]="Gitea/Forgejo (tea)" [az]="Azure DevOps (az)"
)

package_manager() {
  for manager in apt-get dnf pacman zypper; do
    command -v "$manager" >/dev/null && { echo "$manager"; return; }
  done
}

package_for() {
  echo "${packages[$(package_manager):$1]:-$1}"
}

remove() {
  pkill -f "python3[^ ]* -m akari_kopa tray" || true
  "$here/backend/bin/akari-kopa" remove-shortcut || true
  rm -f "$command_path" "$short_path" "$autostart"
  echo "Removed the Akari Kopa tray."
}

missing_packages() {
  command -v python3 >/dev/null || { package_for python3; return; }
  python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || package_for python3
  python3 -c 'import gi; gi.require_version("Gio", "2.0")' 2>/dev/null || package_for gi
}

install_tray() {
  mkdir -p "$(dirname "$command_path")" "$(dirname "$autostart")"
  ln -sf "$here/backend/bin/akari-kopa" "$command_path"
  ln -sf "$here/backend/bin/akari-kopa" "$short_path"
  cat > "$autostart" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Akari Kopa
Comment=Pipeline and comment state of your merge requests in the system tray
Exec=$command_path tray
Terminal=false
X-GNOME-Autostart-enabled=true
DESKTOP
  echo "Installed. It starts with your desktop session; to start it now, run: akari tray &"
}

found_services() {
  for tool in "${!services[@]}"; do
    command -v "$tool" >/dev/null && echo "${services[$tool]}"
  done
  secret-tool lookup akari-kopa bitbucket.org >/dev/null 2>&1 && echo "Bitbucket (key in the keyring)"
  true
}

if [ "${1:-}" = "--remove" ]; then
  remove
  exit 0
fi

missing=$(missing_packages | sort -u | tr '\n' ' ')
if [ -n "$missing" ]; then
  echo "Install these packages first: $missing" >&2
  exit 1
fi

install_tray
"$command_path" shortcut || true
readable=$(found_services | sort | paste -sd ',' | sed 's/,/, /g')
echo "Services it can read: ${readable:-none yet; install and log in to glab, gh, tea (0.12+) or az}"
