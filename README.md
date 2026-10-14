# Merge requests

One coloured orb per open merge request, in your bar or system tray, so you see when a pipeline breaks without opening a browser.

| Orb | Meaning |
|---|---|
| green / red | your merge request, pipeline passed / failed |
| blue / yellow | one you are reviewing, pipeline passed / failed |
| ring | pipeline still running |

Hover shows the number and author; a click lists them and opens one. A pipeline waiting on manual jobs counts as passed. An orb leaves once its merge request merges or closes.

## Omarchy

```sh
omarchy plugin add https://github.com/KayAugust/merge-requests.git --enable --yes
omarchy bar put kayu.merge-requests --section center
```

Optional shortcut in `~/.config/hypr/bindings.lua`:

```lua
o.bind("SUPER + CTRL + M", "Merge requests", "omarchy-shell kayu.merge-requests toggle")
```

## Any other Linux desktop

A system tray icon per merge request, for KDE, XFCE, Cinnamon, MATE, Budgie, Waybar, and GNOME with the AppIndicator extension.

```sh
git clone https://github.com/KayAugust/merge-requests.git ~/.local/share/merge-requests
~/.local/share/merge-requests/tray/install
merge-requests-tray &
```

It starts with your session from then on. `tray/install --remove` undoes it.

## Services

Each service is read through the tool you already log in with, so no key is stored here.

| Service | Log in with |
|---|---|
| GitLab, including self-hosted | `glab auth login` |
| GitHub, including Enterprise | `gh auth login` |
| Gitea, Forgejo, Codeberg | `tea login add` (tea 0.12 or newer) |
| Bitbucket Cloud | an API token in the system keyring, below |

Bitbucket has no login tool, so its key goes in the keyring. Create an [Atlassian API token](https://id.atlassian.com/manage-profile/security/api-tokens) with the read scopes for user, workspace, repository and pull request, then:

```sh
secret-tool store --label="Bitbucket (merge requests)" merge-requests bitbucket.org
```

and enter `you@example.com:your-token`. Bitbucket is checked every five minutes rather than every minute, to stay inside its rate limit.

## Needs

bash 4.4+, jq 1.6+ and curl. The tray also needs Python 3.6+ with PyGObject (`python3-gi`, `python3-gobject` or `python-gobject`); `tray/install` names whatever is missing.

## Adding a service

Add an executable to `providers/` that prints a JSON array of merge requests; `lib/merge-request.jq` turns a service's own status words into the orb's states.
