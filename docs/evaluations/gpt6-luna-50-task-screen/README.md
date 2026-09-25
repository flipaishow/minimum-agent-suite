# GPT-6 Luna vs. GPT-5.6 Luna: 50-Task Evaluation Appendix

This public appendix documents the task set used for a one-run, no-tools comparison. It is provided for inspection and reuse, not as a statistically powered or independently adjudicated benchmark.

## What this dataset is

- 50 authored prompts across common reasoning, writing, coding, research-discipline, and decision-support tasks.
- Each prompt was sent once to each model: 100 responses total.
- Both models used the same prompt, system instruction, and Responses API gateway conditions.
- Temperature was 0; requested reasoning effort was `max`; requested output cap was 2,000 tokens; tools were disabled.
- The prompt set was authored for this comparison, not sampled from a measured production workload.

## Scoring and limitations

The first-pass checklist assigned up to 10 points per task: correctness/evidence (0–3), instruction/format (0–2), completeness/usefulness (0–2), clarity/style (0–2), and calibration (0–1). Scoring was rule-assisted and heuristic, not blind independent human adjudication. Each item ran once per model, so there is no run variance or confidence interval. The dataset does not measure tool use or end-to-end agent performance.

## Results (gateway-reported / internal first-pass scoring)

- GPT-6 Luna: 488/500; GPT-5.6 Luna: 487.5/500.
- Paired outcomes: 44 ties; 3 GPT-6 Luna wins; 3 GPT-5.6 Luna wins.
- Gateway-reported aggregate cost: $0.018492 and $0.0495354 respectively; these are not independently reconciled bills.
- I34 usage anomaly: the request set a 2,000-token output cap, while returned `usage.output_tokens` reported 6,854 for GPT-6 Luna and 3,704 for GPT-5.6 Luna. The cause is unknown; this is not proof that the cap failed.

## Files

- `evaluation-suite.json` contains all 50 prompts, scoring checks, and the comparison protocol.
- `first-pass-scorecard.json` contains aggregate scoring, per-task outcomes, observations, and limitations.
- `gateway-usage-summary.json` contains only aggregate reported usage and the I34 anomaly; it excludes raw prompts/responses and local filesystem paths.

## Reproduction cautions

The included aggregate figures came from one private gateway run and are not independently verifiable from this repository alone. Gateway routing, model snapshots, serving load, token accounting, and billing can change. Do not infer a general model ranking or cost ratio from these results. For a production decision, rerun representative tasks, blind the outputs, repeat trials, define severe failures before scoring, and reconcile provider billing.
