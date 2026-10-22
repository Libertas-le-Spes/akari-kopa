# Security review

This review describes the repository at commit `734c9ca627a6e6fb2fd1874f565a5ee76f685d37` on 2026-10-22. Most of what it proposes is planned, not done. It will change: whoever fixes a finding, or makes any part of this document untrue, updates it in the same pull request.

## What Akari Kopa is, and what an attacker would want from it

Akari Kopa puts one coloured orb per open merge request on the Omarchy bar or in a system tray. A Python program asks each forge (GitLab, GitHub, Gitea or Forgejo, Azure DevOps) for your merge requests, keeps the last answer in a cache, and prints a summary that the bar's QML draws. Clicking one opens its page in your browser.

It never asks for a token of its own. It borrows the login you already made with each forge's own tool: `glab`, `gh`, `tea` or `az`. That is the main reason it is in reasonable shape: there is no token file of its own to protect.

So what is worth stealing or abusing is:

- **the logins it borrows.** `gh` asks for the `repo`, `read:org` and `gist` scopes by default, which is write access to every repository you can reach. Anything that runs code inside Akari Kopa can use them.
- **the click.** Akari Kopa hands a web address that came from a server to your desktop's "open this" machinery. That machinery can do far more than open a browser.
- **what it shows.** Merge request titles, project names and colleagues' names are often confidential work information.

## Verdict

**Nothing Critical or High. Four Medium findings, worth fixing in the order below.**

None of the findings can be used by a stranger on the internet against someone using github.com or gitlab.com. Each one needs one of three things: a forge server that lies, a file planted in a folder where you run the `akari` command, or a push to this repository's `main` branch.

The two that most need fixing are:

1. **The page addresses that forges send are opened without being checked.** In the bar, the tray and the list, whatever text the server sends as the merge request's address goes straight to the desktop's opener. That includes `file://`, `smb://`, `nfs://` and any custom scheme, and in the list a value starting with `-` arrives as an option instead of an address. A self-hosted GitLab, Gitea or GitHub Enterprise server that has been taken over can use this for a one-click attack on your desktop.
2. **The `main` branch is not protected,** and every install updates from it. Anyone who gets push access to the organisation, for example through one stolen login, can ship code that runs on every user's next update with their borrowed forge logins.

Everything below was checked against that commit. Where a claim is about what code does, it was run against made-up data and the output is pasted.

## Findings

| ID | Severity | Title | Location |
|---|---|---|---|
| F1 | Medium | Addresses from the forge are opened without being checked | `backend/akari_kopa/adapters/dialogs/xdg_browser.py:9`, `backend/akari_kopa/adapters/desktop/linux_desktop.py:45`, `frontend/omarchy-bar/BarWidget.qml:39`, each service's `reading.py` |
| F2 | Medium | The `main` branch every install updates from is not protected | GitHub repository settings |
| F3 | Medium | The `akari` command runs Python code from whichever folder you are in | `backend/bin/akari-kopa:2` |
| F4 | Medium | The Azure DevOps token follows redirects to other hosts and to plain `http` | `backend/akari_kopa/adapters/transport/https.py:22-26` |
| F5 | Low | Merge request titles and project names are readable by every account on the machine while the list is open | `backend/akari_kopa/adapters/dialogs/zenity.py:16`, `kdialog.py:16`, `adapters/transport/graphql_cli.py:19`, `adapters/services/gitea/tea.py:18` |
| F6 | Low | It borrows full-power logins where read-only would do | `backend/akari_kopa/wiring.py:49-55`, `adapters/services/azure_devops/az.py:13` |
| F7 | Low | Titles go into notifications and tray tooltips as markup | `backend/akari_kopa/adapters/desktop/linux_desktop.py:36-41`, `adapters/desktop/status_notifier.py:183`, `entrypoints/tray/icon_contents.py:18` |
| F8 | Low | The cache writer follows a planted link and does not tighten a folder that already exists | `backend/akari_kopa/adapters/storage/answer_folder.py:28-33` |
| F9 | Info | The install path goes unescaped into shell and Lua configuration, which is rewritten in place | `backend/akari_kopa/adapters/shortcuts/hyprland.py:30,43`, `sway.py:12`, `kde.py:27`, `config_lines.py:14-20` |
| F10 | Info | Nothing runs the tests on a pull request | no `.github/workflows` |

---

## F1 · Medium · Addresses from the forge are opened without being checked

