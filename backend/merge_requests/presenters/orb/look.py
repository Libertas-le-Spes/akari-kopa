from dataclasses import dataclass

from merge_requests.attention.merge_request.merge_request import COMMENTS, MergeRequest
from merge_requests.attention.merge_request.role import MINE, REVIEWING
from merge_requests.attention.pipeline.pipeline import FAILED, NO_PIPELINE, PASSED, RUNNING

GREEN = "#3fb950"
RED = "#f85149"
PURPLE = "#a371f7"
BLUE = "#4c8dff"
YELLOW = "#e3b341"
GREY = "#9aa0a6"

COLOURS = {
    MINE.name: {PASSED.name: GREEN, NO_PIPELINE.name: GREEN, RUNNING.name: GREEN, FAILED.name: RED, COMMENTS: PURPLE},
    REVIEWING.name: {PASSED.name: BLUE, NO_PIPELINE.name: BLUE, RUNNING.name: BLUE, FAILED.name: YELLOW, COMMENTS: BLUE},
}

WORDS = {
    PASSED.name: "passing",
    NO_PIPELINE.name: "no pipeline",
    RUNNING.name: "running",
    FAILED.name: "failing",
    COMMENTS: "comments to answer",
}


@dataclass(frozen=True)
class Look:
    colour: str
    ring: bool
    faded: bool


def look_of(merge_request: MergeRequest, faded: bool) -> Look:
    return Look(COLOURS[merge_request.role.name][merge_request.standing()], merge_request.pipeline.running, faded)


def word_of(merge_request: MergeRequest) -> str:
    return WORDS[merge_request.standing()]


NOT_UPDATED = Look(GREY, ring=True, faded=True)
