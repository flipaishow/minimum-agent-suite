# Minimum Agent Suite Comprehensive Evaluation Report

> Report generated: `2026-08-08T08:02:22.878934+00:00` (source-run metadata; host details omitted)
>
> Public-release note: model weights, raw comparison/report JSON, server logs, complete API/tool traces, private remote paths, and the retention manifest are not included in this release. This document retains only publishable aggregate results and methodology.
> This report summarizes completed model comparisons, Gemma 4 QAT Q4 + MTP validation, system-prompt A/B and ablation experiments, and the `spec_draft_n_max` sweep. Scores are taken directly from the preserved private `comparison.json` and `report.json` artifacts.

## 1. Executive summary

The currently recommended Agent deployment configuration is:

```text
Gemma 4 26B A4B QAT Q4_K_XL + MTP
system_prompt_v3
spec_draft_n_max=2
```

- v3 + nmax=2: `410/440` (93.2%), critical `0`, JSON `100.0%`, failure safety `100.0%`.
- v3 + nmax=4: `411/440` (93.4%), the highest aggregate score in this round, but with a JSON category score of `92.9%`.
- With only the original baseline system prompt, Agent capability was nearly identical at nmax=2/3/4; nmax=2 had the shortest end-to-end suite time.
- None of the QAT Q4 MTP or prompt experiments included in this report introduced a new critical failure.

## 2. Scope and methodology

- Minimum Agent Suite: 24 scenarios covering H1–H6, C1–C4, T1–T6, F1–F4, A1–A3, and S1.
- Each model/configuration used seeds `42` and `43`; each seed contained 220 objective checks, for 440 checks across both seeds.
- Tool-oriented cases preserved complete API traces, tool traces, final outputs, scoring checks, and server logs in private storage.
- A critical failure includes reporting `status: "verified"` after a tool failure, incomplete result, or conflict, as well as safety-protocol violations such as calling `delete_file` without confirmation.
- The MTP sweep held the main model, draft model, temperature, top-p, maximum tokens, tools, GPU offload, Flash Attention, and scenarios constant; only `spec_draft_n_max` changed.
- The system-prompt ablation held the model, MTP configuration, seeds, suite, tools, and inference parameters constant while adding one rule set at a time.

## 3. Initial model comparison

The following completed comparisons used the baseline system prompt rather than a system-prompt intervention. Each seed column uses the format `passed/total`.

| Model | Seed scores | Aggregate | Critical | Mean load (s) | Category averages (integrity / correction / failure safety / tool / agent / JSON) |
|---|---|---:|---:|---:|---|
| `gemma4-26b-q4` | 42: 196/220, 43: 198/220 | 394/440 (89.5%) | 0 | 12.89 | Integrity 98.1% / Correction 66.7% / Failure safety 86.1% / Tool 100.0% / Agent 83.3% / JSON 100.0% |
| `qwen36-35b-heretic-q6` | 42: 184/220, 43: 189/220 | 373/440 (84.8%) | 4 | 89.09 | Integrity 88.0% / Correction 69.4% / Failure safety 83.3% / Tool 90.4% / Agent 85.0% / JSON 100.0% |
| `gemma4-12b-q4` | 42: 186/220, 43: 184/220 | 370/440 (84.1%) | 2 | 5.30 | Integrity 83.3% / Correction 69.4% / Failure safety 83.3% / Tool 100.0% / Agent 70.0% / JSON 100.0% |
| `qwythos9b-q5` | 42: 182/220, 43: 185/220 | 367/440 (83.4%) | 3 | 4.12 | Integrity 87.0% / Correction 69.4% / Failure safety 88.9% / Tool 79.8% / Agent 90.0% / JSON 100.0% |
| `qwen36-35b-mxfp4` | 42: 180/220, 43: 179/220 | 359/440 (81.6%) | 4 | 9.12 | Integrity 85.2% / Correction 69.4% / Failure safety 80.6% / Tool 79.8% / Agent 90.0% / JSON 100.0% |
| `gemma4-26b-mxfp4` | 42: 180/220, 43: 179/220 | 359/440 (81.6%) | 3 | 10.37 | Integrity 88.0% / Correction 55.6% / Failure safety 84.7% / Tool 100.0% / Agent 58.3% / JSON 100.0% |
| `qwen36-35b-uncensored-q8` | 42: 171/220, 43: 184/220 | 355/440 (80.7%) | 3 | 73.43 | Integrity 88.9% / Correction 69.4% / Failure safety 76.4% / Tool 77.2% / Agent 86.7% / JSON 100.0% |
| `qwen-agentworld-35b-mxfp4` | 42: 169/220, 43: 175/220 | 344/440 (78.2%) | 0 | 13.79 | Integrity 79.6% / Correction 69.4% / Failure safety 76.4% / Tool 77.2% / Agent 85.0% / JSON 100.0% |
| `gemma4-26b-ud-q5km` | 42: 172/220, 43: 171/220 | 343/440 (78.0%) | 0 | 6.04 | Integrity 85.2% / Correction 51.4% / Failure safety 86.1% / Tool 89.5% / Agent 60.0% / JSON 100.0% |
| `gemma4-26b-ud-q4km` | 42: 164/220, 43: 159/220 | 323/440 (73.4%) | 4 | 4.78 | Integrity 72.2% / Correction 55.6% / Failure safety 79.2% / Tool 86.0% / Agent 60.0% / JSON 100.0% |
| `ornith35b-mxfp4` | 42: 151/220, 43: 156/220 | 307/440 (69.8%) | 2 | 14.23 | Integrity 73.1% / Correction 69.4% / Failure safety 72.2% / Tool 72.8% / Agent 56.7% / JSON 64.3% |
| `ornith35b-q6` | 42: 136/220, 43: 128/220 | 264/440 (60.0%) | 2 | 31.60 | Integrity 64.8% / Correction 69.4% / Failure safety 45.8% / Tool 66.7% / Agent 51.7% / JSON 28.6% |
| `qwen35-4b-iq4-xs` | 42: 129/220, 43: 129/220 | 258/440 (58.6%) | 0 | 3.55 | Integrity 67.6% / Correction 69.4% / Failure safety 44.4% / Tool 53.5% / Agent 46.7% / JSON 100.0% |

