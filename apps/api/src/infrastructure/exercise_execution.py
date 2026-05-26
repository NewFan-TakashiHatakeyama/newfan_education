from __future__ import annotations

import ast
import io
import json
import sqlite3
import subprocess
import sys
import textwrap
import traceback
from contextlib import redirect_stdout
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
        kind = str(exercise.get("kind", "notebook"))
        metadata = exercise.get("metadata") or {}
        if kind in {"notebook", "sql"}:
            return self._run_pyodide_compatible(kind=kind, metadata=metadata, code=code)
        return self._run_docker_sandbox(kind=kind, metadata=metadata, code=code)

    def _run_pyodide_compatible(
        self,
        *,
        kind: str,
        metadata: dict[str, Any],
        code: str,
    ) -> ExerciseExecutionResult:
        if kind == "sql":
            return self._run_sql_pipeline(code=code)
        return self._run_notebook_pipeline(metadata=metadata, code=code)

    def _run_notebook_pipeline(
        self,
        *,
        metadata: dict[str, Any],
        code: str,
    ) -> ExerciseExecutionResult:
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    return ExerciseExecutionResult(
                        status="failed",
                        stdout="",
                        stderr="Imports are restricted in pyodide-compatible mode.",
                        engine="pyodide",
                        pipeline="notebook",
                        details={"reason": "import_restricted"},
                    )
            safe_builtins = {
                "len": len,
                "sum": sum,
                "min": min,
                "max": max,
                "range": range,
                "list": list,
                "dict": dict,
                "set": set,
                "sorted": sorted,
                "enumerate": enumerate,
                "zip": zip,
                "abs": abs,
                "round": round,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "print": print,
            }
            namespace: dict[str, Any] = {"__builtins__": safe_builtins}
            stdout_buffer = io.StringIO()
            with redirect_stdout(stdout_buffer):
                exec(compile(tree, "<exercise>", "exec"), namespace, namespace)
            output = stdout_buffer.getvalue().strip()
            required_output_keyword = str(metadata.get("requiredOutputKeyword", "")).strip().lower()
            if required_output_keyword and required_output_keyword not in output.lower():
                return ExerciseExecutionResult(
                    status="failed",
                    stdout=output,
                    stderr=f"Output must include keyword: {required_output_keyword}",
                    engine="pyodide",
                    pipeline="notebook",
                    details={"requiredOutputKeyword": required_output_keyword},
                )
            return ExerciseExecutionResult(
                status="passed",
                stdout=output or "Notebook cell executed successfully.",
                stderr="",
                engine="pyodide",
                pipeline="notebook",
                details={"language": metadata.get("language", "python")},
            )
        except Exception as exc:  # noqa: BLE001
            return ExerciseExecutionResult(
                status="failed",
                stdout="",
                stderr=f"{type(exc).__name__}: {exc}",
                engine="pyodide",
                pipeline="notebook",
                details={"traceback": traceback.format_exc(limit=2)},
            )

    def _run_sql_pipeline(self, *, code: str) -> ExerciseExecutionResult:
        conn = sqlite3.connect(":memory:")
        try:
            cur = conn.cursor()
            cur.execute("CREATE TABLE progress_events (learner_id TEXT, completed_items INTEGER, total_items INTEGER);")
            cur.executemany(
                "INSERT INTO progress_events (learner_id, completed_items, total_items) VALUES (?, ?, ?);",
                [("learner-a", 8, 10), ("learner-b", 3, 10), ("learner-c", 10, 10)],
            )
            statement = code.strip().rstrip(";")
            if not statement.lower().startswith("select"):
                return ExerciseExecutionResult(
                    status="failed",
                    stdout="",
                    stderr="SQL must start with SELECT.",
                    engine="pyodide",
                    pipeline="sql",
                    details={"dialect": "sqlite"},
                )
            rows = cur.execute(statement).fetchall()
            columns = [column[0] for column in (cur.description or [])]
            if not rows:
                return ExerciseExecutionResult(
                    status="failed",
                    stdout="0 rows returned.",
                    stderr="Query returned no rows.",
                    engine="pyodide",
                    pipeline="sql",
                    details={"columns": columns, "rowCount": 0},
                )
            stdout = json.dumps({"columns": columns, "rows": rows[:5]}, ensure_ascii=False)
            return ExerciseExecutionResult(
                status="passed",
                stdout=stdout,
                stderr="",
                engine="pyodide",
                pipeline="sql",
                details={"columns": columns, "rowCount": len(rows)},
            )
        except Exception as exc:  # noqa: BLE001
            return ExerciseExecutionResult(
                status="failed",
                stdout="",
                stderr=f"{type(exc).__name__}: {exc}",
                engine="pyodide",
                pipeline="sql",
                details={"traceback": traceback.format_exc(limit=2)},
            )
        finally:
            conn.close()

    def _run_docker_sandbox(
        self,
        *,
        kind: str,
        metadata: dict[str, Any],
        code: str,
    ) -> ExerciseExecutionResult:
        if not self._settings.docker_sandbox_enabled:
            return self._run_local_sandbox_fallback(
                kind=kind,
                harness=self._build_harness(kind=kind, metadata=metadata),
                code=code,
                reason="sandbox_disabled",
            )

        harness = self._build_harness(kind=kind, metadata=metadata)
        try:
            proc = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "-i",
                    self._settings.docker_sandbox_image,
                    "python",
                    "-c",
                    harness,
                ],
                input=code,
                text=True,
                capture_output=True,
                timeout=self._settings.docker_sandbox_timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self._run_local_sandbox_fallback(
                kind=kind,
                harness=harness,
                code=code,
                reason="docker_timeout",
            )
        except FileNotFoundError:
            return self._run_local_sandbox_fallback(
                kind=kind,
                harness=harness,
                code=code,
                reason="docker_not_found",
            )

        stdout = (proc.stdout or "").strip()
        stderr = proc.stderr.strip()
        if proc.returncode != 0 and (
            "Cannot connect to the Docker daemon" in stderr
            or "is the docker daemon running" in stderr.lower()
        ):
            return self._run_local_sandbox_fallback(
                kind=kind,
                harness=harness,
                code=code,
                reason="docker_daemon_unavailable",
            )
        if proc.returncode != 0:
            return ExerciseExecutionResult(
                status="failed",
                stdout=stdout,
                stderr=stderr or "Sandbox returned non-zero status.",
                engine="docker_sandbox",
                pipeline=kind,
                details={"exitCode": proc.returncode},
            )
        try:
            parsed = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            return ExerciseExecutionResult(
                status="failed",
                stdout=stdout,
                stderr="Sandbox returned invalid JSON result.",
                engine="docker_sandbox",
                pipeline=kind,
                details={},
            )
        status = str(parsed.get("status", "failed"))
        return ExerciseExecutionResult(
            status=status,
            stdout=str(parsed.get("stdout", "")),
            stderr=str(parsed.get("stderr", "")),
            engine="docker_sandbox",
            pipeline=kind,
            details=parsed.get("details", {}),
        )

    def _run_local_sandbox_fallback(
        self,
        *,
        kind: str,
        harness: str,
        code: str,
        reason: str,
    ) -> ExerciseExecutionResult:
        try:
            proc = subprocess.run(
                [sys.executable, "-c", harness],
                input=code,
                text=True,
                capture_output=True,
                timeout=self._settings.docker_sandbox_timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return ExerciseExecutionResult(
                status="failed",
                stdout="",
                stderr="Fallback sandbox execution timed out.",
                engine="docker_sandbox",
                pipeline=kind,
                details={"fallback": "local", "reason": reason},
            )

        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        if proc.returncode != 0:
            return ExerciseExecutionResult(
                status="failed",
                stdout=stdout,
                stderr=stderr or "Local fallback sandbox failed.",
                engine="docker_sandbox",
                pipeline=kind,
                details={"fallback": "local", "reason": reason, "exitCode": proc.returncode},
            )
        try:
            parsed = json.loads(stdout) if stdout else {}
        except json.JSONDecodeError:
            return ExerciseExecutionResult(
                status="failed",
                stdout=stdout,
                stderr="Local fallback returned invalid JSON result.",
                engine="docker_sandbox",
                pipeline=kind,
                details={"fallback": "local", "reason": reason},
            )
        details = parsed.get("details", {}) if isinstance(parsed, dict) else {}
        if isinstance(details, dict):
            details["fallback"] = "local"
            details["fallbackReason"] = reason
        return ExerciseExecutionResult(
            status=str(parsed.get("status", "failed")),
            stdout=str(parsed.get("stdout", "")),
            stderr=str(parsed.get("stderr", "")),
            engine="docker_sandbox",
            pipeline=kind,
            details=details if isinstance(details, dict) else {"fallback": "local", "reason": reason},
        )

    def _build_harness(self, *, kind: str, metadata: dict[str, Any]) -> str:
        rubric = json.dumps(metadata, ensure_ascii=False)
        return textwrap.dedent(
            f"""
            import io
            import json
            import math
            import sys
            import traceback
            from contextlib import redirect_stdout

            kind = {kind!r}
            metadata = {rubric}
            user_code = sys.stdin.read()
            namespace = {{}}
            stdout_buffer = io.StringIO()
            result = {{"status": "failed", "stdout": "", "stderr": "", "details": {{}}}}
            try:
                with redirect_stdout(stdout_buffer):
                    exec(compile(user_code, "<sandbox>", "exec"), namespace, namespace)
                output = namespace.get("OUTPUT")
                if kind == "rag":
                    queries = output.get("queries", []) if isinstance(output, dict) else []
                    if not queries:
                        raise ValueError("OUTPUT.queries is required")
                    hits = 0
                    reciprocal_sum = 0.0
                    for query in queries:
                        relevant = query.get("relevant")
                        retrieved = query.get("retrieved", [])
                        if relevant in retrieved:
                            hits += 1
                            reciprocal_sum += 1.0 / (retrieved.index(relevant) + 1)
                    total = len(queries)
                    hit_at_k = hits / total
                    mrr = reciprocal_sum / total
                    passed = hit_at_k >= float(metadata.get("minHitAtK", 0.5)) and mrr >= float(metadata.get("minMRR", 0.4))
                    result["status"] = "passed" if passed else "failed"
                    result["stdout"] = f"hit@k={{hit_at_k:.2f}} mrr={{mrr:.2f}}"
                    result["details"] = {{"hitAtK": hit_at_k, "mrr": mrr}}
                elif kind == "ocr":
                    if not isinstance(output, dict):
                        raise ValueError("OUTPUT must be JSON-like dict")
                    required = ["vendor", "amount", "date"]
                    missing = [k for k in required if k not in output or output.get(k) in ("", None)]
                    if missing:
                        result["status"] = "failed"
                        result["stdout"] = json.dumps(output, ensure_ascii=False)
                        result["stderr"] = f"Missing fields: {{', '.join(missing)}}"
                        result["details"] = {{"missing": missing}}
                    else:
                        result["status"] = "passed"
                        result["stdout"] = json.dumps(output, ensure_ascii=False)
                        result["details"] = {{"validatedFields": required}}
                else:
                    result["status"] = "failed"
                    result["stderr"] = "Unsupported sandbox pipeline."
                printed = stdout_buffer.getvalue().strip()
                if printed:
                    result["details"]["printOutput"] = printed
            except Exception as exc:
                result["status"] = "failed"
                result["stderr"] = f"{{type(exc).__name__}}: {{exc}}"
                result["details"]["traceback"] = traceback.format_exc(limit=2)

            print(json.dumps(result, ensure_ascii=False))
            """
        )
