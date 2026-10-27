from akari_kopa.adapters.services.gitea.tea import Tea, TeaLogin


class ConversationParts:
    def __init__(self, tea: Tea):
        self.tea = tea

    def pull_and_status(self, login: TeaLogin, issue: dict) -> tuple[dict, dict]:
        repo = issue["repository"]["full_name"]
        pull = self.tea.get(login, f"/repos/{repo}/pulls/{issue['number']}")
        return pull, self.tea.get(login, f"/repos/{repo}/commits/{pull['head']['sha']}/status")

    def of(self, login: TeaLogin, issue: dict, pull: dict) -> tuple[list[dict], list[dict], list[dict], dict]:
        repo = issue["repository"]["full_name"]
        number = issue["number"]
        reviews = self.tea.get(login, f"/repos/{repo}/pulls/{number}/reviews")
        comments = self.tea.get(login, f"/repos/{repo}/issues/{number}/comments")
        head_commit = self.tea.get(login, f"/repos/{repo}/git/commits/{pull['head']['sha']}")
        return comments, reviews, self._review_comments(login, repo, number, reviews), head_commit

    def _review_comments(self, login: TeaLogin, repo: str, number: int, reviews: list[dict]) -> list[dict]:
        said = []
        for review in reviews:
            said += self.tea.get(login, f"/repos/{repo}/pulls/{number}/reviews/{review['id']}/comments")
        return said