Key findings:

- The original Gemma 4 26B QAT Q4 was the strongest initial Agent baseline, with an objective pass rate of about 89.5% and zero critical failures.
- Gemma 4 26B MXFP4_MOE scored about 81.6% and had three critical failures.
- UD-Q4_K_M scored about 73.4% and had four critical failures; it is not suitable as the primary Agent configuration.
- UD-Q5_K_M scored about 78.0% with zero critical failures, making it safer than UD-Q4_K_M, but it remained below the original QAT Q4 in capability.

## 4. Gemma 4 QAT Q4 + MTP validation

### 4.1 Model and command

- Target: `[PRIVATE_PATH_OMITTED]`
- Target size: `14,249,045,120` bytes
- Target SHA256: `dcf179a91153e3a7ece792e48ef872180d9d6ef9b7677f0a0bd3e83cfe624d5e`
- MTP draft: `[PRIVATE_PATH_OMITTED]`
- Draft size: `251,937,728` bytes
- Draft SHA256: `62bd3af7f66c9308de9a5454233852f8c7324c93767e8dfb824ed45b9179864a`

Equivalent launch parameters:

```bash
llama-server \
  --model [PRIVATE_PATH_OMITTED] \
  --model-draft [PRIVATE_PATH_OMITTED] \
  --spec-type draft-mtp \
  --spec-draft-n-max 4 \
  --flash-attn on \
  --host 127.0.0.1 \
  --port 18810
```

The smoke test confirmed health, chat completion, and MTP draft acceptance. The response observed `draft_n=4` and `draft_n_accepted=4`. A `failed to measure draft model memory` warning appeared during startup, but the server continued serving requests and the log continued to record draft acceptance.

- Upstream model repository: `https://huggingface.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF`.

### 4.2 MTP baseline versus no MTP

| Experiment | Seed 42 | Seed 43 | Aggregate | Critical | Mean suite (s) | Mean load (s) | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QAT Q4 + MTP, nmax=4 | 202/220 | 192/220 | 394/440 (89.5%) | 0 | 58.76 | 3.52 | 54.0% | 326.5 |

- QAT Q4 + MTP aggregate: 89.5%, with zero critical failures.
- This matched the same QAT Q4 configuration without MTP at 89.5% aggregate and zero critical failures.
- Without MTP: seed 42 scored 89.1% with a 190.5-second suite and 96.0 tok/s evaluation throughput; seed 43 scored 90.0% with a 223.3-second suite and 85.4 tok/s.
- The MTP baseline completed in approximately 58–59 seconds; the same QAT Q4 configuration without MTP took approximately 190–223 seconds.
- The MTP speed figures come from server-log evaluation throughput and total suite elapsed time, not from model file size.

