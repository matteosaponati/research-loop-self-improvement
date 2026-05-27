# Harness Orchestrator Ledger

- Updated: 2026-05-05T01:09:56+02:00
- Host: login01
- Repo: /home/matteosaponati/research-loops-stresstest

## Configuration

- `codex_model`: `gpt-5.3-codex`
- `codex_reasoning_effort`: `medium`
- `codex_stop_after_seconds`: `14400`
- `codex_min_remaining_seconds`: `900`
- `time_limit`: `04:15:00`
- `exclude_nodes`: `dgx04`
- `max_active`: `3`
- `poll_seconds`: `300`
- `std_count`: `0`
- `dead_count`: `10`
- `noisy_count`: `0`
- `usage_limit_fallback_wait_seconds`: `3600`
- `archive_grace_seconds`: `120`
- `archive_root`: `/home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval`

## Cases

| Case | State | Eval | Latest job | Rows | Resume after | Archive |
| --- | --- | --- | --- | ---: | --- | --- |
| dead1 | completed | `dead_code_bpb` | `404528` | 52 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead1-dead-gpt53codex-medium-4h-orchestrated-dead1-gpt53codex-medium-4h-orchestrated-1-20260504-094953 |
| dead2 | completed | `dead_code_bpb` | `404529` | 36 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead2-dead-gpt53codex-medium-4h-orchestrated-dead2-gpt53codex-medium-4h-orchestrated-2-20260504-094953 |
| dead3 | completed | `dead_code_bpb` | `404530` | 35 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead3-dead-gpt53codex-medium-4h-orchestrated-dead3-gpt53codex-medium-4h-orchestrated-3-20260504-094953 |
| dead4 | completed | `dead_code_bpb` | `405605` | 37 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead4-dead-gpt53codex-medium-4h-orchestrated-dead4-gpt53codex-medium-4h-orchestrated-4-20260504-133954 |
| dead5 | completed | `dead_code_bpb` | `405606` | 34 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead5-dead-gpt53codex-medium-4h-orchestrated-dead5-gpt53codex-medium-4h-orchestrated-5-20260504-133954 |
| dead6 | completed | `dead_code_bpb` | `405609` | 49 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead6-dead-gpt53codex-medium-4h-orchestrated-dead6-gpt53codex-medium-4h-orchestrated-6-20260504-134454 |
| dead7 | completed | `dead_code_bpb` | `406179` | 36 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead7-dead-gpt53codex-medium-4h-orchestrated-dead7-gpt53codex-medium-4h-orchestrated-7-20260504-172955 |
| dead8 | completed | `dead_code_bpb` | `406180` | 35 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead8-dead-gpt53codex-medium-4h-orchestrated-dead8-gpt53codex-medium-4h-orchestrated-8-20260504-172955 |
| dead9 | completed | `dead_code_bpb` | `406197` | 37 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead9-dead-gpt53codex-medium-4h-orchestrated-dead9-gpt53codex-medium-4h-orchestrated-9-20260504-173455 |
| dead10 | completed | `dead_code_bpb` | `406736` | 36 |  | /home/matteosaponati/research-loops-stresstest/docs/experiments-logs/04-05-26-gpt-5.3-codex-deadcode-eval/research-loop-agent-dead10-dead-gpt53codex-medium-4h-orchestrated-dead10-gpt53codex-medium-4h-orchestrated-10-20260504-211956 |

## Events

