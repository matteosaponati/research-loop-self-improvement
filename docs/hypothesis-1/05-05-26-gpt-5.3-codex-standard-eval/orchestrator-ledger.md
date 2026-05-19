# Harness Orchestrator Ledger

- Updated: 2026-05-06T10:01:09+02:00
- Host: login01
- Repo: /home/matteosaponati/research-loops-stresstest

## Configuration

- `archive_grace_seconds`: `120`
- `archive_root`: `/home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval`
- `codex_min_remaining_seconds`: `900`
- `codex_model`: `gpt-5.3-codex`
- `codex_reasoning_effort`: `medium`
- `codex_stop_after_seconds`: `14400`
- `dead_count`: `0`
- `exclude_nodes`: `dgx04`
- `max_active`: `7`
- `noisy_count`: `0`
- `poll_seconds`: `300`
- `std_count`: `10`
- `time_limit`: `04:15:00`
- `usage_limit_fallback_wait_seconds`: `3600`

## Cases

| Case | State | Eval | Latest job | Rows | Resume after | Archive |
| --- | --- | --- | --- | ---: | --- | --- |
| std1 | completed | `val_bpb` | `412150` | 35 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std1-std-gpt53codex-medium-4h-orchestrated-std1-gpt53codex-medium-4h-orchestrated-1-20260505-200241 |
| std2 | completed | `val_bpb` | `412151` | 35 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std2-std-gpt53codex-medium-4h-orchestrated-std2-gpt53codex-medium-4h-orchestrated-2-20260505-200241 |
| std3 | completed | `val_bpb` | `412152` | 34 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std3-std-gpt53codex-medium-4h-orchestrated-std3-gpt53codex-medium-4h-orchestrated-3-20260505-200241 |
| std4 | running | `val_bpb` | `415508` |  |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std4-std-gpt53codex-medium-4h-orchestrated-std4-gpt53codex-medium-4h-orchestrated-4-20260506-100108 |
| std5 | running | `val_bpb` | `415509` |  |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std5-std-gpt53codex-medium-4h-orchestrated-std5-gpt53codex-medium-4h-orchestrated-5-20260506-100108 |
| std6 | running | `val_bpb` | `415510` |  |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std6-std-gpt53codex-medium-4h-orchestrated-std6-gpt53codex-medium-4h-orchestrated-6-20260506-100109 |
| std7 | running | `val_bpb` | `415511` |  |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std7-std-gpt53codex-medium-4h-orchestrated-std7-gpt53codex-medium-4h-orchestrated-7-20260506-100109 |
| std8 | running | `val_bpb` | `415512` |  |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std8-std-gpt53codex-medium-4h-orchestrated-std8-gpt53codex-medium-4h-orchestrated-8-20260506-100109 |
| std9 | running | `val_bpb` | `415513` |  |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std9-std-gpt53codex-medium-4h-orchestrated-std9-gpt53codex-medium-4h-orchestrated-9-20260506-100109 |
| std10 | running | `val_bpb` | `415514` |  |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/05-05-26-gpt-5.3-codex-standard-eval/research-loop-agent-std10-std-gpt53codex-medium-4h-orchestrated-std10-gpt53codex-medium-4h-orchestrated-10-20260506-100109 |

## Events