**What this is.** Every merge request carries the address of its web page. GitLab sends it as `webUrl`, GitHub as `url`, Gitea as `html_url`. Akari Kopa keeps that text as it comes and, when you click, gives it to the desktop to open. There are three ways to open one, and none of them checks the address:

| Where you click | What opens it | Location |
|---|---|---|
| the bar's list | `Qt.openUrlExternally` | `frontend/omarchy-bar/BarWidget.qml:37-40` |
| the tray menu | `Gio.AppInfo.launch_default_for_uri` | `backend/akari_kopa/adapters/desktop/linux_desktop.py:43-47` |
| the Super + Ctrl + M list | `xdg-open <address>` | `backend/akari_kopa/adapters/dialogs/xdg_browser.py:8-9` |

Azure DevOps is the exception: its address is built locally from fixed text, with each part escaped (`adapters/services/azure_devops/reading.py:28`).

**Why it matters.** The desktop's "open" is not "open in a browser". It opens whatever the address names, with whichever program is registered for it: local files, network shares (`smb://`, `nfs://`, `dav://`), and any custom scheme some installed application has registered. Positive Security showed in 2021 that this turned "open a link" into one-click code execution in Telegram, Nextcloud, VLC, LibreOffice, Wireshark and Mumble. On Xfce, an `nfs://` address mounted a share without warning, and a `.desktop` file on it ran without warning. Their fix is the one proposed here: *"Applications that let users open external URLs should validate the URLs with a URI scheme allowlist."*

**Shown with made-up data.** A fake Gitea service returned five hostile addresses. They went through the real listing, the real cache and the real list command, into a stub `xdg-open` that only writes down what it was given:

```text
cached url values: ['file:///home/someone/.ssh/id_ed25519', '--help', 'javascript:alert(1)', 'smb://203.0.113.9/share', 'example-scheme://do?x=1']
--- what the stubbed xdg-open was asked to open:
xdg-open|file:///home/someone/.ssh/id_ed25519|
xdg-open|--help|
xdg-open|javascript:alert(1)|
xdg-open|smb://203.0.113.9/share|
xdg-open|example-scheme://do?x=1|
```

The cache stores them as they are and gives them back as they are, so a bad address keeps working after the server has been fixed, for as long as the merge request stays in the cache.

The `--help` line is an argument injection (CWE-88). The real `xdg-open` takes only `--help`, `--manual` and `--version`, so today it only prints help. That safety comes from `xdg-open`'s small option list, not from anything Akari Kopa does.

**Who could do this, and what happens if it is left alone.** Not a stranger on github.com or gitlab.com: those servers build the address themselves. It needs a forge server that lies. That means one you added with `glab`, `tea` or `gh` (a self-hosted GitLab, a Gitea or Forgejo instance, GitHub Enterprise) that has been compromised or is run by someone hostile, or a captured connection to one. The person it lands on clicks an orb that looks like any other. Depending on their desktop, they get a file manager mounting the attacker's share, a document opening in a program with its own bugs, or, on the weakest setups, a program running.

**Fix options.**

| Option | What it stops | What it fails to stop |
|---|---|---|
| A. Check the scheme at the three openers: only `https://` | `file:`, `smb:`, `nfs:`, custom schemes and a leading `-`, at the moment of opening | `https` addresses on other hosts, such as a look-alike sign-in page. Bad addresses still sit in the cache and the board. Three openers in two languages must each stay correct, and a fourth one added later starts out unchecked. |
| B. A web address type, made only by a check: `https`, the host must be the forge host that was asked, no user name or password in it, no spaces or control characters. Each service builds one when it reads the answer; the cache reads it back through the same check and drops entries that fail; the openers take only this type. | Everything A stops, plus addresses pointing away from the forge you asked, and anything planted in the cache. A bad address never gets into the board at all. | The bar's QML gets addresses as JSON text, so a check in Python does not cover a bug in the QML or a future QML path that reads something else. It does not stop a lying server sending a page on its own host, which it controls anyway. |
| C. A guard in the QML before `Qt.openUrlExternally`: open nothing unless the address starts with `https://` | The bar, even if the Python side regresses | Only the bar. |

**Recommendation: B and C together.** B blocks bad addresses where they come in and makes the wrong call impossible in Python. C is a second, independent check in the one place that is not Python. Fail closed: a merge request whose address fails the check still shows its orb, but clicking it opens nothing and the list says why. Use the forge host each service already knows (the `--hostname` given to `gh` and `glab`, the URL of the `tea` login).

**How to seal it.**

