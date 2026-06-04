# Harness Orchestrator Ledger

- Updated: 2026-05-05T22:02:23+02:00
- Host: login01
- Repo: /home/matteosaponati/research-loops-stresstest

## Configuration

- `archive_grace_seconds`: `120`
- `archive_root`: `/home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval`
- `codex_min_remaining_seconds`: `900`
- `codex_model`: `gpt-5.3-codex`
- `codex_reasoning_effort`: `medium`
- `codex_stop_after_seconds`: `14400`
- `dead_count`: `0`
- `exclude_nodes`: `dgx04`
- `max_active`: `3`
- `noisy_count`: `10`
- `poll_seconds`: `300`
- `std_count`: `0`
- `time_limit`: `04:15:00`
- `usage_limit_fallback_wait_seconds`: `3600`

## Cases

| Case | State | Eval | Latest job | Rows | Resume after | Archive |
| --- | --- | --- | --- | ---: | --- | --- |
| noisy1 | completed | `noisy_val_bpb` | `407269` | 39 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy1-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy1-gpt53codex-medium-4h-orchestrated-1-20260505-000212 |
| noisy2 | completed | `noisy_val_bpb` | `407270` | 36 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy2-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy2-gpt53codex-medium-4h-orchestrated-2-20260505-000213 |
| noisy3 | completed | `noisy_val_bpb` | `407271` | 37 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy3-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy3-gpt53codex-medium-4h-orchestrated-3-20260505-000213 |
| noisy4 | completed | `noisy_val_bpb` | `409940` | 33 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy4-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy4-gpt53codex-medium-4h-orchestrated-4-20260505-102321 |
| noisy5 | completed | `noisy_val_bpb` | `409941` | 34 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy5-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy5-gpt53codex-medium-4h-orchestrated-5-20260505-102321 |
| noisy6 | completed | `noisy_val_bpb` | `409942` | 34 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy6-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy6-gpt53codex-medium-4h-orchestrated-6-20260505-102322 |
| noisy7 | completed | `noisy_val_bpb` | `411587` | 30 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy7-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy7-gpt53codex-medium-4h-orchestrated-7-20260505-141720 |
| noisy8 | completed | `noisy_val_bpb` | `411588` | 31 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy8-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy8-gpt53codex-medium-4h-orchestrated-8-20260505-141721 |
| noisy9 | completed | `noisy_val_bpb` | `411589` | 30 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy9-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy9-gpt53codex-medium-4h-orchestrated-9-20260505-141721 |
| noisy10 | completed | `noisy_val_bpb` | `412036` | 37 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-noisy-eval/research-loop-agent-noisy10-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy10-gpt53codex-medium-4h-orchestrated-10-20260505-180722 |

## Events