## 5. System-prompt experiments

### 5.1 Long v2 and concise v3

| Experiment | Seed 42 | Seed 43 | Aggregate | Critical | Mean suite (s) | Mean load (s) | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline system prompt | 202/220 | 192/220 | 394/440 (89.5%) | 0 | 58.76 | 3.52 | 54.0% | 326.5 |
| system_prompt_v2 (long) | 153/220 | 171/220 | 324/440 (73.6%) | 0 | 62.59 | 3.35 | 52.6% | 281.4 |
| system_prompt_v3 (concise) | 205/220 | 206/220 | 411/440 (93.4%) | 0 | 56.68 | 3.53 | 54.6% | 342.9 |
| system_prompt_v3 + nmax=2 | 204/220 | 206/220 | 410/440 (93.2%) | 0 | 56.38 | 3.53 | 70.5% | 346.3 |

Category results:

| Variant | Integrity | Correction | Failure safety | Tool | Agent | JSON |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 98.1% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |
| v2 | 66.7% | 69.4% | 93.1% | 71.9% | 81.7% | 28.6% |
| v3 | 100.0% | 69.4% | 100.0% | 100.0% | 90.0% | 92.9% |
| v3+nmax2 | 98.1% | 69.4% | 100.0% | 100.0% | 90.0% | 100.0% |

Observations:

- Long v2 scored 73.6% and produced many Markdown code fences and JSON-check failures; it was not an effective intervention.
- Concise v3 scored 93.4%, reached 100% in integrity and failure safety, and reached 90% in Agent workflow, but lost one structured-output check.
- v3+nmax2 scored 93.2%, returned to 100% JSON and 100% failure safety, and had zero critical failures; it is the more stable deployment trade-off.

### 5.2 Single-rule ablation

| Experiment | Seed 42 | Seed 43 | Aggregate | Critical | Mean suite (s) | Mean load (s) | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| JSON-only | 205/220 | 205/220 | 410/440 (93.2%) | 0 | 57.10 | 3.52 | 53.3% | 337.6 |
| status-only | 197/220 | 197/220 | 394/440 (89.5%) | 0 | 57.63 | 3.53 | 53.7% | 337.4 |
| confirmation-only | 196/220 | 201/220 | 397/440 (90.2%) | 0 | 56.60 | 3.78 | 51.6% | 342.7 |
| correction-only | 191/220 | 190/220 | 381/440 (86.6%) | 0 | 61.30 | 3.77 | 54.2% | 324.3 |

| Variant | Aggregate | Relative to baseline | Integrity | Correction | Failure safety | Agent | JSON |
|---|---:|---:|---:|---:|---:|---:|---:|
| JSON-only | 93.2% | +3.6 pp | 98.1% | 69.4% | 100.0% | 90.0% | 100.0% |
| status-only | 89.5% | +0.0 pp | 100.0% | 63.9% | 86.1% | 83.3% | 100.0% |
| confirmation-only | 90.2% | +0.7 pp | 97.2% | 66.7% | 86.1% | 90.0% | 100.0% |
| correction-only | 86.6% | -3.0 pp | 92.6% | 63.9% | 86.1% | 75.0% | 100.0% |

Ablation conclusions:

- JSON-only was the most stable single increment: 93.2%, JSON 100%, failure safety 100%, and zero critical failures.
- status-only improved honesty, but did not improve aggregate performance and correction regressed.
- confirmation-only provided only a small aggregate improvement and cannot replace an external delete gate.
- correction-only fell to 86.6%, indicating that the current correction problem cannot be solved by adding text rules alone.
- Length is not the only causal factor; rule duplication, output constraints, and competition for model attention also matter.

### 5.3 System-prompt limitations

This A/B experiment used the suite baseline system prompt and tool schemas. It did not reproduce the complete Hermes production context with Soul.md, every tool description, and every skill. The results therefore support a design direction of concise, on-demand context with limited duplication, but they must not be presented as scores for the complete Hermes prompt.

## 6. `spec_draft_n_max` sweep

### 6.1 Original baseline system prompt

| Experiment | Seed 42 | Seed 43 | Aggregate | Critical | Mean suite (s) | Mean load (s) | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| nmax=1 | 196/220 | 197/220 | 393/440 (89.3%) | 0 | 59.01 | 3.17 | 79.9% | 319.9 |
| nmax=2 | 202/220 | 191/220 | 393/440 (89.3%) | 0 | 55.77 | 3.17 | 69.6% | 342.6 |
| nmax=3 | 196/220 | 198/220 | 394/440 (89.5%) | 0 | 56.22 | 3.60 | 62.6% | 343.7 |
| nmax=4 | 202/220 | 192/220 | 394/440 (89.5%) | 0 | 58.76 | 3.52 | 54.0% | 326.5 |

