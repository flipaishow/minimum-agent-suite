# Language-Factor Analysis

This document reports a controlled 2x2 follow-up to the independent English-fixture evaluation. It separates the language of the system prompt from the language of the benchmark-facing fixture text.

## Experimental contract

All four conditions used the same:

- 24 scenario IDs and category assignments
- model and MTP draft model, with identical SHA-256 hashes
- `temperature=0.2`, `top_p=0.9`, `max_tokens=768`
- `spec_type=draft-mtp`, `spec_draft_n_max=2`, Flash Attention on, reasoning off
- seeds `42` and `43`
- tool names, schemas, simulator, safety boundaries, context, server settings, and request timeout
- loopback-only child servers and separate private result roots

The four conditions were:

| Condition | System prompt | Scenario/tool fixture text |
|---|---|---|
| A | Chinese | Chinese |
| B | English | Chinese |
| C | Chinese | English |
| D | English | English |

A and B used the original Chinese runner/scorer. C and D used the independent English runner/scorer with the corrected English vocabulary parity. The original Chinese results and the English results were not overwritten.

### Artifact identity

- main model SHA-256: `dcf179a91153e3a7ece792e48ef872180d9d6ef9b7677f0a0bd3e83cfe624d5e`
- draft model SHA-256: `62bd3af7f66c9308de9a5454233852f8c7324c93767e8dfb824ed45b9179864a`
- Chinese system prompt SHA-256: `a093332b6dab33ff2826f6f7afbdeaa094c7b6be7c38bb9f330200efbc41d249`
- English system prompt SHA-256: `4a51163bb6177b1198f88c38c1b92bf758b7e957f72dc6fd17707fac42a1c4a1`

Raw reports, traces, and server logs remain in private experiment storage.

## Results

Each seed contains 220 objective checks.

| Condition | Seed 42 | Seed 43 | Aggregate | Critical failures |
|---|---:|---:|---:|---:|
| A: Chinese system + Chinese fixtures | 204/220 (92.73%) | 206/220 (93.64%) | **410/440 (93.18%)** | 0 |
| B: English system + Chinese fixtures | 194/220 (88.18%) | 193/220 (87.73%) | **387/440 (87.95%)** | 0 |
| C: Chinese system + English fixtures | 190/220 (86.36%) | 192/220 (87.27%) | **382/440 (86.82%)** | 0 |
| D: English system + English fixtures | 190/220 (86.36%) | 190/220 (86.36%) | **380/440 (86.36%)** | 0 |

### Category rates pooled across both seeds

| Category | A | B | C | D |
|---|---:|---:|---:|---:|
| Agent workflow | 90.00% | 60.00% | 83.33% | 63.33% |
| Correction | 69.44% | 69.44% | 69.44% | 69.44% |
| Failure safety | 100.00% | 100.00% | 86.11% | 83.33% |
| Honesty | 98.15% | 94.44% | 96.30% | 96.30% |
| Structured output | 100.00% | 92.86% | 85.71% | 100.00% |
| Tool use | 100.00% | 100.00% | 91.23% | 100.00% |

### Integrity and tool-loop indicators

| Condition | Invalid JSON cases / 48 | Tool-round-limit cases | False `verified` after error | `delete_file` calls |
|---|---:|---:|---:|---:|
| A | 0 | 0 | 0 | 0 |
| B | 2 | 0 | 0 | 0 |
| C | 4 | 4 | 0 | 0 |
| D | 4 | 4 | 0 | 0 |

All four conditions had zero critical failures.

## Factor effects

The cleanest comparisons hold the fixture language constant:

- **Chinese fixtures, A → B:** changing only the system prompt from Chinese to English lost `23/440` checks, or **-5.23 percentage points**.
- **English fixtures, C → D:** changing only the system prompt from Chinese to English lost `2/440` checks, or **-0.45 percentage points**.

Holding the system prompt constant gives the following directional comparisons:

- **Chinese system, A → C:** English fixture text lost `28/440` checks, or **-6.36 percentage points**.
- **English system, B → D:** English fixture text lost `7/440` checks, or **-1.59 percentage points**.

The 2x2 interaction term is `+21` checks (`+4.77 pp`): the English system prompt is much more damaging on Chinese fixtures than on English fixtures. On English fixtures it partially restores structured-output and general tool-use checks, while agent-workflow behavior remains weak.

## What changed in the traces

- **B:** English system prompt caused repeated workflow failures in `A1_plan_inventory_verify`, `A2_resume_state`, and `A3_new_constraint`. It also produced two invalid-JSON cases and one seed-level `S1_strict_json` failure. There were no tool-round-limit errors.
- **C:** Chinese system prompt with English fixtures produced tool-round limits in both `T4_read_before_write` and `F3_partial_result` for both seeds. These are real trace-level failures, not only scorer vocabulary mismatches.
- **D:** English system plus English fixtures kept the `F3_partial_result` loop and added `A3_new_constraint` loop behavior, but recovered the structured-output and general tool-use category rates relative to C.
- `C1`–`C4` correction remained equally weak in all four conditions. This is not evidence that Chinese improved correction behavior.

## Interpretation

The data does **not** support the universal claim that Chinese is inherently easier for an LLM. It supports a narrower conclusion:

> For this model, this protocol prompt, this tool schema, this fixture translation, and these two seeds, the all-Chinese condition was the most stable overall. Language effects were concentrated in workflow and failure/tool-loop behavior, and the system-prompt language interacted strongly with fixture language.

The likely mechanism is a combination of tokenization, learned instruction-following patterns, speech-act wording, and the model's alignment to tool-use protocols in each language. Semantic translation does not guarantee equivalent next-token behavior.

For a Chinese-oriented workload, condition A is currently the strongest measured configuration. For an English-oriented workload, neither C nor D is equivalent to A: D has better structured/tool checks than C, while C has better agent-workflow checks than D. English should therefore be tuned and re-evaluated as its own production condition rather than treated as a drop-in translation.

## Limitations

1. Only two seeds and one model were tested; this is a measured effect, not a universal language ranking.
2. A/B use the Chinese scorer vocabulary and C/D use the corrected English scorer vocabulary. Comparisons within each fixture-language row keep the scorer constant; cross-row score deltas should be interpreted together with raw tool traces.
3. The system prompts are semantically matched translations, not token-identical interventions. Wording and tokenization remain part of the language condition.
4. More seeds and a bilingual shared scorer would be needed for a stronger statistical and scorer-independent decomposition.
