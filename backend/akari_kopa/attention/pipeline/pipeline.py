from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Pipeline:
    name: str
    running: bool
    outranks_comments: bool


PASSED = Pipeline("passed", running=False, outranks_comments=False)
FAILED = Pipeline("failed", running=False, outranks_comments=True)
RUNNING = Pipeline("running", running=True, outranks_comments=False)
NO_PIPELINE = Pipeline("no pipeline", running=False, outranks_comments=False)

PIPELINES = {pipeline.name: pipeline for pipeline in (PASSED, FAILED, RUNNING, NO_PIPELINE)}


@dataclass(frozen=True)
class PipelineWords:
    passed: frozenset[str]
    failed: frozenset[str]

    def read(self, states: Iterable[str | None]) -> Pipeline:
        reported = [state for state in states if state]
        if not reported:
            return NO_PIPELINE
        if any(state in self.failed for state in reported):
            return FAILED
        return PASSED if all(state in self.passed for state in reported) else RUNNING
