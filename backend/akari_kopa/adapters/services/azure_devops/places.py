from urllib.parse import quote

PROFILES = "https://app.vssps.visualstudio.com/_apis"
ORGANISATIONS = "https://dev.azure.com"
HOSTS = frozenset({"app.vssps.visualstudio.com", "dev.azure.com"})


def part(text) -> str:
    return quote(str(text), safe="")


def organisation_api(organisation: str) -> str:
    return f"{ORGANISATIONS}/{part(organisation)}/_apis"


def project_api(organisation: str, project_id: str) -> str:
    return f"{ORGANISATIONS}/{part(organisation)}/{part(project_id)}/_apis"


def pull_request_api(organisation: str, pull_request: dict) -> str:
    repository = pull_request["repository"]
    api = project_api(organisation, repository["project"]["id"])
    return f"{api}/git/repositories/{part(repository['id'])}/pullRequests/{part(pull_request['pullRequestId'])}"
