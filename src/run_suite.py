#!/usr/bin/env python3
"""Run the public Minimum Agent Suite for one model configuration.

The wrapper starts the suite once per seed on loopback only. Model weights and
llama.cpp are external prerequisites and are never downloaded or published by
this project.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SEEDS = (42, 43)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_executable(value: str) -> Path:
    candidate = Path(value).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    found = shutil.which(value)
    if found:
        return Path(found).resolve()
    raise SystemExit(f"llama-server is not executable or not on PATH: {value}")


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Path to the main GGUF model")
    parser.add_argument(
        "--server-bin",
        default=os.environ.get("LLAMA_SERVER", "llama-server"),
        help="llama-server path or executable name",
    )
    parser.add_argument("--model-draft", default="", help="Optional MTP/speculative draft GGUF")
    parser.add_argument("--spec-type", default="", help="For MTP, normally draft-mtp")
    parser.add_argument(
        "--spec-draft-n-max",
        type=int,
        default=2,
        help="Maximum draft tokens per speculative iteration (default: 2)",
    )
    parser.add_argument("--flash-attn", choices=("on", "off", "auto"), default="")
    parser.add_argument("--system-prompt-file", default="")
    parser.add_argument("--output-root", default="")
    parser.add_argument("--base-port", type=int, default=19000)
    parser.add_argument("--ctx-size", type=int, default=8192)
    parser.add_argument("--threads", type=int, default=12)
    parser.add_argument("--n-gpu-layers", type=int, default=999)
    parser.add_argument("--max-tokens", type=int, default=768)
    parser.add_argument("--request-timeout", type=float, default=45)
    parser.add_argument("--seeds", default="42,43", help="Comma-separated deterministic seeds")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    suite = Path(__file__).with_name("agent_eval_suite.py").resolve()
    model = Path(args.model).expanduser().resolve()
    if not model.is_file():
        raise SystemExit(f"model file does not exist: {model}")
    server = resolve_executable(args.server_bin)
    draft = Path(args.model_draft).expanduser().resolve() if args.model_draft else None
    if draft is not None and not draft.is_file():
        raise SystemExit(f"draft model file does not exist: {draft}")
    prompt = Path(args.system_prompt_file).expanduser().resolve() if args.system_prompt_file else None
    if prompt is not None and not prompt.is_file():
        raise SystemExit(f"system prompt file does not exist: {prompt}")
    try:
        seeds = tuple(int(value.strip()) for value in args.seeds.split(",") if value.strip())
    except ValueError as exc:
        raise SystemExit("--seeds must be comma-separated integers") from exc
    if not seeds:
        raise SystemExit("--seeds must contain at least one seed")
    if not 1024 <= args.base_port <= 65534:
        raise SystemExit("--base-port must leave room for all selected seeds")

    root = (
        Path(args.output_root).expanduser()
        if args.output_root
        else Path("results") / f"minimum-agent-{utc_stamp()}"
    )
    root.mkdir(parents=True, exist_ok=True)
    comparison: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "suite": str(suite),
        "server_binary": str(server),
        "configuration": {
            "seeds": list(seeds),
            "model": str(model),
            "model_draft": str(draft) if draft else None,
            "spec_type": args.spec_type or None,
            "spec_draft_n_max": args.spec_draft_n_max if args.spec_type else None,
            "flash_attn": args.flash_attn or None,
            "ctx_size": args.ctx_size,
            "threads": args.threads,
            "n_gpu_layers": args.n_gpu_layers,
            "max_tokens": args.max_tokens,
            "request_timeout": args.request_timeout,
            "system_prompt_file": str(prompt) if prompt else None,
            "loopback_only": True,
        },
        "candidates": [],
    }
    comparison_path = root / "comparison.json"
    runner_log = root / "runner.log"
    for index, seed in enumerate(seeds):
        port = args.base_port + index
        if not port_is_free(port):
            raise SystemExit(f"loopback port is already in use: {port}")
        result_dir = root / f"seed-{seed}"
        result_dir.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            str(suite),
            "--model", str(model),
            "--server-bin", str(server),
            "--port", str(port),
            "--seed", str(seed),
            "--ctx-size", str(args.ctx_size),
            "--threads", str(args.threads),
            "--n-gpu-layers", str(args.n_gpu_layers),
            "--max-tokens", str(args.max_tokens),
            "--request-timeout", str(args.request_timeout),
            "--output", str(result_dir),
        ]
        if draft is not None:
            command += ["--model-draft", str(draft)]
        if args.spec_type:
            command += ["--spec-type", args.spec_type, "--spec-draft-n-max", str(args.spec_draft_n_max)]
        if args.flash_attn:
            command += ["--flash-attn", args.flash_attn]
        if prompt is not None:
            command += ["--system-prompt-file", str(prompt)]
        record: dict[str, Any] = {
            "label": "public-suite-run",
            "seed": seed,
            "port": port,
            "command": command,
            "result_dir": str(result_dir),
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        with runner_log.open("a", encoding="utf-8") as log:
            log.write(json.dumps({"event": "start", **record}, ensure_ascii=False) + "\n")
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        (result_dir / "runner_stdout.txt").write_text(completed.stdout or "", encoding="utf-8")
        (result_dir / "runner_stderr.txt").write_text(completed.stderr or "", encoding="utf-8")
        report_path = result_dir / "report.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
            record["summary"] = report.get("summary")
            record["load_time_seconds"] = report.get("load_time_seconds")
            record["status"] = "passed" if completed.returncode == 0 else "completed-with-failures"
        else:
            record["status"] = "no-report"
        record["returncode"] = completed.returncode
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        comparison["candidates"].append(record)
        comparison_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"seed": seed, "status": record["status"], "summary": record.get("summary")}, ensure_ascii=False), flush=True)
    comparison["finished_at"] = datetime.now(timezone.utc).isoformat()
    comparison_path.write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"comparison": str(comparison_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
