from datetime import datetime

from akari_kopa.adapters.storage.conversation_codec import decoded_conversation, encoded_conversation
from akari_kopa.attention.merge_request.address_check import address_of
from akari_kopa.attention.merge_request.merge_request import MergeRequest
from akari_kopa.attention.merge_request.role import ROLES
from akari_kopa.attention.merge_request.web_address import RefusedAddress, WebAddress
from akari_kopa.attention.pipeline.pipeline import PIPELINES
from akari_kopa.attention.repository.follow_up import REPOSITORIES


def encoded(merge_request: MergeRequest) -> dict:
    found = {
        "service": merge_request.service,
        "reference": merge_request.reference,
        "title": merge_request.title,
        "address": _encoded_address(merge_request.address),
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
        address=_decoded_address(raw["address"]),
        project=raw["project"],
        author=raw["author"],
        pipeline=PIPELINES[raw["pipeline"]],
        opened=datetime.fromisoformat(raw["opened"]),
        repository=REPOSITORIES[raw["repository"]],
        conversation=decoded_conversation(raw),
    )


def _stored_web_address(address: WebAddress) -> dict:
    return {"kind": "web", "text": address.text, "forgeHost": address.forge_host}


def _stored_refused_address(address: RefusedAddress) -> dict:
    return {"kind": "refused", "reason": address.reason, "forgeHost": address.forge_host}


def _web_address(raw: dict) -> WebAddress | RefusedAddress:
    return address_of(raw["text"], raw["forgeHost"])


def _refused_address(raw: dict) -> RefusedAddress:
    return RefusedAddress(raw["reason"], raw["forgeHost"])


ADDRESSES_STORED = {WebAddress: _stored_web_address, RefusedAddress: _stored_refused_address}
STORED_ADDRESSES = {"web": _web_address, "refused": _refused_address}


def _encoded_address(address: WebAddress | RefusedAddress) -> dict:
    return ADDRESSES_STORED[type(address)](address)


def _decoded_address(raw: dict) -> WebAddress | RefusedAddress:
    return STORED_ADDRESSES[raw["kind"]](raw)