- 2026-05-04T09:49:53+02:00: created new orchestrator state
- 2026-05-04T09:49:53+02:00: orchestrator started
- 2026-05-04T09:49:53+02:00 `dead1`: submitting research-loop-agent-dead1-dead-gpt53codex-medium-4h-orchestrated-dead1-gpt53codex-medium-4h-orchestrated-1-20260504-094953
- 2026-05-04T09:49:53+02:00 `dead1`: submitted research-loop-agent-dead1-dead-gpt53codex-medium-4h-orchestrated-dead1-gpt53codex-medium-4h-orchestrated-1-20260504-094953 as Slurm job 404528
- 2026-05-04T09:49:53+02:00 `dead2`: submitting research-loop-agent-dead2-dead-gpt53codex-medium-4h-orchestrated-dead2-gpt53codex-medium-4h-orchestrated-2-20260504-094953
- 2026-05-04T09:49:53+02:00 `dead2`: submitted research-loop-agent-dead2-dead-gpt53codex-medium-4h-orchestrated-dead2-gpt53codex-medium-4h-orchestrated-2-20260504-094953 as Slurm job 404529
- 2026-05-04T09:49:53+02:00 `dead3`: submitting research-loop-agent-dead3-dead-gpt53codex-medium-4h-orchestrated-dead3-gpt53codex-medium-4h-orchestrated-3-20260504-094953
- 2026-05-04T09:49:54+02:00 `dead3`: submitted research-loop-agent-dead3-dead-gpt53codex-medium-4h-orchestrated-dead3-gpt53codex-medium-4h-orchestrated-3-20260504-094953 as Slurm job 404530
- 2026-05-04T13:39:54+02:00 `dead2`: research-loop-agent-dead2-dead-gpt53codex-medium-4h-orchestrated-dead2-gpt53codex-medium-4h-orchestrated-2-20260504-094953 completed with 36 result rows
- 2026-05-04T13:39:54+02:00 `dead3`: research-loop-agent-dead3-dead-gpt53codex-medium-4h-orchestrated-dead3-gpt53codex-medium-4h-orchestrated-3-20260504-094953 completed with 35 result rows
- 2026-05-04T13:39:54+02:00 `dead4`: submitting research-loop-agent-dead4-dead-gpt53codex-medium-4h-orchestrated-dead4-gpt53codex-medium-4h-orchestrated-4-20260504-133954
- 2026-05-04T13:39:54+02:00 `dead4`: submitted research-loop-agent-dead4-dead-gpt53codex-medium-4h-orchestrated-dead4-gpt53codex-medium-4h-orchestrated-4-20260504-133954 as Slurm job 405605
- 2026-05-04T13:39:54+02:00 `dead5`: submitting research-loop-agent-dead5-dead-gpt53codex-medium-4h-orchestrated-dead5-gpt53codex-medium-4h-orchestrated-5-20260504-133954
- 2026-05-04T13:39:54+02:00 `dead5`: submitted research-loop-agent-dead5-dead-gpt53codex-medium-4h-orchestrated-dead5-gpt53codex-medium-4h-orchestrated-5-20260504-133954 as Slurm job 405606
- 2026-05-04T13:44:54+02:00 `dead1`: research-loop-agent-dead1-dead-gpt53codex-medium-4h-orchestrated-dead1-gpt53codex-medium-4h-orchestrated-1-20260504-094953 completed with 52 result rows
- 2026-05-04T13:44:54+02:00 `dead6`: submitting research-loop-agent-dead6-dead-gpt53codex-medium-4h-orchestrated-dead6-gpt53codex-medium-4h-orchestrated-6-20260504-134454
- 2026-05-04T13:44:54+02:00 `dead6`: submitted research-loop-agent-dead6-dead-gpt53codex-medium-4h-orchestrated-dead6-gpt53codex-medium-4h-orchestrated-6-20260504-134454 as Slurm job 405609
- 2026-05-04T17:29:55+02:00 `dead4`: research-loop-agent-dead4-dead-gpt53codex-medium-4h-orchestrated-dead4-gpt53codex-medium-4h-orchestrated-4-20260504-133954 completed with 37 result rows
- 2026-05-04T17:29:55+02:00 `dead5`: research-loop-agent-dead5-dead-gpt53codex-medium-4h-orchestrated-dead5-gpt53codex-medium-4h-orchestrated-5-20260504-133954 completed with 34 result rows
- 2026-05-04T17:29:55+02:00 `dead7`: submitting research-loop-agent-dead7-dead-gpt53codex-medium-4h-orchestrated-dead7-gpt53codex-medium-4h-orchestrated-7-20260504-172955
- 2026-05-04T17:29:55+02:00 `dead7`: submitted research-loop-agent-dead7-dead-gpt53codex-medium-4h-orchestrated-dead7-gpt53codex-medium-4h-orchestrated-7-20260504-172955 as Slurm job 406179
- 2026-05-04T17:29:55+02:00 `dead8`: submitting research-loop-agent-dead8-dead-gpt53codex-medium-4h-orchestrated-dead8-gpt53codex-medium-4h-orchestrated-8-20260504-172955
- 2026-05-04T17:29:55+02:00 `dead8`: submitted research-loop-agent-dead8-dead-gpt53codex-medium-4h-orchestrated-dead8-gpt53codex-medium-4h-orchestrated-8-20260504-172955 as Slurm job 406180
- 2026-05-04T17:34:55+02:00 `dead6`: research-loop-agent-dead6-dead-gpt53codex-medium-4h-orchestrated-dead6-gpt53codex-medium-4h-orchestrated-6-20260504-134454 completed with 49 result rows
- 2026-05-04T17:34:55+02:00 `dead9`: submitting research-loop-agent-dead9-dead-gpt53codex-medium-4h-orchestrated-dead9-gpt53codex-medium-4h-orchestrated-9-20260504-173455
- 2026-05-04T17:34:55+02:00 `dead9`: submitted research-loop-agent-dead9-dead-gpt53codex-medium-4h-orchestrated-dead9-gpt53codex-medium-4h-orchestrated-9-20260504-173455 as Slurm job 406197
- 2026-05-04T21:19:56+02:00 `dead7`: research-loop-agent-dead7-dead-gpt53codex-medium-4h-orchestrated-dead7-gpt53codex-medium-4h-orchestrated-7-20260504-172955 completed with 36 result rows
- 2026-05-04T21:19:56+02:00 `dead10`: submitting research-loop-agent-dead10-dead-gpt53codex-medium-4h-orchestrated-dead10-gpt53codex-medium-4h-orchestrated-10-20260504-211956
- 2026-05-04T21:19:56+02:00 `dead10`: submitted research-loop-agent-dead10-dead-gpt53codex-medium-4h-orchestrated-dead10-gpt53codex-medium-4h-orchestrated-10-20260504-211956 as Slurm job 406736
- 2026-05-04T21:24:56+02:00 `dead8`: research-loop-agent-dead8-dead-gpt53codex-medium-4h-orchestrated-dead8-gpt53codex-medium-4h-orchestrated-8-20260504-172955 completed with 35 result rows
- 2026-05-04T21:54:56+02:00 `dead9`: research-loop-agent-dead9-dead-gpt53codex-medium-4h-orchestrated-dead9-gpt53codex-medium-4h-orchestrated-9-20260504-173455 completed with 37 result rows
- 2026-05-05T01:09:56+02:00 `dead10`: research-loop-agent-dead10-dead-gpt53codex-medium-4h-orchestrated-dead10-gpt53codex-medium-4h-orchestrated-10-20260504-211956 completed with 36 result rows
- 2026-05-05T01:09:56+02:00: orchestrator finished; failures=none
