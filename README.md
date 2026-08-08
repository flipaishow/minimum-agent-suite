# Minimum Agent Suite

A reproducible local-LLM evaluation suite focused on agent behavior, tool use, failure safety, correction, and strict JSON output.

> This is a sanitized public release. Model weights, raw server logs, full API/tool traces, private environment paths, and credentials are intentionally excluded from the repository.

## Contents

- `src/agent_eval_suite.py`: 24 Chinese-fixture scenarios and objective evaluators
- `src/agent_eval_suite_en.py`: independent English-fixture suite variant
- `src/model_eval_pilot.py`: shared loopback-server, HTTP, and GPU-metrics helpers
- `src/run_suite.py`: multi-seed runner; each run uses loopback only
- `prompts/`: baseline system prompt and single-factor ablation candidates
- `prompts/en/system-prompt-v3.txt`: English system-prompt condition
- `docs/comprehensive-report.md`: sanitized aggregate evaluation report
- `docs/english-evaluation-summary.md`: English-versus-Chinese fixture comparison

## Benchmark fixtures and language

The explanatory documentation in this repository is written in English. The original Chinese benchmark fixture and its historical results remain unchanged for reproducibility. An independent English-fixture variant is provided in `src/agent_eval_suite_en.py` and `prompts/en/`; it has its own measured results in [`docs/english-evaluation-summary.md`](docs/english-evaluation-summary.md). Do not mix the Chinese and English scores as if they were the same condition.

## Evaluation scope

The suite contains 24 fixed scenarios:

- H1–H6: integrity and evidence
- C1–C4: correction
- T1–T6: tool use
- F1–F4: failure safety
- A1–A3: agent workflow
- S1: strict JSON output

Each configuration uses seeds `42` and `43` by default. Each seed contains 220 objective checks.

## Requirements

- Python 3.10+
- An executable [`llama.cpp`](https://github.com/ggml-org/llama.cpp) `llama-server`
- A GGUF main model supplied by the user; MTP also requires a draft GGUF
- GPU/CPU, Flash Attention, and model-specific dependencies managed by the user

This repository does not download, store, or redistribute model weights.

## Quick start

### Without MTP

```bash
python src/run_suite.py \
  --model /path/to/model.gguf \
  --server-bin /path/to/llama-server \
  --system-prompt-file prompts/system-prompt-v3.txt \
  --output-root results/local-baseline
```

### With Gemma MTP

```bash
python src/run_suite.py \
  --model /path/to/main-model.gguf \
  --model-draft /path/to/mtp-draft.gguf \
  --server-bin /path/to/llama-server \
  --spec-type draft-mtp \
  --spec-draft-n-max 2 \
  --flash-attn on \
  --system-prompt-file prompts/system-prompt-v3.txt \
  --output-root results/local-gemma-mtp
```

Windows Git Bash example:

```bash
python src/run_suite.py \
  --model 'C:/models/main-model.gguf' \
  --model-draft 'C:/models/mtp-draft.gguf' \
  --server-bin 'C:/llama.cpp/build/bin/llama-server.exe' \
  --spec-type draft-mtp \
  --spec-draft-n-max 2 \
  --flash-attn on \
  --system-prompt-file prompts/system-prompt-v3.txt \
  --output-root results/windows-run
```

`run_suite.py` uses a different loopback port for each seed and writes JSON output under `results/`. That directory is ignored by `.gitignore` to prevent accidental publication of raw traces.

## Published aggregate summary

See [`docs/comprehensive-report.md`](docs/comprehensive-report.md) for the full sanitized report and limitations. Representative results:

| Configuration | Aggregate | Critical | JSON | Failure safety |
|---|---:|---:|---:|---:|
| QAT Q4 + MTP baseline, nmax=4 | 89.5% | 0 | 100% | 86.1% |
| system prompt v3 + nmax=4 | 93.4% | 0 | 92.9% | 100% |
| system prompt v3 + nmax=2 | 93.2% | 0 | 100% | 100% |
| English fixture, system prompt v3 + nmax=2 | 86.36% | 0 | 91.7% | 83.3% |

The English row is a separate two-seed measurement; see the detailed comparison document for its scope and limitations. For the original evaluated tool-oriented workload, the recommended setting is `system_prompt_v3 + spec_draft_n_max=2`. This is not a universal guarantee for every model or long-context workload; rerun the suite with your own model, llama.cpp version, and hardware.

## Safety boundaries

- The test server binds to `127.0.0.1` only; do not point it at a production bind address.
- `delete_file` in the suite is a sandbox evaluator simulation and does not delete user files.
- Real tool gateways must independently block destructive actions until confirmation; prompts are not an authorization boundary.
- A tool failure, partial result, `not_found`, or conflicting evidence must not be reported as `status: "verified"`.
- Do not commit API keys, tokens, passwords, SSH private keys, `.env` files, raw logs, or model files.

## Reproducibility and result handling

For each private run, preserve:

- the command and llama.cpp version
- seed, model/draft hashes, and system-prompt hash
- load time, suite elapsed time, and evaluation throughput
- complete JSON, tool traces, and server logs

The public report contains aggregate results only. Keep raw JSON and logs in private storage.

## License

This project is released under the [MIT License](LICENSE).
