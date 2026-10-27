from datetime import datetime

from akari_kopa.attention.conversation.conversation import Conversation


def encoded_conversation(conversation: Conversation) -> dict:
    return {
        "unresolvedThreads": _encoded_moments(conversation.unresolved_threads),
        "comments": _encoded_moments(conversation.comments),
        "lastAnswer": _encoded_moment(conversation.last_answer),
    }


def decoded_conversation(raw: dict) -> Conversation:
    return Conversation(_decoded_moments(raw["unresolvedThreads"]), _decoded_moments(raw["comments"]), _decoded_moment(raw["lastAnswer"]))


def _encoded_moments(moments: tuple[datetime, ...]) -> list[str]:
    encoded = []
    for moment in moments:
        encoded.append(moment.isoformat())
    return encoded


def _decoded_moments(texts: list[str]) -> tuple[datetime, ...]:
    decoded = []
    for text in texts:
        decoded.append(datetime.fromisoformat(text))
    return tuple(decoded)


def _encoded_moment(moment: datetime | None) -> str | None:
    if moment is None:
        return None
    return moment.isoformat()


def _decoded_moment(text: str | None) -> datetime | None:
    if text is None:
        return None
    return datetime.fromisoformat(text)