- 2026-05-05T20:02:41+02:00: created new orchestrator state
- 2026-05-05T20:02:41+02:00: orchestrator started
- 2026-05-05T20:02:41+02:00 `std1`: submitting research-loop-agent-std1-std-gpt53codex-medium-4h-orchestrated-std1-gpt53codex-medium-4h-orchestrated-1-20260505-200241
- 2026-05-05T20:02:41+02:00 `std1`: submitted research-loop-agent-std1-std-gpt53codex-medium-4h-orchestrated-std1-gpt53codex-medium-4h-orchestrated-1-20260505-200241 as Slurm job 412150
- 2026-05-05T20:02:41+02:00 `std2`: submitting research-loop-agent-std2-std-gpt53codex-medium-4h-orchestrated-std2-gpt53codex-medium-4h-orchestrated-2-20260505-200241
- 2026-05-05T20:02:41+02:00 `std2`: submitted research-loop-agent-std2-std-gpt53codex-medium-4h-orchestrated-std2-gpt53codex-medium-4h-orchestrated-2-20260505-200241 as Slurm job 412151
- 2026-05-05T20:02:41+02:00 `std3`: submitting research-loop-agent-std3-std-gpt53codex-medium-4h-orchestrated-std3-gpt53codex-medium-4h-orchestrated-3-20260505-200241
- 2026-05-05T20:02:41+02:00 `std3`: submitted research-loop-agent-std3-std-gpt53codex-medium-4h-orchestrated-std3-gpt53codex-medium-4h-orchestrated-3-20260505-200241 as Slurm job 412152
- 2026-05-05T20:02:41+02:00: orchestrator stopped after one polling iteration
- 2026-05-05T20:03:02+02:00: resumed existing orchestrator state
- 2026-05-05T20:03:02+02:00: orchestrator started
- 2026-05-06T10:01:08+02:00: resumed existing orchestrator state
- 2026-05-06T10:01:08+02:00: orchestrator started
- 2026-05-06T10:01:08+02:00 `std1`: research-loop-agent-std1-std-gpt53codex-medium-4h-orchestrated-std1-gpt53codex-medium-4h-orchestrated-1-20260505-200241 completed with 35 result rows
- 2026-05-06T10:01:08+02:00 `std2`: research-loop-agent-std2-std-gpt53codex-medium-4h-orchestrated-std2-gpt53codex-medium-4h-orchestrated-2-20260505-200241 completed with 35 result rows
- 2026-05-06T10:01:08+02:00 `std3`: research-loop-agent-std3-std-gpt53codex-medium-4h-orchestrated-std3-gpt53codex-medium-4h-orchestrated-3-20260505-200241 completed with 34 result rows
- 2026-05-06T10:01:08+02:00 `std4`: submitting research-loop-agent-std4-std-gpt53codex-medium-4h-orchestrated-std4-gpt53codex-medium-4h-orchestrated-4-20260506-100108
- 2026-05-06T10:01:08+02:00 `std4`: submitted research-loop-agent-std4-std-gpt53codex-medium-4h-orchestrated-std4-gpt53codex-medium-4h-orchestrated-4-20260506-100108 as Slurm job 415508
- 2026-05-06T10:01:08+02:00 `std5`: submitting research-loop-agent-std5-std-gpt53codex-medium-4h-orchestrated-std5-gpt53codex-medium-4h-orchestrated-5-20260506-100108
- 2026-05-06T10:01:09+02:00 `std5`: submitted research-loop-agent-std5-std-gpt53codex-medium-4h-orchestrated-std5-gpt53codex-medium-4h-orchestrated-5-20260506-100108 as Slurm job 415509
- 2026-05-06T10:01:09+02:00 `std6`: submitting research-loop-agent-std6-std-gpt53codex-medium-4h-orchestrated-std6-gpt53codex-medium-4h-orchestrated-6-20260506-100109
- 2026-05-06T10:01:09+02:00 `std6`: submitted research-loop-agent-std6-std-gpt53codex-medium-4h-orchestrated-std6-gpt53codex-medium-4h-orchestrated-6-20260506-100109 as Slurm job 415510
- 2026-05-06T10:01:09+02:00 `std7`: submitting research-loop-agent-std7-std-gpt53codex-medium-4h-orchestrated-std7-gpt53codex-medium-4h-orchestrated-7-20260506-100109
- 2026-05-06T10:01:09+02:00 `std7`: submitted research-loop-agent-std7-std-gpt53codex-medium-4h-orchestrated-std7-gpt53codex-medium-4h-orchestrated-7-20260506-100109 as Slurm job 415511
- 2026-05-06T10:01:09+02:00 `std8`: submitting research-loop-agent-std8-std-gpt53codex-medium-4h-orchestrated-std8-gpt53codex-medium-4h-orchestrated-8-20260506-100109
- 2026-05-06T10:01:09+02:00 `std8`: submitted research-loop-agent-std8-std-gpt53codex-medium-4h-orchestrated-std8-gpt53codex-medium-4h-orchestrated-8-20260506-100109 as Slurm job 415512
- 2026-05-06T10:01:09+02:00 `std9`: submitting research-loop-agent-std9-std-gpt53codex-medium-4h-orchestrated-std9-gpt53codex-medium-4h-orchestrated-9-20260506-100109
- 2026-05-06T10:01:09+02:00 `std9`: submitted research-loop-agent-std9-std-gpt53codex-medium-4h-orchestrated-std9-gpt53codex-medium-4h-orchestrated-9-20260506-100109 as Slurm job 415513
- 2026-05-06T10:01:09+02:00 `std10`: submitting research-loop-agent-std10-std-gpt53codex-medium-4h-orchestrated-std10-gpt53codex-medium-4h-orchestrated-10-20260506-100109
- 2026-05-06T10:01:09+02:00 `std10`: submitted research-loop-agent-std10-std-gpt53codex-medium-4h-orchestrated-std10-gpt53codex-medium-4h-orchestrated-10-20260506-100109 as Slurm job 415514
- 2026-05-06T10:01:09+02:00: orchestrator stopped after one polling iteration
