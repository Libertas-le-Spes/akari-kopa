from datetime import datetime

from akari_kopa.adapters.storage.conversation_codec import decoded_conversation, encoded_conversation
from akari_kopa.attention.merge_request.address_check import address_of
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import ROLES
from akari_kopa.attention.pipeline.pipeline import PIPELINES
from akari_kopa.attention.repository.follow_up import REPOSITORIES


def encoded(merge_request: MergeRequest) -> dict:
    found = {
        "service": merge_request.service,
        "reference": merge_request.reference,
        "title": merge_request.title,
        "address": merge_request.address.text,
        "forgeHost": merge_request.address.forge_host,
        "project": merge_request.project,
        "author": merge_request.author,
        "role": merge_request.role.name,
        "pipeline": merge_request.pipeline.name,
        "opened": merge_request.opened.isoformat(),
        "repository": merge_request.repository.name,
    }
    found.update(encoded_conversation(merge_request.conversation))
    return found


def decoded(raw: dict) -> MergeRequest:
    return MergeRequest(
        service=raw["service"],
        role=ROLES[raw["role"]],
        reference=raw["reference"],
        title=raw["title"],
        address=address_of(raw["address"], raw["forgeHost"]),
        project=raw["project"],
        author=raw["author"],
        pipeline=PIPELINES[raw["pipeline"]],
        opened=datetime.fromisoformat(raw["opened"]),
        repository=REPOSITORIES[raw["repository"]],
        conversation=decoded_conversation(raw),
    )
