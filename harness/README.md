# Docker SSH-GPU Harness

Run from the repo root. No virtualenv activation is needed; `docker_harness.sh`
uses `uv`.

```bash
GPU_SSH_HOST=<gpu-host> \
GPU_SSH_USER=<user> \
GPU_SSH_PORT=<port> \
GPU_SSH_KEY=/path/to/private_key \
GPU_REMOTE_ROOT=/root/research-loop-runs \
./docker_harness.sh \
  --agent codex \
  --agent-model gpt-5.4 \
  --reasoning-effort medium \
  --loops 0 \
  --run-id my-run-id \
  --job-name my-job-name \
  --eval-name val_bpb
```

This is one example:

```bash
GPU_SSH_HOST=80.188.223.202 \
GPU_SSH_USER=root \
GPU_SSH_PORT=18999 \
GPU_SSH_KEY=/Users/matteosaponati/.ssh/vast_gpu_key \
GPU_REMOTE_ROOT=/root/research-loop-runs \
./docker_harness.sh \
  --smoke \
  --agent codex \
  --agent-model gpt-5.4 \
  --reasoning-effort high \
  --loops 1 \
  --run-id vast-test-001 \
  --job-name vast-real-gpu-test \
  --eval-name val_bpb
```

```bash
GPU_SSH_HOST=80.188.223.202 \
GPU_SSH_USER=root \
GPU_SSH_PORT=18999 \
GPU_SSH_KEY=/Users/matteosaponati/.ssh/vast_gpu_key \
GPU_REMOTE_ROOT=/root/research-loop-runs \
./docker_harness.sh \
  --agent codex \
  --agent-model gpt-5.5 \
  --reasoning-effort xhigh \
  --loops 0 \
  --run-id gpt-5.5-xhigh-seed-1 \
  --job-name seed-1 \
  --time-limit-seconds 11700 \
  --eval-name val_bpb
```

The SSH key and SSH config stay on the host. Docker receives only the isolated
workspace, `/agent-home`, and a local broker URL/token.

Use `--broker-port <port>` or `GPU_BROKER_PORT=<port>` to pin the localhost
broker port when multiple harness jobs are running.

## Workflow

- `docker_harness.sh`: thin shell entrypoint into `python -m harness`.
- `__main__.py`: parses CLI and starts one harness run.
- `config.py`: opinionated CLI, fixed defaults, host validation.
- `workspace.py`: creates or resumes `.local/docker-harness/<run-id>/research-loop`.
- `scripts.py`: generated in-container `uv`, `git`, and entrypoint scripts.
- `docker_run.py`: starts the host broker and Docker container.
- `gpu_broker.py`: receives brokered experiment requests and runs them over SSH.
- `archive.py`: copies logs, results, and resume snapshot into `docs/experiments/`.
- `run.py`: linear orchestration glue for the full run.
- `util.py`: small filesystem, subprocess, and copy helpers.
