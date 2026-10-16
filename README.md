# Merge requests

One coloured orb per open merge request, in your bar or system tray, so you see when a pipeline breaks without opening a browser.

| Orb | Meaning |
|---|---|
| green / red | your merge request, pipeline passed / failed; green too when it has no pipeline |
| purple | yours, and someone left comments you have not resolved or answered; a failed pipeline still shows red |
| blue / yellow | one you are reviewing, pipeline passed / failed |
| ring | pipeline still running |

Hover shows the number and author; a click lists them and opens one. A pipeline waiting on manual jobs counts as passed. An orb leaves once its merge request merges or closes.

A merge request to a repository you cannot push to shows for its first three days, then steps aside: maintainers there answer when they answer. It is looked at again on days 5 and 7, then weekly, and comes back only if comments are waiting for you. On day 31 it is let go.

## Omarchy

```sh
omarchy plugin add https://github.com/Libertas-le-Spes/merge-requests.git --enable --yes
omarchy bar put kayu.merge-requests --section center
```

For the Super + Ctrl + M shortcut to the list:

```sh
~/.config/omarchy/plugins/kayu.merge-requests/backend/bin/merge-requests shortcut
```

## Any other Linux desktop

A system tray icon per merge request, for KDE, XFCE, Cinnamon, MATE, Budgie, Waybar, and GNOME with the AppIndicator extension.

```sh
git clone https://github.com/Libertas-le-Spes/merge-requests.git ~/.local/share/merge-requests
~/.local/share/merge-requests/install.sh
merge-requests tray &
```

It starts with your session from then on, and Super + Ctrl + M opens a list of your merge requests; pick one to open it. The shortcut is set the way your desktop keeps its own: KDE Plasma, GNOME, Budgie, Cinnamon, MATE, Xfce, Hyprland and Sway. The list needs zenity or kdialog. `install.sh --remove` undoes all of it.

## Services

Each service is read through the tool you already log in with. Bitbucket and Azure DevOps have no such tool, so their key goes in the system keyring.

| Service | Log in with |
|---|---|
| GitLab, including self-hosted | `glab auth login` |
| GitHub, including Enterprise | `gh auth login` |
| Gitea, Forgejo, Codeberg | `tea login add` (tea 0.12 or newer) |
| Bitbucket Cloud | an API token in the keyring, below |
| Azure DevOps | a personal access token in the keyring, below |

For Bitbucket, create an [Atlassian API token](https://id.atlassian.com/manage-profile/security/api-tokens) with the read scopes for user, workspace, repository, permission and pull request, then:

```sh
secret-tool store --label="Bitbucket (merge requests)" merge-requests bitbucket.org
```

and enter `you@example.com:your-token`. Bitbucket is checked every five minutes rather than every minute, to stay inside its rate limit.

For Azure DevOps, create a [personal access token](https://learn.microsoft.com/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate) for **all accessible organizations** with the read scopes for code, build, security and user profile, then:

```sh
secret-tool store --label="Azure DevOps (merge requests)" merge-requests dev.azure.com
```

and enter the token. Every organisation you belong to is read, and a pull request's pipeline is the builds Azure Pipelines ran for it.

When a service cannot be reached, its last answer stays on show, faded, with the reason in the list.

## Needs

Python 3.10 or newer. The tray also needs PyGObject (`python3-gi`, `python3-gobject` or `python-gobject`); `install.sh` names whatever is missing.

## Adding a service

Add a class to `backend/merge_requests/adapters/services/` that says whether it is set up and returns the merge requests it finds, and list it in `backend/merge_requests/wiring.py`. Nothing else changes.

## Tests

```sh
cd backend && python3 -m unittest
```
