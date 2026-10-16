from datetime import datetime

from merge_requests.attention.conversation.conversation import Conversation
from merge_requests.attention.merge_request.merge_request import MergeRequest
from merge_requests.attention.merge_request.role import ROLES
from merge_requests.attention.pipeline.pipeline import PIPELINES
from merge_requests.attention.repository.follow_up import REPOSITORIES


def encoded(merge_request: MergeRequest) -> dict:
    conversation = merge_request.conversation
    return {
        **{name: getattr(merge_request, name) for name in ("service", "reference", "title", "url", "project", "author")},
        "role": merge_request.role.name,
        "pipeline": merge_request.pipeline.name,
        "opened": merge_request.opened.isoformat(),
        "repository": merge_request.repository.name,
        "unresolvedThreads": [moment.isoformat() for moment in conversation.unresolved_threads],
        "comments": [moment.isoformat() for moment in conversation.comments],
        "lastAnswer": conversation.last_answer.isoformat() if conversation.last_answer else None,
    }


def decoded(raw: dict) -> MergeRequest:
    return MergeRequest(
        **{name: raw[name] for name in ("service", "reference", "title", "url", "project", "author")},
        role=ROLES[raw["role"]],
        pipeline=PIPELINES[raw["pipeline"]],
        opened=datetime.fromisoformat(raw["opened"]),
        repository=REPOSITORIES[raw["repository"]],
        conversation=Conversation(
            tuple(datetime.fromisoformat(moment) for moment in raw["unresolvedThreads"]),
            tuple(datetime.fromisoformat(moment) for moment in raw["comments"]),
            datetime.fromisoformat(raw["lastAnswer"]) if raw["lastAnswer"] else None,
        ),
    )
