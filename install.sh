#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
launcher="$here/backend/bin/akari-kopa"
command_path="$HOME/.local/bin/akari-kopa"
short_path="$HOME/.local/bin/akari"
autostart="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/akari-kopa-tray.desktop"

declare -A packages=(
  [apt-get:python3]=python3 [apt-get:gi]=python3-gi
  [dnf:python3]=python3 [dnf:gi]=python3-gobject
  [pacman:python3]=python [pacman:gi]=python-gobject
  [zypper:python3]=python3 [zypper:gi]=python3-gobject
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

is_ours() {
  [ -L "$1" ] && [ "$(readlink -f "$1")" = "$(readlink -f "$launcher")" ]
}

refuse_unsafe_path() {
  if [[ ! $1 =~ ^[A-Za-z0-9/._-]+$ ]]; then
    echo "Akari Kopa needs a folder whose name has only letters, digits, '/', '.', '_' and '-': $1" >&2
    exit 1
  fi
}

link_command() {
  if [ -e "$1" ] || [ -L "$1" ]; then
    if ! is_ours "$1"; then
      echo "$1 is another program; Akari Kopa leaves it alone. Remove it first to install Akari Kopa there." >&2
      exit 1
    fi
    return
  fi
  ln -s "$launcher" "$1"
}

unlink_command() {
  if is_ours "$1"; then
    rm -f "$1"
  fi
}

remove() {
  pkill -u "$(id -u)" -f "python3 -I [^ ]*/backend/bin/start.py tray" || true
  "$launcher" remove-shortcut || true
  unlink_command "$command_path"
  unlink_command "$short_path"
  rm -f "$autostart"
  echo "Removed the Akari Kopa tray."
}

missing_packages() {
  command -v python3 >/dev/null || { package_for python3; return; }
  python3 -I -c 'import sys; sys.exit(sys.version_info < (3, 10))' || package_for python3
  python3 -I -c 'import gi; gi.require_version("Gio", "2.0")' 2>/dev/null || package_for gi
}

install_tray() {
  mkdir -p "$(dirname "$command_path")" "$(dirname "$autostart")"
  link_command "$command_path"
  link_command "$short_path"
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
  true
}

if [ "${1:-}" = "--remove" ]; then
  remove
  exit 0
fi

refuse_unsafe_path "$here"
refuse_unsafe_path "$command_path"

missing=$(missing_packages | sort -u | tr '\n' ' ')
if [ -n "$missing" ]; then
  echo "Install these packages first: $missing" >&2
  exit 1
fi

install_tray
"$command_path" shortcut || true
readable=$(found_services | sort | paste -sd ',' | sed 's/,/, /g')
echo "Services it can read: ${readable:-none yet; install and log in to glab, gh, tea (0.12+) or az}"