- One test per service with a table of hostile addresses (made up, as above), each expecting rejection.
- A cache test that writes a hostile address into a cache file and expects it to be dropped on reading.
- An architecture test: no file except the opener adapters may contain `xdg-open`, `launch_default_for_uri` or `openUrlExternally`, and `Browser.open` and `Desktop.open_in_browser` take the web address type, not `str`.
- A test that reads `BarWidget.qml` and fails unless the one `Qt.openUrlExternally` call sits behind the `https://` guard.

Sources: [Positive Security, "Allow arbitrary URLs, expect arbitrary code execution"](https://positive.security/blog/url-open-rce); [CVE-2014-9622, xdg-open eval injection through the URL argument](https://nvd.nist.gov/vuln/detail/CVE-2014-9622); [Electron security checklist: do not use `shell.openExternal` with untrusted content](https://www.electronjs.org/docs/latest/tutorial/security#15-do-not-use-shellopenexternal-with-untrusted-content); [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html); [CWE-88](https://cwe.mitre.org/data/definitions/88.html); [CWE-20](https://cwe.mitre.org/data/definitions/20.html).

---

## F2 · Medium · The `main` branch every install updates from is not protected

**What this is.** The README installs Akari Kopa with `omarchy plugin add` from this repository and updates it with `omarchy plugin update`. Both take whatever is on `main`. The bar then runs that code as you, with your `gh`, `glab`, `tea` and `az` logins in reach.

**What was found.** GitHub's public API, asked without any login, answers that `main` is not protected:

```text
protected: False
visibility: public default: main
```

The last five commits are unsigned (`git log --format=%G?` gives `N` for each). There is one tag, `v3.1.0`, and the install instructions do not use it.

**What happens if it is left alone.** Anyone who gets push access can put code on `main`: a stolen session or token of any account with write access to the organisation, or a mistaken force-push. Every user who next runs the update and restarts the bar runs that code. With the `repo` scope that `gh` holds by default, that code can push to every repository those users can reach. GitHub CLI's own advisories show how much a token reaching the wrong place costs ([CVE-2024-53858](https://nvd.nist.gov/vuln/detail/cve-2024-53858)).

**Fix options.**

| Option | What it stops | What it fails to stop |
|---|---|---|
| A. A ruleset on `main`: changes only through pull requests, no force-push, no deletion, required status check (F10) | Direct and force pushes; merges that break the tests | A merged pull request from a stolen account that has merge rights |
| B. Require signed commits on `main` | Commits made with a stolen GitHub token or session alone, without the signing key | A stolen signing key; a malicious change that the owner signs without noticing |
| C. Require two-factor sign-in for everyone in the organisation | Most stolen-password takeovers | Stolen session cookies and tokens |
| D. Users install a signed tag or a fixed commit, not `main` | A bad push reaching users before it is released | A bad change that gets released. Depends on whether `omarchy plugin` can install a given tag or commit; **not verified**. |

**Recommendation: A, B and C now, D once confirmed.** These are settings, not code, and they protect every later fix in this document. Each one covers a gap in the others.

**How to seal it.** The ruleset itself is the seal. Note in the README's install section which tag users should install. A scheduled check could read `protected` from the same public API and fail when it is `false`.

Sources: [GitHub: about rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets); [GitHub: requiring two-factor authentication in your organization](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization); [CWE-494, download of code without integrity check](https://cwe.mitre.org/data/definitions/494.html).

---

## F3 · Medium · The `akari` command runs Python code from whichever folder you are in

**What this is.** `akari`, `akari-kopa`, the keyboard shortcut and the bar all start the program through one small launcher, `backend/bin/akari-kopa`. It runs `python3 -m akari_kopa`. With `-m`, Python puts **the current folder** first in the list of places it loads modules from, ahead of the standard library.

**Shown with made-up data.** A folder held a file named `json.py` that only prints a line. Running `akari-kopa` from that folder, with an unknown subcommand so nothing reaches any forge:

```text
$ cd untrusted-folder && akari-kopa no-such-command
PLANTED json.py ran inside akari-kopa
exit 0
$ cd elsewhere && akari-kopa no-such-command
akari-kopa: say one of board, tray, choose, shortcut, remove-shortcut
exit 2
$ cd untrusted-folder && PYTHONPATH=…/backend python3 -P -m akari_kopa no-such-command
akari-kopa: say one of board, tray, choose, shortcut, remove-shortcut
exit 2
```

**What happens if it is left alone.** Someone who can put a file into a folder where you might type `akari` (a repository you cloned to review, an unpacked download) gets their code run inside Akari Kopa, next to your forge logins. You would see nothing unusual. It is the same class of bug as the GitHub CLI's [GHSA-fqfh-778m-2v32](https://github.com/advisories/GHSA-fqfh-778m-2v32), where `gh` ran a `git` program from the current folder. Whether the bar's process starts in a folder an attacker could write to was **not demonstrated**.

**Fix options.**

| Option | What it stops | What it fails to stop |
|---|---|---|
| A. `python3 -P -m akari_kopa` | The current folder | `PYTHON*` environment variables and your own site-packages folder. Needs Python 3.11: on 3.10, `-P` is an error, so it fails closed, but the README and `install.sh` would have to ask for 3.11. |
| B. `python3 -I` running a small launcher file that adds its own absolute folder to `sys.path` and calls `main` | The current folder, every `PYTHON*` variable, your site-packages folder. Works on 3.10. | Anyone who can already write to the install folder or the system Python, who owns the program anyway. |

**Recommendation: B.** It removes every outside place Python would look, not just one, and it works on the Python version the README promises. Update `install.sh`'s `pkill` pattern (`install.sh:31`) in the same change, because it matches `-m akari_kopa tray`.

**How to seal it.** A test that runs the real launcher from a temporary folder holding a made-up `json.py` that writes a marker file, and fails if the marker appears. An architecture test that the launcher contains `-I`.

Sources: [Python command line, `-P` and `-I`](https://docs.python.org/3/using/cmdline.html); [CWE-427, uncontrolled search path element](https://cwe.mitre.org/data/definitions/427.html).

---

## F4 · Medium · The Azure DevOps token follows redirects to other hosts and to plain `http`

**What this is.** For Azure DevOps, Akari Kopa asks `az` for a short-lived access token and then calls the REST API itself with Python's `urllib`, sending `Authorization: Bearer <token>` (`adapters/transport/https.py`). This is the only place Akari Kopa holds a token itself. The token comes through `az`'s output, not its arguments, and lives only in memory. That part is good.

**What is wrong.** When a server answers "go elsewhere", `urllib` follows and copies every header set with `headers=`, `Authorization` included, to whatever host it is sent to. It also follows from `https` to `http`. CPython's `redirect_request` drops only `content-length` and `content-type`. It is the same mistake as urllib3's [CVE-2018-20060](https://research.averlon.ai/vulnerability-intelligence/cve/CVE-2018-20060), but in the standard library, which still does it on Python 3.14, as shown below.

**Shown with made-up data**, using the real transport class on Python 3.14 with two local servers, the first redirecting to the second under a different host name:

```text
asked 127.0.0.1, redirected to a different host (localhost); that host received Authorization: ['Bearer made-up-token-123']
```

**What happens if it is left alone.** Any redirect from `dev.azure.com` or `app.vssps.visualstudio.com`, whether from a misconfiguration, a moved endpoint or an attacker who can influence one, hands your token to the new host, possibly in clear text. That token can act as you across every Azure DevOps organisation you belong to (F6).

**Fix options.**

| Option | What it stops | What it fails to stop |
|---|---|---|
| A. Remove `Authorization` when a redirect changes host or scheme (what `requests` does) | Cross-host and downgrade leaks | Nothing else checks that the first address was right |
| B. Follow no redirects at all; a redirect becomes "not updated" with the reason | Every redirect leak, with no logic to get wrong | Only redirects; does not check the first address |
| C. The transport accepts only `https` addresses on an allowlist of hosts (`dev.azure.com`, `app.vssps.visualstudio.com`) and refuses anything else before sending | A wrong or `http` address built from API data | Redirects, on its own |
| D. Set the header with `add_unredirected_header` | The header being copied by `urllib`'s redirect | Nothing if a later change uses another client |

**Recommendation: B, C and D together.** None of the Azure DevOps calls used here needs a redirect, so refusing them costs nothing and fails closed. C checks where the token goes before anything is sent. D is a third layer if someone later turns redirects back on.

**How to seal it.** Turn the demonstration above into a unit test (two local servers, a made-up token, expect a `ServiceError` and nothing received by the second server). Add a test that building the transport with an `http://` or off-list address raises. Add an architecture test that only `https.py` imports `urllib.request`.

Sources: [CPython `urllib/request.py`, `HTTPRedirectHandler.redirect_request`](https://github.com/python/cpython/blob/main/Lib/urllib/request.py); [CWE-200](https://cwe.mitre.org/data/definitions/200.html); [CWE-319](https://cwe.mitre.org/data/definitions/319.html); [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).

---

## F5 · Low · Merge request titles and project names are readable by every account on the machine while the list is open

**What this is.** On Linux, any account on the machine can read any process's command line from `/proc/<pid>/cmdline`, unless `/proc` is mounted with `hidepid`. Akari Kopa passes merge request details as command-line arguments in three places:

- **the Super + Ctrl + M list:** every row (title, author, project, address) is an argument to `zenity` or `kdialog` for as long as the list is open;
- **GitLab paging:** the project path is a `-f project=…` argument to `glab api` (`adapters/services/gitlab/gitlab.py:41`, `adapters/transport/graphql_cli.py:19`);
- **Gitea:** the repository name is in the API path given to `tea api` (`adapters/services/gitea/gitea.py:43-54`).

**No token is ever in an argument.** That was checked for every call, and the Azure token arrives on `az`'s output.

**Shown with made-up data**, through the real list adapter with a stub `zenity` that waits:

```text
pid 2315895 mode: -r--r--r-- kayu
/bin/sh …/slowbin/zenity --list --title=Akari Kopa --text=Open which one? … --print-column=1 gitlab https://gitlab.example.com/acme/secret-merger/-/merge_requests/7 !7 · Example Person Acquire Example Corp quietly · acme/secret-merger
--- /proc mount options:
rw,nosuid,nodev,noexec,relatime
```

`-r--r--r--`, and no `hidepid`: every account could read it.

**What happens if it is left alone.** On a laptop with one user, nothing. On a shared machine, another account can log the names of private projects and what is being worked on. CWE-214 names this case.

**Fix options.**

| Option | What it stops | What it fails to stop |
|---|---|---|
| A. Send `zenity` its rows on standard input (`zenity --list` reads them from there) | The list leak, for `zenity` | `kdialog`, which takes its menu only as arguments |
| B. Send GraphQL queries and variables to `gh` and `glab` as a JSON body on standard input (`gh api graphql --input -`; `glab api` also reads `--input` from standard input) | The GitLab and GitHub argument leaks | `tea api`, which takes its path as an argument (`tea` has no other way that was found) |
| C. Drop `kdialog` as a list tool | The `kdialog` leak | Users on desktops without `zenity` lose the list. Fail-closed: the command says to install `zenity`. |
| D. Advise mounting `/proc` with `hidepid=invisible` on shared machines | Every argument leak on that machine, from every program | Machines where it is not set; it can break tools that read other users' processes |

**Recommendation: A, B and C, and mention D in the README for shared machines.** That leaves one known gap, `tea`'s path, which should be written down here until it is closed.

**How to seal it.** A test with a recording fake command runner, a made-up title used as a marker, and a run through every service and the list: no argument may contain the marker.

Sources: [CWE-214, invocation of process using visible sensitive information](https://cwe.mitre.org/data/definitions/214.html); `gh api --help` and `glab api --help` (installed versions 2.102.0 and 1.113.0), which document `--input` reading from standard input.

---

## F6 · Low · It borrows full-power logins where read-only would do

**What this is.** Akari Kopa only reads. But the logins it borrows can write: `gh auth login` asks for `repo`, `read:org` and `gist` ("the minimum required scopes", in `gh auth login --help`); `glab auth login` usually gets `api`; the Azure token from `az account get-access-token` can do anything you can do in Azure DevOps.

**What happens if it is left alone.** This is not a bug on its own. It decides how bad F1, F2 and F3 are: whatever runs inside Akari Kopa can push code, merge, or delete as you, on every forge you are logged in to.

**How the borrowed logins are stored.** Akari Kopa never touches them, but users should know:

| Tool | Where it keeps the token by default |
|---|---|
| `gh` | the desktop's keyring (Secret Service), since 2.26.0; plain text in `~/.config/gh/hosts.yml` with `--insecure-storage` or when no keyring is found |
| `glab` | the keyring when one is available, otherwise plain text in its config file, per `glab auth login --help` |
| `tea` | **not confirmed**; its configuration lives in `$XDG_CONFIG_HOME/tea` |
| `az` | plain-text files under `~/.azure` on Linux, per Microsoft's own documentation |

**Fix options.**

| Option | What it stops | What it fails to stop |
|---|---|---|
| A. Keep borrowing, and say in the README which scopes and storage to choose | Nothing technical | Everything above |
| B. Akari Kopa's own read-only tokens, kept in the Secret Service with `secret-tool` (already installed with libsecret) and handed to `glab` and `gh` through `GITLAB_TOKEN` and `GH_TOKEN` in their environment. Only the same account can read a process's environment. GitLab: a token with only `read_api`. Azure DevOps: a token with only Code (Read) and Build (Read). | Write access through Akari Kopa | Any program running as you can ask an unlocked Secret Service for any secret: it does not tell programs apart. GitHub has no read-only token covering private repositories across several owners: a fine-grained token covers one owner, and a classic token needs the full `repo` scope for private repositories. |

**Recommendation: B for GitLab and Azure DevOps; for GitHub, one fine-grained read-only token per owner where that covers your repositories, and A where it does not.** Fail closed: if the Secret Service is locked or missing, report "not updated" and never fall back to a file.

**How to seal it.** A test that the code that builds the environment for `gh` and `glab` never writes a token into an argument or a file. A check at start-up that refuses an Azure DevOps token unless it came from the Secret Service.

Sources: [GitHub CLI 2.26.0 release notes](https://github.com/cli/cli/releases/tag/v2.26.0); [glab: store credentials in the OS keyring by default](https://gitlab.com/gitlab-org/cli/-/merge_requests/3528); [Microsoft: MSAL-based Azure CLI, token cache storage](https://learn.microsoft.com/en-us/cli/azure/msal-based-azure-cli); [GitHub: managing personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens); [GitLab: personal access token scopes](https://docs.gitlab.com/user/profile/personal_access_tokens/); [freedesktop Secret Service specification](https://specifications.freedesktop.org/secret-service-spec/latest/); [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html).

---

## F7 · Low · Titles go into notifications and tray tooltips as markup

**What this is.** In the tray version, clicking an icon sends a desktop notification whose body includes the merge request's title (`entrypoints/tray/icon_contents.py:18,32`). The same text goes into the tray icon's tooltip (`adapters/desktop/status_notifier.py:183`). The notification specification allows the body to contain `<b>`, `<i>`, `<u>`, `<a href>` and `<img src>`. Many tray hosts draw tooltip text as rich text as well. The title is sent unescaped, and anyone who can open a merge request that asks you for review chooses it.

**Not demonstrated** in a real notification server: none was run, to keep real notifications out of the review. By the specification, a title can make text bold or broken, add a link, or ask the server to load an image. What actually happens depends on the notification server.

The **bar is not affected**: every text in its QML, and the Omarchy bar's own tooltip, is drawn with `Text.PlainText`.

**Fix.** Escape the title, author and project with `GLib.markup_escape_text` wherever they become a notification body or a tooltip. Nothing about that is weaker than sending plain text, and it closes the whole case.

**How to seal it.** A test with a made-up title like `<b>x</b><img src="https://example.invalid/p.png"/>` that expects only escaped text in the notification body and tooltip.

Sources: [freedesktop notification specification, markup](https://specifications.freedesktop.org/notification/latest/markup.html); [CWE-116](https://cwe.mitre.org/data/definitions/116.html).

---

## F8 · Low · The cache writer follows a planted link and does not tighten a folder that already exists

**What this is.** Each forge's last answer is kept in `~/.cache/kayu.akari-kopa/answers/<service>.json`, so the bar can keep showing something when a forge is unreachable. The folder is created with mode `0700` and each file is set to `0600`. That is right for a normal home folder.

**What is weaker than it looks.**

- The temporary file always has the same name, `<service>.writing`, and is opened in a way that follows a link. If a link is already there, the write goes to wherever it points.
- The file is created with the default permissions, usually `0644`, and only then changed to `0600`.
- If the folder already exists with looser permissions, it is left as it is.

**Shown with made-up data.** An answers folder was made `0777`, with `gitea.writing` linked to an unrelated file, and then the real cache writer was run:

```text
folder after keep: drwxrwxrwx
victim now: -rw------- {"given": "2030-01-02T00:00:00+00:00", "mergeRequests": []}
lrwxrwxrwx …/victim.txt
```

The unrelated file was overwritten and its permissions changed, and the cache entry was left as a link to it.

**What happens if it is left alone.** Nothing, as long as the cache stays in your own home folder, because only you can write there. It matters only if `XDG_CACHE_HOME` points somewhere another account can write, such as a shared folder. It is Low, and cheap to make safe.

**Fix.** Before writing, check the folder with `lstat`: it must not be a link, it must be owned by you, and it must be `0700`. Tighten it when it is yours, and refuse to cache when it is not (fail closed: the board still works, it just keeps nothing). Write through a file created with `O_CREAT | O_EXCL | O_NOFOLLOW` and mode `0600` from the start, under a random name (`tempfile.mkstemp` does this), then rename. Reading follows the same folder check.

**How to seal it.** The demonstration above as a test, expecting refusal. A test that the new file is never readable by others, even for a moment, by checking its mode from inside the write.

Sources: [CWE-59, link following](https://cwe.mitre.org/data/definitions/59.html); [CWE-276, incorrect default permissions](https://cwe.mitre.org/data/definitions/276.html).

---

## F9 · Info · The install path goes unescaped into shell and Lua configuration, which is rewritten in place

**What this is.** `akari shortcut` adds a line to your desktop's configuration that runs `<install folder>/backend/bin/akari-kopa choose`. On Hyprland and Sway that line runs through a shell, and on Hyprland's Lua configuration it sits inside a Lua string. The folder path is pasted in as it is. Shown with a made-up folder name and a fake command runner, so nothing was reloaded:

```text
bind = SUPER CTRL, M, exec, /home/someone/odd $(touch /tmp/x)") os.execute("id")--/backend/bin/akari-kopa choose
hl.bind("SUPER + CTRL + M", hl.dsp.exec_cmd("/home/someone/odd $(touch /tmp/x)") os.execute("id")--/backend/bin/akari-kopa choose"), { description = "Akari Kopa" })
```

You choose the install folder yourself, so this is not something an attacker controls. A folder with a space in its name already breaks the shortcut. The same configuration files are also rewritten in place, so a crash halfway through a write can leave your Hyprland or Sway configuration cut short.

**Fix.** Refuse to add a shortcut when the install path has anything outside a safe set of characters (letters, digits, `/`, `.`, `_`, `-`), and say why: fail closed rather than try to quote correctly for four different languages. Write configuration through a temporary file and a rename, keeping the original file's permissions.

**How to seal it.** A test per kind of shortcut with a made-up hostile path, expecting refusal.

Sources: [OWASP OS Command Injection Defense Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html); [CWE-78](https://cwe.mitre.org/data/definitions/78.html).

---

## F10 · Info · Nothing runs the tests on a pull request

**What this is.** There is no `.github/workflows` folder. The 87 tests pass locally; that was run with a stub browser and stub openers, and the tests called none of them. But nothing stops a pull request that breaks them, so none of the seals proposed above would hold on their own.

**Fix.** One workflow that runs `python3 -m unittest` on every pull request and on `main`:

- triggered by `pull_request`, **never** `pull_request_target`, which would run code from a fork with this repository's write token;
- `permissions: contents: read` at the top, nothing more;
- every action pinned to a full commit hash, not a tag;
- no secrets.

Then make it a required check in F2's ruleset.

**How to seal it.** The ruleset requires the check. A test that reads every workflow file and fails on `pull_request_target`, on a missing `permissions` block, or on an action not pinned to a 40-character hash.

Sources: [GitHub: security hardening for GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions).

---

## What was checked and found sound

| Area | What was found |
|---|---|
| Token storage | Akari Kopa stores no token of its own. Logins stay with `gh`, `glab`, `tea` and `az`. |
| Tokens in process arguments | None. The Azure token comes on `az`'s output and goes only into a request header (`adapters/services/azure_devops/az.py:13-15`). |
| Tokens in logs, errors, cache, QML | No token reaches any of them. Error reasons are the last line of a tool's error output, cut to 160 characters, and they never contain the token Akari Kopa holds. |
| TLS | `urllib` uses Python's default context, which checks certificates and host names (`verify_mode: 2 check_hostname: True`). `gh`, `glab`, `tea` and `az` do their own checking. |
| Shell injection in subprocesses | Every program is started with a list of arguments, never through a shell (`adapters/transport/command_line.py`). |
| GraphQL variables | Passed with `-f`, which `gh` and `glab` take as plain text, so a value starting with `@` cannot make them read a file. Each value is preceded by its name, so none can start with `-`. |
| Azure DevOps addresses | Built from fixed hosts, with organisation, project and repository names escaped. |
| QML drawing | Every `Text` uses `Text.PlainText`, and so does the Omarchy bar's tooltip, so titles cannot inject rich text there. The bar's process has a fixed command with no arguments. |
| Local ports and IPC | Nothing listens on a network port, unlike the localhost page that was fixed in Chronata. The Quickshell IPC target offers only `refresh` and `toggle` and gives nothing back. The tray's D-Bus objects are on your own session bus, and menu numbers are checked against the menu's length. |
| Cache permissions | Files are `0600` in a `0700` folder in the normal case (see F8 for the edges). |
| Dependencies | Standard library only, plus the distribution's PyGObject. No pip packages, nothing downloaded at install time. |
| `install.sh` | No downloads and no `sudo`. It only links the command, writes an autostart entry and names missing packages. |
| Tests | Use made-up data and fakes. Run with stub openers, they started nothing. |

## Plan: small steps, safest first

Each step can ship on its own, has its own tests, and updates this document in the same pull request.

1. **Protect `main` (F2 A, B, C).** A ruleset, signed commits, two-factor sign-in for the organisation. Settings only, and it protects every step after it.
2. **Run the tests on every pull request (F10).** A least-privilege workflow, made a required check. From here on, every seal below is enforced.
3. **Check every address before it can be opened (F1 B and C).** A web address type in the `attention` ring, made only by its check. One small factory per forge that knows that forge's host, all behind the same interface, with no branching on which forge it is. The cache reads through the same check. The openers take only the type, and the QML gets its own guard. Hostile-address tests and the architecture test.
4. **Start Python isolated (F3 B).** A launcher file run with `python3 -I`; update `install.sh`'s `pkill` pattern. The planted-module test.
5. **Lock down the Azure transport (F4 B, C, D).** No redirects, a host allowlist, an unredirected header. The two-server test.
6. **Keep merge request details out of process arguments (F5 A, B, C).** Rows to `zenity` and queries to `gh` and `glab` on standard input; retire `kdialog`; note `tea`'s gap here. The marker test.
7. **Escape markup in notifications and tooltips (F7).** The made-up markup test.
8. **Harden the cache writer (F8).** Folder check, exclusive no-follow creation, fail closed. The planted-link test.
9. **Read-only logins in the Secret Service (F6 B),** one class per forge's way of handing over a token, failing closed when the keyring is locked. Update the README's Services section.
10. **Refuse unsafe install paths and write configuration atomically (F9).**
11. **Pin installs to signed tags (F2 D),** once it is confirmed that `omarchy plugin` can install a given tag or commit.

## Sources

- Positive Security, "Allow arbitrary URLs, expect arbitrary code execution": https://positive.security/blog/url-open-rce
- NVD, CVE-2014-9622 (xdg-utils): https://nvd.nist.gov/vuln/detail/CVE-2014-9622
- Electron security checklist, `shell.openExternal`: https://www.electronjs.org/docs/latest/tutorial/security#15-do-not-use-shellopenexternal-with-untrusted-content
- OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
- OWASP OS Command Injection Defense Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html
- OWASP Secrets Management Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- CPython `urllib/request.py`: https://github.com/python/cpython/blob/main/Lib/urllib/request.py
- urllib3 CVE-2018-20060, Authorization kept across hosts: https://research.averlon.ai/vulnerability-intelligence/cve/CVE-2018-20060
- Python command line options `-P` and `-I`: https://docs.python.org/3/using/cmdline.html
- GitHub CLI advisory GHSA-fqfh-778m-2v32 (runs `git` from the current folder): https://github.com/advisories/GHSA-fqfh-778m-2v32
- NVD, CVE-2024-53858 (GitHub CLI token sent to other hosts): https://nvd.nist.gov/vuln/detail/cve-2024-53858
- GitHub CLI 2.26.0, keyring storage by default: https://github.com/cli/cli/releases/tag/v2.26.0
- glab, keyring storage by default: https://gitlab.com/gitlab-org/cli/-/merge_requests/3528
- Microsoft, MSAL-based Azure CLI: https://learn.microsoft.com/en-us/cli/azure/msal-based-azure-cli
- GitHub, managing personal access tokens: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
- GitLab, personal access tokens and scopes: https://docs.gitlab.com/user/profile/personal_access_tokens/
- freedesktop Secret Service specification: https://specifications.freedesktop.org/secret-service-spec/latest/
- freedesktop notification specification, markup: https://specifications.freedesktop.org/notification/latest/markup.html
- GitHub, rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets
- GitHub, requiring two-factor authentication: https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization
- GitHub, security hardening for GitHub Actions: https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions
- CWE-20, CWE-59, CWE-78, CWE-88, CWE-116, CWE-200, CWE-214, CWE-276, CWE-319, CWE-427, CWE-494: https://cwe.mitre.org/data/definitions/<number>.html
