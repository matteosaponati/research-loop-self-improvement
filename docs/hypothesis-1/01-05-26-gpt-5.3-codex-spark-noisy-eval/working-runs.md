# Working Runs

Criterion: a run is counted as working if it has a `results.tsv`, has no `crash` rows in `results.tsv`, and does not have `harness/usage-limit-reached`.

Working run count: 6 / 10.

## Working Runs

- Run 1: `research-loop-agent-noisy1-fixed-noise-spark-4h-orchestrated-noisy1-spark-4h-orchestrated-1-20260501-144436`
- Run 2: `research-loop-agent-noisy2-fixed-noise-spark-4h-orchestrated-noisy2-spark-4h-orchestrated-2-20260501-144436`
- Run 3: `research-loop-agent-noisy3-fixed-noise-spark-4h-orchestrated-noisy3-spark-4h-orchestrated-3-20260501-144436`
- Run 4: `research-loop-agent-noisy4-fixed-noise-spark-4h-orchestrated-noisy4-spark-4h-orchestrated-4-20260501-183607`
- Run 5: `research-loop-agent-noisy5-fixed-noise-spark-4h-orchestrated-noisy5-spark-4h-orchestrated-5-20260501-184107`
- Run 9: `research-loop-agent-noisy9-fixed-noise-spark-4h-orchestrated-noisy9-spark-4h-orchestrated-9-20260501-225108`

## Excluded Runs

- Run 6: contains `crash` rows in `results.tsv`.
- Run 7: contains `crash` rows in `results.tsv` and has `harness/usage-limit-reached`.
- Run 8: has `harness/usage-limit-reached`.
- Run 10: has `harness/usage-limit-reached` and no `results.tsv`.