- 2026-05-05T00:02:12+02:00: created new orchestrator state
- 2026-05-05T00:02:12+02:00: orchestrator started
- 2026-05-05T00:02:12+02:00 `noisy1`: submitting research-loop-agent-noisy1-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy1-gpt53codex-medium-4h-orchestrated-1-20260505-000212
- 2026-05-05T00:02:13+02:00 `noisy1`: submitted research-loop-agent-noisy1-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy1-gpt53codex-medium-4h-orchestrated-1-20260505-000212 as Slurm job 407269
- 2026-05-05T00:02:13+02:00 `noisy2`: submitting research-loop-agent-noisy2-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy2-gpt53codex-medium-4h-orchestrated-2-20260505-000213
- 2026-05-05T00:02:13+02:00 `noisy2`: submitted research-loop-agent-noisy2-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy2-gpt53codex-medium-4h-orchestrated-2-20260505-000213 as Slurm job 407270
- 2026-05-05T00:02:13+02:00 `noisy3`: submitting research-loop-agent-noisy3-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy3-gpt53codex-medium-4h-orchestrated-3-20260505-000213
- 2026-05-05T00:02:13+02:00 `noisy3`: submitted research-loop-agent-noisy3-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy3-gpt53codex-medium-4h-orchestrated-3-20260505-000213 as Slurm job 407271
- 2026-05-05T00:02:13+02:00: orchestrator stopped after one polling iteration
- 2026-05-05T00:02:41+02:00: resumed existing orchestrator state
- 2026-05-05T00:02:41+02:00: orchestrator started
- 2026-05-05T00:03:52+02:00: resumed existing orchestrator state
- 2026-05-05T00:03:52+02:00: orchestrator started
- 2026-05-05T10:23:21+02:00: resumed existing orchestrator state
- 2026-05-05T10:23:21+02:00: orchestrator started
- 2026-05-05T10:23:21+02:00 `noisy1`: research-loop-agent-noisy1-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy1-gpt53codex-medium-4h-orchestrated-1-20260505-000212 completed with 39 result rows
- 2026-05-05T10:23:21+02:00 `noisy2`: research-loop-agent-noisy2-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy2-gpt53codex-medium-4h-orchestrated-2-20260505-000213 completed with 36 result rows
- 2026-05-05T10:23:21+02:00 `noisy3`: research-loop-agent-noisy3-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy3-gpt53codex-medium-4h-orchestrated-3-20260505-000213 completed with 37 result rows
- 2026-05-05T10:23:21+02:00 `noisy4`: submitting research-loop-agent-noisy4-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy4-gpt53codex-medium-4h-orchestrated-4-20260505-102321
- 2026-05-05T10:23:21+02:00 `noisy4`: submitted research-loop-agent-noisy4-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy4-gpt53codex-medium-4h-orchestrated-4-20260505-102321 as Slurm job 409940
- 2026-05-05T10:23:21+02:00 `noisy5`: submitting research-loop-agent-noisy5-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy5-gpt53codex-medium-4h-orchestrated-5-20260505-102321
- 2026-05-05T10:23:22+02:00 `noisy5`: submitted research-loop-agent-noisy5-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy5-gpt53codex-medium-4h-orchestrated-5-20260505-102321 as Slurm job 409941
- 2026-05-05T10:23:22+02:00 `noisy6`: submitting research-loop-agent-noisy6-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy6-gpt53codex-medium-4h-orchestrated-6-20260505-102322
- 2026-05-05T10:23:22+02:00 `noisy6`: submitted research-loop-agent-noisy6-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy6-gpt53codex-medium-4h-orchestrated-6-20260505-102322 as Slurm job 409942
- 2026-05-05T14:17:20+02:00: resumed existing orchestrator state
- 2026-05-05T14:17:20+02:00: orchestrator started
- 2026-05-05T14:17:20+02:00 `noisy4`: research-loop-agent-noisy4-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy4-gpt53codex-medium-4h-orchestrated-4-20260505-102321 completed with 33 result rows
- 2026-05-05T14:17:20+02:00 `noisy5`: research-loop-agent-noisy5-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy5-gpt53codex-medium-4h-orchestrated-5-20260505-102321 completed with 34 result rows
- 2026-05-05T14:17:20+02:00 `noisy6`: research-loop-agent-noisy6-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy6-gpt53codex-medium-4h-orchestrated-6-20260505-102322 completed with 34 result rows
- 2026-05-05T14:17:20+02:00 `noisy7`: submitting research-loop-agent-noisy7-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy7-gpt53codex-medium-4h-orchestrated-7-20260505-141720
- 2026-05-05T14:17:21+02:00 `noisy7`: submitted research-loop-agent-noisy7-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy7-gpt53codex-medium-4h-orchestrated-7-20260505-141720 as Slurm job 411587
- 2026-05-05T14:17:21+02:00 `noisy8`: submitting research-loop-agent-noisy8-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy8-gpt53codex-medium-4h-orchestrated-8-20260505-141721
- 2026-05-05T14:17:21+02:00 `noisy8`: submitted research-loop-agent-noisy8-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy8-gpt53codex-medium-4h-orchestrated-8-20260505-141721 as Slurm job 411588
- 2026-05-05T14:17:21+02:00 `noisy9`: submitting research-loop-agent-noisy9-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy9-gpt53codex-medium-4h-orchestrated-9-20260505-141721
- 2026-05-05T14:17:21+02:00 `noisy9`: submitted research-loop-agent-noisy9-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy9-gpt53codex-medium-4h-orchestrated-9-20260505-141721 as Slurm job 411589
- 2026-05-05T18:07:22+02:00 `noisy7`: research-loop-agent-noisy7-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy7-gpt53codex-medium-4h-orchestrated-7-20260505-141720 completed with 30 result rows
- 2026-05-05T18:07:22+02:00 `noisy10`: submitting research-loop-agent-noisy10-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy10-gpt53codex-medium-4h-orchestrated-10-20260505-180722
- 2026-05-05T18:07:23+02:00 `noisy10`: submitted research-loop-agent-noisy10-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy10-gpt53codex-medium-4h-orchestrated-10-20260505-180722 as Slurm job 412036
- 2026-05-05T18:12:23+02:00 `noisy8`: research-loop-agent-noisy8-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy8-gpt53codex-medium-4h-orchestrated-8-20260505-141721 completed with 31 result rows
- 2026-05-05T18:17:23+02:00 `noisy9`: research-loop-agent-noisy9-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy9-gpt53codex-medium-4h-orchestrated-9-20260505-141721 completed with 30 result rows
- 2026-05-05T22:02:23+02:00 `noisy10`: research-loop-agent-noisy10-fixed-noise-gpt53codex-medium-4h-orchestrated-noisy10-gpt53codex-medium-4h-orchestrated-10-20260505-180722 completed with 37 result rows
- 2026-05-05T22:02:23+02:00: orchestrator finished; failures=none
