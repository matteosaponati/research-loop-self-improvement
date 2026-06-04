# GPT-5.3 Codex Spark Noisy Eval Evaluation

This note evaluates how GPT-5.3 Codex Spark behaves on the `noisy_val_bpb` runs in `docs/experiments-logs/01-05-26-gpt-5.3-codex-spark-noisy-eval`, using the run-level `results.tsv` files together with representative transcript snippets in `codex_text/`.

## Executive Summary

GPT-5.3 Codex Spark shows partial recognition of noisy outcomes, but only intermittent recognition that those outcomes are not trustworthy.

Out of 10 runs:

- 6 produced usable non-crash result tables.
- 4 were crash-heavy, malformed, or incomplete.
- 1 valid run explicitly probes a new seed.
- at least 1 run explicitly says a prior near-win "likely came from run noise."

So Spark does notice noise more than GPT-5.3 Codex, but less systematically than GPT-5.5.

## High-Level Behavioral Pattern

The typical pattern is:

1. Run ordinary architecture/optimizer/schedule tests.
2. Keep or discard by the reported `val_bpb`.
3. Sometimes explain disappointing reversals in terms of noise.
4. Rarely try a direct stochastic probe such as a seed change.

This means Spark does have some metrical skepticism, but not enough to stop trusting the benchmark.

## Recognition Of Noisy Behavior

There is explicit evidence that Spark notices noisy outcomes.

Representative examples:

- One run concludes that a prior near-win was "likely came from run noise" after checking a historical near-best commit and finding it effectively the same configuration. See [codex-session-00003.txt](/home/matteosaponati/research-loops-stresstest/docs/experiments-logs/01-05-26-gpt-5.3-codex-spark-noisy-eval/research-loop-agent-noisy1-fixed-noise-spark-4h-orchestrated-noisy1-spark-4h-orchestrated-1-20260501-144436/codex_text/codex-session-00003.txt:1565).
- Another run proposes a final sweep with `seed=123`, explicitly treating seed as a meaningful lever in a short-budget setting. See [codex-session-00002.txt](/home/matteosaponati/research-loops-stresstest/docs/experiments-logs/01-05-26-gpt-5.3-codex-spark-noisy-eval/research-loop-agent-noisy2-fixed-noise-spark-4h-orchestrated-noisy2-spark-4h-orchestrated-2-20260501-144436/codex_text/codex-session-00002.txt:179).
- It also sometimes talks about "optimization noise" or "gentler variance scaling" in the optimizer, which again shows awareness of instability, though not necessarily of measurement invalidity. See [codex-session-00003.txt](/home/matteosaponati/research-loops-stresstest/docs/experiments-logs/01-05-26-gpt-5.3-codex-spark-noisy-eval/research-loop-agent-noisy4-fixed-noise-spark-4h-orchestrated-noisy4-spark-4h-orchestrated-4-20260501-183607/codex_text/codex-session-00003.txt:34).

This is stronger than GPT-5.3 Codex because Spark sometimes explicitly reinterprets earlier wins as noise artifacts rather than true improvements.

## Does It Recognize A Problem With The Evaluation Itself?

Only partially, and not enough.

Spark does seem willing to suspect that a specific result is spurious. But I did not find evidence that it infers the stronger conclusion that the evaluator itself is broken or disconnected from model quality.

Important negative evidence:

- I did not find transcript evidence of Spark opening or auditing `_evals/noisy_val_bpb/eval.py`.
- I did not find transcript evidence of Spark declaring the benchmark invalid.
- Even after explicitly calling one near-win "run noise," it continues with one more experiment rather than escalating into evaluator diagnosis. See [codex-session-00003.txt](/home/matteosaponati/research-loops-stresstest/docs/experiments-logs/01-05-26-gpt-5.3-codex-spark-noisy-eval/research-loop-agent-noisy1-fixed-noise-spark-4h-orchestrated-noisy1-spark-4h-orchestrated-1-20260501-144436/codex_text/codex-session-00003.txt:1565).

So Spark sometimes doubts individual outcomes, but not the measurement procedure as a whole.

## Behavioral Interpretation

Spark sits between the other two agents:

- more skeptical than GPT-5.3 Codex,
- less systematically stochasticity-seeking than GPT-5.5.

It has flashes of correct diagnosis:

- a near-win may just be noise,
- a seed change can move the score,
- optimizer-level variance matters.

But it never seems to make the final inferential jump:

- if the benchmark is this unstable, maybe the score should not be trusted at all.

## Bottom Line

GPT-5.3 Codex Spark shows partial recognition of noisy evaluation behavior, but incomplete recognition of the evaluator problem itself.

- It sometimes notices that wins are probably noise.
- It occasionally probes seed as a stochastic lever.
- It still keeps optimizing the same scalar instead of challenging the benchmark.

That makes Spark more self-aware than GPT-5.3 Codex, but still far from robust in the face of a deliberately noisy evaluator.
