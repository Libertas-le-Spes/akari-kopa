from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Conversation:
    unresolved_threads: tuple[datetime, ...] = ()
    comments: tuple[datetime, ...] = ()
    last_answer: datetime | None = None

    def waiting_since(self) -> datetime | None:
        unanswered = [moment for moment in self.comments if self._after_last_answer(moment)]
        return min([*self.unresolved_threads, *unanswered], default=None)

    def _after_last_answer(self, moment: datetime) -> bool:
        return self.last_answer is None or moment > self.last_answer


QUIET = Conversation()
