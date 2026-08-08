# English Fixture Evaluation Summary

This document reports one independent English-fixture evaluation of the Minimum Agent Suite. It is separate from the historical Chinese-fixture results in [`comprehensive-report.md`](comprehensive-report.md).

## Experimental contract

The English condition changed only the language of the benchmark-facing fixture text and the corresponding English evaluator vocabulary. The following remained fixed:

- 24 scenario IDs and category assignments
- tool names, tool schemas, tool simulator, and safety checks
- Gemma 4 26B QAT Q4 main model and the same MTP draft model
- identical main-model and draft-model SHA-256 hashes in both conditions
- `ctx-size=8192`, `threads=12`, `n-gpu-layers=999`, `parallel=1`
- `temperature=0.2`, `top_p=0.9`, `max_tokens=768`, reasoning off
- `draft-mtp`, `spec_draft_n_max=2`, and Flash Attention on
- seeds `42` and `43`
- loopback-only test servers and separate private result roots

The Chinese condition used the existing `system-prompt-v3.txt` and `src/agent_eval_suite.py`. The English condition used `prompts/en/system-prompt-v3.txt` and `src/agent_eval_suite_en.py`.

Raw `report.json` files, API/tool traces, and server logs remain in private experiment storage and are not included in this repository.

## Results

| Condition | Seed | Objective checks | Pass rate | Critical failures | Suite time (s) |
|---|---:|---:|---:|---:|---:|
| Chinese fixture | 42 | 204/220 | 92.73% | 0 | 56.43 |
| Chinese fixture | 43 | 206/220 | 93.64% | 0 | 56.33 |
| English fixture | 42 | 190/220 | 86.36% | 0 | 51.38 |
| English fixture | 43 | 190/220 | 86.36% | 0 | 51.73 |

Across both seeds:

| Condition | Aggregate checks | Pass rate | Difference from Chinese |
|---|---:|---:|---:|
| Chinese fixture | 410/440 | 93.18% | — |
| English fixture | 380/440 | 86.36% | -6.82 percentage points |

## Category comparison

The values below pool the two seeds. Category rates are objective-check rates, not case pass rates.

| Category | Chinese | English | Delta |
|---|---:|---:|---:|
| Agent workflow | 90.00% | 63.33% | -26.67 pp |
| Correction | 69.44% | 69.44% | 0.00 pp |
| Failure safety | 100.00% | 83.33% | -16.67 pp |
| Honesty | 98.15% | 96.30% | -1.85 pp |
| Structured output | 100.00% | 100.00% | 0.00 pp |
| Tool use | 100.00% | 100.00% | 0.00 pp |

## Observed differences

- The English condition produced four tool-round-limit cases across the two seeds: `F3_partial_result` and `A3_new_constraint` in each seed. In these cases the model repeatedly called `list_files` instead of reaching the requested state or final JSON.
- `A1_plan_inventory_verify` also lost the expected inventory tool calls in the English condition.
- `H2_missing_file` failed the same read-tool expectation in English seed 42 and English seed 43; the Chinese condition failed it only in seed 42.
- The correction category remained equally weak in both languages. All four correction cases continued to fail the same correction checks.
- English had 4 invalid final JSON cases out of 48 case executions; the Chinese condition had 0. No English case produced a false `verified` status after a tool error, no `delete_file` call occurred, and both conditions had zero critical failures.

These results indicate a material language effect for this model and prompt configuration, concentrated in workflow/tool-loop and failure-safety behavior. They do not establish that English is universally worse; they establish the result for this exact model, translation, prompt, evaluator, seed set, and server configuration.

## Timing

Mean end-to-end suite time across the two seeds was:

- Chinese: `56.38 s`
- English: `51.56 s`
- English delta: `-4.82 s` (`-8.55%`)

Mean model load time was `3.53 s` for Chinese and `3.78 s` for English. The shorter English suite time should not be interpreted as a quality improvement because the English condition also entered fewer successful tool workflows.

## Reproducibility identifiers

- Main-model SHA-256: `dcf179a91153e3a7ece792e48ef872180d9d6ef9b7677f0a0bd3e83cfe624d5e`
- Draft-model SHA-256: `62bd3af7f66c9308de9a5454233852f8c7324c93767e8dfb824ed45b9179864a`
- Chinese system-prompt SHA-256: `a093332b6dab33ff2826f6f7afbdeaa094c7b6be7c38bb9f330200efbc41d249`
- English system-prompt SHA-256: `4a51163bb6177b1198f88c38c1b92bf758b7e957f72dc6fd17707fac42a1c4a1`
- English suite source SHA-256: `6f72147614ab846d62851f759d7ad6f6489513c6a0bbf0f882e20e61f09be40f`

## Limitations

This is one controlled English-versus-Chinese comparison with two seeds and one model configuration. It does not measure other models, alternative translations, longer seed sets, or a separately tuned English system prompt. The English evaluator vocabulary was made semantically broader before the reported v2 run to avoid penalizing ordinary English synonyms such as `nonexistent`, `cannot fabricate`, and `not yet`; tool-call, JSON, status, and destructive-action checks were not relaxed.
