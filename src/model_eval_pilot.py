#!/usr/bin/env python3
"""Run a side-effect-bounded llama.cpp model-evaluation pilot.

The script starts exactly one child llama-server process on loopback, runs a
small deterministic prompt suite, records objective checks and runtime
metrics, then terminates only the child process it started.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_MODEL = ""
DEFAULT_SERVER = os.environ.get("LLAMA_SERVER", "llama-server")


class EvaluationError(RuntimeError):
    """Raised when the evaluation cannot continue safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tail_text(path: Path, lines: int = 80) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return "\n".join(content.splitlines()[-lines:])


def optional_int(value: str) -> int | None:
    value = value.strip()
    if value.upper() in {"N/A", "NA", "[N/A]", "-"}:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def gpu_snapshot() -> dict[str, Any]:
    command = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        rows: list[dict[str, Any]] = []
        for line in completed.stdout.splitlines():
            fields = [field.strip() for field in line.split(",")]
            if len(fields) != 5:
                continue
            name, total, used, utilization, temperature = fields
            rows.append(
                {
                    "name": name,
                    "memory_total_mib": optional_int(total),
                    "memory_used_mib": optional_int(used),
                    "utilization_gpu_pct": optional_int(utilization),
                    "temperature_c": optional_int(temperature),
                }
            )
        return {"available": True, "gpus": rows}
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        return {"available": False, "error": str(exc), "gpus": []}