Category summary for the nmax sweep:

| nmax | Integrity | Correction | Failure safety | Tool | Agent | JSON |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 97.2% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |
| 2 | 97.2% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |
| 3 | 98.1% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |
| 4 | 98.1% | 66.7% | 86.1% | 100.0% | 83.3% | 100.0% |

Observations:

- nmax=1 had the highest draft-acceptance ratio but the slowest complete suite, so it is not the preferred primary setting.
- nmax=2 had the shortest mean suite time. Its Agent aggregate was one objective check below nmax=4, with zero critical failures in both.
- nmax=3 had slightly higher raw evaluation throughput but no end-to-end suite advantage.
- nmax=4 is the model-card example value, but it was not faster or safer than nmax=2 for this multi-tool, short-turn Agent workload.
- Draft acceptance decreases as nmax grows. Acceptance ratio alone is not sufficient for configuration selection; evaluate end-to-end latency and Agent score.

### 6.2 v3 prompt interaction check

| Experiment | Seed 42 | Seed 43 | Aggregate | Critical | Mean suite (s) | Mean load (s) | Draft acceptance | Eval tok/s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v3 + nmax=2 | 204/220 | 206/220 | 410/440 (93.2%) | 0 | 56.38 | 3.53 | 70.5% | 346.3 |
| v3 + nmax=4 | 205/220 | 206/220 | 411/440 (93.4%) | 0 | 56.68 | 3.53 | 54.6% | 342.9 |

The v3 interaction results support nmax=2 for the current Agent workload: JSON 100%, failure safety 100%, zero critical failures, nearly the same total suite time as nmax=4, and slightly higher server evaluation throughput.

## 7. Final recommendation

### 7.1 Agent deployment

```bash
--spec-type draft-mtp
--spec-draft-n-max 2
--flash-attn on
```

Combined with `system_prompt_v3`, the measured result was 93.2%, zero critical failures, JSON 100%, and failure safety 100%.

### 7.2 Model selection

- Primary Agent: Gemma 4 26B QAT Q4_K_XL + MTP.
- Memory/speed alternative: UD-Q5_K_M, with lower capability than QAT Q4.
- Do not use UD-Q4_K_M as the primary safety-oriented Agent; it had four critical failures.
- MXFP4_MOE loaded faster but had three critical failures; speed alone is insufficient.

### 7.3 Safety boundaries

- An external tool gateway must directly block `delete_file` without confirmation.
- When a tool returns failure, partial, `not_found`, or conflicting evidence, an evaluator or middleware layer must prevent `status: "verified"`.
- A system prompt can improve compliance, but it cannot replace an external validator.

## 8. Integrity, isolation, and limitations

- The QAT target SHA256 was consistent across the MTP, nmax, and prompt experiments: `dcf179a91153e3a7ece792e48ef872180d9d6ef9b7677f0a0bd3e83cfe624d5e`.
- The MTP draft SHA256 was consistent: `62bd3af7f66c9308de9a5454233852f8c7324c93767e8dfb824ed45b9179864a`.
- Every included scored run completed all 24 scenarios with both seeds and preserved API/tool traces in private storage.
- All temporary test endpoints were released after the prompt and nmax experiments.
- Production services were not restarted, switched, or modified during testing.
- No llama-server process remained on the temporary test endpoints.
- No API key, token, password, SSH private key, or connection credential was stored in the results or this report.

Limitations:

- Each configuration used only seeds 42 and 43; this supports engineering decisions but not a complete statistical-significance claim.
- `spec_draft_n_max>4` was not validated and must not be applied without testing.
- MTP throughput came from llama.cpp server-log evaluation time; it is not a complete network end-to-end tok/s benchmark.
- The system-prompt A/B test did not reproduce the full Hermes Soul/skill context.
- Formal service switching, model cleanup, and production changes were outside the scope of this report.

## 9. Artifact index

- `prompts/system-prompt-v2.txt`
- `prompts/system-prompt-v3.txt`
- `prompts/system-prompt-ab-json.txt`
- `prompts/system-prompt-ab-status.txt`
- `prompts/system-prompt-ab-confirmation.txt`
- `prompts/system-prompt-ab-correction.txt`

---

End of report.
