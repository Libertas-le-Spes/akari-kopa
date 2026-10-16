import re
from datetime import datetime

BEYOND_MICROSECONDS = re.compile(r"(\.\d{6})\d+")


def moment(text: str) -> datetime:
    return datetime.fromisoformat(BEYOND_MICROSECONDS.sub(r"\1", text).replace("Z", "+00:00"))


def moments(texts) -> tuple[datetime, ...]:
    return tuple(moment(text) for text in texts if text)


def latest(texts) -> datetime | None:
    return max(moments(texts), default=None)