class GpuSampler:
    def __init__(self, interval_seconds: float = 0.5) -> None:
        self.interval_seconds = interval_seconds
        self.samples: list[dict[str, Any]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self.samples.append(gpu_snapshot())

        def worker() -> None:
            while not self._stop.wait(self.interval_seconds):
                self.samples.append(gpu_snapshot())

        self._thread = threading.Thread(target=worker, name="gpu-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self.samples.append(gpu_snapshot())

    def summary(self) -> dict[str, Any]:
        gpu_rows = [
            gpu
            for sample in self.samples
            for gpu in sample.get("gpus", [])
        ]
        if not gpu_rows:
            return {"available": False, "samples": len(self.samples)}
        memory_values = [
            row["memory_used_mib"]
            for row in gpu_rows
            if isinstance(row.get("memory_used_mib"), int)
        ]
        utilization_values = [
            row["utilization_gpu_pct"]
            for row in gpu_rows
            if isinstance(row.get("utilization_gpu_pct"), int)
        ]
        temperature_values = [
            row["temperature_c"]
            for row in gpu_rows
            if isinstance(row.get("temperature_c"), int)
        ]
        return {
            "available": True,
            "samples": len(self.samples),
            "framebuffer_memory_available": bool(memory_values),
            "max_memory_used_mib": max(memory_values) if memory_values else None,
            "max_utilization_gpu_pct": max(utilization_values)
            if utilization_values
            else None,
            "max_temperature_c": max(temperature_values)
            if temperature_values
            else None,
            "gpus": sorted({row["name"] for row in gpu_rows}),
        }


def http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 10,
) -> tuple[int, dict[str, Any], float]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            status = response.status
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    elapsed = time.perf_counter() - started
    try:
        parsed = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        parsed = {"raw": raw}
    if not isinstance(parsed, dict):
        parsed = {"value": parsed}
    return status, parsed, elapsed


def http_text(url: str, timeout: float = 10) -> str:
    request = Request(url, headers={"Accept": "text/plain"}, method="GET")
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def build_prompts() -> list[dict[str, Any]]:
    needle = "藍寶石-4721"
    sections = []
    for index in range(96):
        text = f"文件段落 {index:03d}：這是一段用來測試長文本定位能力的背景資料。"
        if index == 47:
            text += f" 本段的關鍵值是 {needle}。"
        sections.append(text)
    long_context = "\n".join(sections)
    return [
        {
            "id": "zh_tw_instruction",
            "prompt": (
                "請使用台灣繁體中文回答。只列出三點，說明部署本地語言模型時"
                "為什麼要固定測試參數；不要加入開場白。"
            ),
            "checks": ["non_empty", "three_bullets"],
        },
        {
            "id": "math_exact",
            "prompt": "計算 37 × 48。只回傳阿拉伯數字，不要附加說明。",
            "checks": ["math_exact"],
        },
        {
            "id": "json_schema",
            "prompt": (
                "請只輸出合法 JSON，不要 markdown code fence。格式必須是 "
                '{"answer":"台北市","language":"zh-TW"}，回答台灣的首都是哪裡。'
            ),
            "checks": ["json_schema"],
        },
        {
            "id": "code_generation",
            "prompt": (
                "請用 Python 寫一個 is_palindrome(text) 函式，忽略大小寫與空白，"
                "並附上至少兩個 assert 測試。只輸出程式碼。"
            ),
            "checks": ["code_shape"],
        },
        {
            "id": "long_context_needle",
            "prompt": (
                "請閱讀以下文件，只回答關鍵值本身，不要附加說明。\n\n"
                f"{long_context}\n\n關鍵值是什麼？"
            ),
            "checks": ["needle"],
        },
    ]


def wait_for_health(
    base_url: str,
    process: subprocess.Popen[str],
    log_path: Path,
    timeout_seconds: float,
) -> float:
    started = time.perf_counter()
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise EvaluationError(
                f"llama-server exited with code {process.returncode}.\n"
                f"Log tail:\n{tail_text(log_path)}"
            )
        try:
            status, _, _ = http_json("GET", f"{base_url}/health", timeout=2)
            if status == 200:
                return time.perf_counter() - started
        except (OSError, URLError, TimeoutError):
            pass
        time.sleep(0.5)
    raise EvaluationError(
        f"health check timed out after {timeout_seconds:.1f}s.\n"
        f"Log tail:\n{tail_text(log_path)}"
    )


def stop_child(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


def extract_message_fields(response: dict[str, Any]) -> tuple[str, str, str | None]:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        return "", "", None
    first = choices[0]
    if not isinstance(first, dict):
        return "", "", None
    message = first.get("message")
    if isinstance(message, dict):
        content = message.get("content", "")
        reasoning = message.get("reasoning_content", "")
        finish_reason = first.get("finish_reason")
        return (
            content if isinstance(content, str) else str(content),
            reasoning if isinstance(reasoning, str) else str(reasoning),
            finish_reason if isinstance(finish_reason, str) else None,
        )
    text = first.get("text", "")
    finish_reason = first.get("finish_reason")
    return (
        text if isinstance(text, str) else str(text),
        "",
        finish_reason if isinstance(finish_reason, str) else None,
    )


def checks_for(prompt_id: str, content: str) -> dict[str, bool]:
    checks: dict[str, bool] = {"non_empty": bool(content.strip())}
    if prompt_id == "zh_tw_instruction":
        bullet_lines = [
            line
            for line in content.splitlines()
            if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+", line)
        ]
        checks["three_bullets"] = len(bullet_lines) == 3
    elif prompt_id == "math_exact":
        checks["math_exact"] = bool(re.fullmatch(r"\s*1776\s*", content))
    elif prompt_id == "json_schema":
        try:
            parsed = json.loads(content)
            checks["json_schema"] = (
                isinstance(parsed, dict)
                and parsed.get("answer") == "台北市"
                and parsed.get("language") == "zh-TW"
                and set(parsed) == {"answer", "language"}
            )
        except json.JSONDecodeError:
            checks["json_schema"] = False
    elif prompt_id == "code_generation":
        checks["code_shape"] = (
            "def is_palindrome" in content
            and "assert" in content
        )
    elif prompt_id == "long_context_needle":
        checks["needle"] = bool(re.search(r"藍寶石\s*-\s*4721", content))
    return checks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--server-bin", default=DEFAULT_SERVER)
    parser.add_argument("--port", type=int, default=18080)
    parser.add_argument("--ctx-size", type=int, default=8192)
    parser.add_argument("--threads", type=int, default=12)
    parser.add_argument("--n-gpu-layers", type=int, default=999)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument(
        "--reasoning",
        choices=("on", "off", "auto"),
        default="off",
        help="llama.cpp reasoning mode; off is preferred for this objective pilot",
    )
    parser.add_argument("--startup-timeout", type=float, default=180)
    parser.add_argument("--request-timeout", type=float, default=120)
    parser.add_argument(
        "--output",
        default="",
        help="結果目錄；未指定時建立於 ./results/<UTC timestamp>",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model = Path(args.model).expanduser()
    server_bin = Path(args.server_bin).expanduser()
    if not model.is_file():
        raise EvaluationError(f"model file does not exist: {model}")
    if not server_bin.is_file() or not os.access(server_bin, os.X_OK):
        raise EvaluationError(f"llama-server is not executable: {server_bin}")
    if not 1024 <= args.port <= 65535:
        raise EvaluationError("port must be between 1024 and 65535")

    output_dir = (
        Path(args.output).expanduser()
        if args.output
        else Path("results") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "server.log"
    report_path = output_dir / "report.json"
    base_url = f"http://127.0.0.1:{args.port}"

    command = [
        str(server_bin),
        "--model",
        str(model),
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--ctx-size",
        str(args.ctx_size),
        "--n-gpu-layers",
        str(args.n_gpu_layers),
        "--threads",
        str(args.threads),
        "--parallel",
        "1",
        "--metrics",
        "--jinja",
        "--reasoning",
        args.reasoning,
    ]

    report: dict[str, Any] = {
        "started_at": utc_now(),
        "model": str(model),
        "model_size_bytes": model.stat().st_size,
        "server_binary": str(server_bin),
        "configuration": {
            "port": args.port,
            "ctx_size": args.ctx_size,
            "threads": args.threads,
            "n_gpu_layers": args.n_gpu_layers,
            "parallel": 1,
            "max_tokens": args.max_tokens,
            "reasoning": args.reasoning,
            "seed": 42,
            "temperature": 0.2,
            "top_p": 0.9,
        },
        "command": command,
        "tests": [],
    }

    process: subprocess.Popen[str] | None = None
    sampler = GpuSampler()
    try:
        with log_path.open("w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
        sampler.start()
        report["load_time_seconds"] = wait_for_health(
            base_url, process, log_path, args.startup_timeout
        )
        prompts = build_prompts()
        for test in prompts:
            request_payload = {
                "model": "local-pilot",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是測試中的本地模型。請嚴格遵守使用者要求，"
                            "不要捏造工具結果。"
                        ),
                    },
                    {"role": "user", "content": test["prompt"]},
                ],
                "temperature": 0.2,
                "top_p": 0.9,
                "seed": 42,
                "max_tokens": args.max_tokens,
                "stream": False,
            }
            started = time.perf_counter()
            result: dict[str, Any] = {
                "id": test["id"],
                "checks_expected": test["checks"],
                "prompt": test["prompt"],
            }
            try:
                status, response, elapsed = http_json(
                    "POST",
                    f"{base_url}/v1/chat/completions",
                    request_payload,
                    timeout=args.request_timeout,
                )
                content, reasoning_content, finish_reason = extract_message_fields(
                    response
                )
                usage = response.get("usage", {})
                completion_tokens = (
                    usage.get("completion_tokens")
                    if isinstance(usage, dict)
                    else None
                )
                result.update(
                    {
                        "http_status": status,
                        "elapsed_seconds": elapsed,
                        "content": content,
                        "reasoning_content": reasoning_content,
                        "finish_reason": finish_reason,
                        "usage": usage,
                        "tokens_per_second": (
                            completion_tokens / elapsed
                            if isinstance(completion_tokens, (int, float))
                            and elapsed > 0
                            else None
                        ),
                        "checks": checks_for(test["id"], content),
                    }
                )
                if status != 200:
                    result["error"] = response
            except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                result["elapsed_seconds"] = time.perf_counter() - started
                result["error"] = str(exc)
                result["checks"] = {check: False for check in test["checks"]}
            report["tests"].append(result)

        try:
            report["metrics_excerpt"] = "\n".join(
                line
                for line in http_text(f"{base_url}/metrics").splitlines()
                if any(token in line for token in ("tokens", "prompt", "eval", "requests"))
            )[:12000]
        except (OSError, URLError, TimeoutError) as exc:
            report["metrics_error"] = str(exc)
    finally:
        sampler.stop()
        report["gpu_summary"] = sampler.summary()
        if process is not None:
            stop_child(process)
            report["server_exit_code"] = process.returncode
        report["server_log"] = str(log_path)
        report["finished_at"] = utc_now()
        total_checks = 0
        passed_checks = 0
        successful_requests = 0
        for test in report["tests"]:
            checks = test.get("checks", {})
            if test.get("http_status") == 200:
                successful_requests += 1
            total_checks += len(checks)
            passed_checks += sum(bool(value) for value in checks.values())
        report["summary"] = {
            "request_count": len(report["tests"]),
            "successful_requests": successful_requests,
            "objective_checks_passed": passed_checks,
            "objective_checks_total": total_checks,
            "objective_check_pass_rate": (
                passed_checks / total_checks if total_checks else None
            ),
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    print(
        json.dumps(
            {
                "report": str(report_path),
                "server_log": str(log_path),
                "summary": report["summary"],
                "gpu_summary": report["gpu_summary"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except EvaluationError as exc:
        print(f"ERROR: {exc}", flush=True)
        raise SystemExit(2)
