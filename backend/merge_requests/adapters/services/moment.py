from datetime import datetime


def moment(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def moments(texts) -> tuple[datetime, ...]:
    return tuple(moment(text) for text in texts if text)


def latest(texts) -> datetime | None:
    return max(moments(texts), default=None)
