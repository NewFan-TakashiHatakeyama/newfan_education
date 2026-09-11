"""Fail closed until a separate authenticated execution service is deployed."""
from dataclasses import dataclass
from typing import Any
from infrastructure.settings import Settings

@dataclass(slots=True)
class ExerciseExecutionResult:
    status: str
    stdout: str
    stderr: str
    engine: str
    pipeline: str
    details: dict[str, Any]

class ExerciseExecutionGateway:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def run(self, exercise: dict, code: str) -> ExerciseExecutionResult:
        return ExerciseExecutionResult(
            status="failed", stdout="",
            stderr="隔離実行基盤が未接続のため実行できません。採点は行われていません。",
            engine="unavailable", pipeline=str(exercise.get("kind", "unknown")),
            details={"reason": "isolated_runner_unavailable", "executed": False},
        )
