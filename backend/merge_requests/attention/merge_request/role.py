from dataclasses import dataclass


@dataclass(frozen=True)
class Role:
    name: str
    heading: str
    word: str


MINE = Role("mine", "My merge requests", "yours")
REVIEWING = Role("review", "Reviewing", "reviewing")

ROLES = {role.name: role for role in (MINE, REVIEWING)}
