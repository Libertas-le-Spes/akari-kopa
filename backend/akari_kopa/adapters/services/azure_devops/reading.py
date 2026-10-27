from urllib.parse import quote

from akari_kopa.adapters.services.moment import moment
from akari_kopa.attention.merge_request.address_check import address_of
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import Role
from akari_kopa.attention.pipeline.pipeline import PipelineWords
from akari_kopa.attention.repository.follow_up import OWN, SOMEONE_ELSES

WORDS = PipelineWords(frozenset({"succeeded", "partiallySucceeded"}), frozenset({"failed", "canceled"}))
WEB_HOST = "dev.azure.com"


def build_state(build: dict) -> str:
    if build["status"] == "completed":
        return build.get("result")
    return build["status"]


def merge_request(organisation: str, pull_request: dict, builds: list[dict], role: Role) -> MergeRequest:
    repository = pull_request["repository"]
    project = repository["project"]["name"]
    number = pull_request["pullRequestId"]
    return MergeRequest(
        service="azure-devops",
        role=role,
        reference=f"!{number}",
        title=pull_request["title"],
        address=address_of(_web_page(organisation, project, repository["name"], number), WEB_HOST),
        project=f"{project}/{repository['name']}",
        author=pull_request["createdBy"]["displayName"],
        pipeline=WORDS.read(_states(builds)),
        opened=moment(pull_request["creationDate"]),
    )


def _states(builds: list[dict]) -> list[str]:
    states = []
    for build in builds:
        states.append(build_state(build))
    return states


def _web_page(organisation: str, project: str, repository: str, number: int) -> str:
    return f"https://{WEB_HOST}/{_part(organisation)}/{_part(project)}/_git/{_part(repository)}/pullrequest/{number}"


def _part(text: str) -> str:
    return quote(text, safe="")


def repository_of(evaluation: dict):
    for each in evaluation["evaluations"]:
        if not each["value"]:
            return SOMEONE_ELSES
    return OWN
