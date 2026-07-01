"""Generated runtime scripts written into each isolated workspace.

The host launcher writes these strings under ``memory/harness`` inside the
agent workspace before Docker starts.  They are scripts, not Python functions,
because they must run inside the agent container where they can sit ahead of
the real ``uv`` and ``git`` commands on ``PATH``.

The generated scripts are intentionally narrow:

* ``UV_WRAPPER`` intercepts only ``immutable/run_experiment.py`` and forwards it
  to the host broker.  All other ``uv`` commands delegate to the real ``uv``.
* ``GIT_WRAPPER`` blocks commits near the soft deadline so a run can archive
  cleanly before the hard Docker timeout.
* ``CONTAINER_ENTRYPOINT`` sets up caches, writes broker metadata, starts the
  selected agent, and restarts it until the loop count or deadline is reached.
"""

from __future__ import annotations


UV_WRAPPER = r'''#!/usr/bin/env bash
set -euo pipefail

# The agent is instructed to run the normal project command.  This wrapper keeps
# that interface intact while routing only immutable/run_experiment.py to the
# host-side broker.  Any other uv command must behave exactly like real uv.
is_experiment_run=0
is_prepare_run=0
for arg in "$@"; do
  [[ "${arg}" == "immutable/run_experiment.py" || "${arg}" == */immutable/run_experiment.py ]] && is_experiment_run=1
  [[ "${arg}" == "immutable/prepare.py" || "${arg}" == */immutable/prepare.py ]] && is_prepare_run=1
done

if [[ "${is_prepare_run}" == "1" ]]; then
  mkdir -p .local/data .local/tokenizer
  touch .local/data/.remote-gpu-ready .local/tokenizer/.remote-gpu-ready
  echo "Remote GPU broker prepares data/tokenizer on the SSH host; local prepare is a no-op."
  exit 0
fi

if [[ "${is_experiment_run}" != "1" ]]; then
  exec "${HARNESS_REAL_UV:-uv}" "$@"
fi

if [[ -f memory/harness/gpu-broker-url ]]; then
  GPU_BROKER_URL="$(tr -d '\r\n' < memory/harness/gpu-broker-url)"
fi
if [[ -f memory/harness/gpu-broker-token ]]; then
  GPU_BROKER_TOKEN="$(tr -d '\r\n' < memory/harness/gpu-broker-token)"
fi
if [[ -z "${GPU_BROKER_URL:-}" || -z "${GPU_BROKER_TOKEN:-}" ]]; then
  echo "Missing GPU broker URL/token in memory/harness." >&2
  exit 1
fi

# Do not let the agent start a remote GPU job if there is not enough wall-clock
# time left for the result to sync back and for the archive path to run.
HARNESS_CODEX_STOP_AT="${HARNESS_CODEX_STOP_AT:-0}"
HARNESS_MIN_REMAINING_SECONDS="${HARNESS_MIN_REMAINING_SECONDS:-0}"
HARNESS_DEADLINE_SENTINEL="${HARNESS_DEADLINE_SENTINEL:-memory/harness/soft-deadline-reached}"
if [[ "${HARNESS_CODEX_STOP_AT}" =~ ^[0-9]+$ && "${HARNESS_CODEX_STOP_AT}" -gt 0 ]]; then
  now="$(date +%s)"
  remaining=$((HARNESS_CODEX_STOP_AT - now))
  if (( remaining < HARNESS_MIN_REMAINING_SECONDS )); then
    mkdir -p "$(dirname "${HARNESS_DEADLINE_SENTINEL}")"
    printf 'refused remote experiment at %s: %ss remain, minimum is %ss\n' "$(date -Is)" "${remaining}" "${HARNESS_MIN_REMAINING_SECONDS}" > "${HARNESS_DEADLINE_SENTINEL}"
    echo "HARNESS_SOFT_DEADLINE_REACHED: ${remaining}s remain; refusing remote GPU experiment" >&2
    exit 75
  fi
fi

python3 - "$@" <<'PY'
import json
import os
import sys
import urllib.error
import urllib.request

request = urllib.request.Request(
    os.environ["GPU_BROKER_URL"].rstrip("/") + "/run",
    data=json.dumps({"args": sys.argv[1:]}).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {os.environ['GPU_BROKER_TOKEN']}",
        "Content-Type": "application/json",
    },
)
try:
    with urllib.request.urlopen(request, timeout=None) as response:
        data = json.loads(response.read().decode("utf-8"))
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    if exc.code == 401:
        sys.stderr.write("gpu broker returned 401 unauthorized: token mismatch for /run request\n")
    sys.stderr.write(body)
    raise SystemExit(1)
except Exception as exc:
    sys.stderr.write(f"gpu broker request failed: {exc}\n")
    raise SystemExit(1)

sys.stdout.write(data.get("stdout", ""))
sys.stderr.write(data.get("stderr", ""))
raise SystemExit(int(data.get("returncode", 1)))
PY
'''
"""Shell wrapper placed before real ``uv`` inside the container."""


GIT_WRAPPER = r'''#!/usr/bin/env bash
set -euo pipefail

# Git remains normal except for commit attempts near the soft deadline.  Blocking
# late commits avoids half-recorded experiment states right before Docker stops.
if [[ "${1:-}" == "commit" ]]; then
  HARNESS_CODEX_STOP_AT="${HARNESS_CODEX_STOP_AT:-0}"
  HARNESS_MIN_REMAINING_SECONDS="${HARNESS_MIN_REMAINING_SECONDS:-0}"
  HARNESS_DEADLINE_SENTINEL="${HARNESS_DEADLINE_SENTINEL:-memory/harness/soft-deadline-reached}"
  if [[ "${HARNESS_CODEX_STOP_AT}" =~ ^[0-9]+$ && "${HARNESS_CODEX_STOP_AT}" -gt 0 ]]; then
    now="$(date +%s)"
    remaining=$((HARNESS_CODEX_STOP_AT - now))
    if (( remaining < HARNESS_MIN_REMAINING_SECONDS )); then
      mkdir -p "$(dirname "${HARNESS_DEADLINE_SENTINEL}")"
      printf 'refused git commit at %s: %ss remain, minimum is %ss\n' "$(date -Is)" "${remaining}" "${HARNESS_MIN_REMAINING_SECONDS}" > "${HARNESS_DEADLINE_SENTINEL}"
      echo "HARNESS_SOFT_DEADLINE_REACHED: ${remaining}s remain; refusing git commit" >&2
      exit 75
    fi
  fi
fi

exec "${HARNESS_REAL_GIT:-git}" "$@"
'''
"""Shell wrapper placed before real ``git`` inside the container."""


CONTAINER_ENTRYPOINT = r'''#!/usr/bin/env bash
set -euo pipefail

# This entrypoint is the only long-running process in the agent container.  It
# prepares the local tool environment, starts the agent, watches for usage-limit
# and deadline stops, and optionally restarts the agent for another loop.
cd /workspace
AGENT="${AGENT:-codex}"
AGENT_MAX_LOOPS="${AGENT_MAX_LOOPS:-0}"
AGENT_MODEL="${AGENT_MODEL:-}"
AGENT_REASONING_EFFORT="${AGENT_REASONING_EFFORT:-}"
HARNESS_CODEX_STOP_AT="${HARNESS_CODEX_STOP_AT:-0}"
HARNESS_MIN_REMAINING_SECONDS="${HARNESS_MIN_REMAINING_SECONDS:-0}"
RESTART_DELAY_SECONDS="${RESTART_DELAY_SECONDS:-10}"
HARNESS_DEADLINE_SENTINEL="memory/harness/soft-deadline-reached"
UV_CACHE_DIR="${UV_CACHE_DIR:-/workspace/.uv-cache}"
UV_TEMP_DIR="${UV_TEMP_DIR:-/workspace/.uv-tmp}"
export UV_CACHE_DIR UV_TEMP_DIR XDG_CACHE_HOME="${XDG_CACHE_HOME:-${UV_CACHE_DIR}}"
export TMPDIR="${TMPDIR:-${UV_TEMP_DIR}}" TMP="${TMP:-${UV_TEMP_DIR}}" TEMP="${TEMP:-${UV_TEMP_DIR}}"
mkdir -p "${UV_CACHE_DIR}" "${UV_TEMP_DIR}" memory/harness "memory/${AGENT}"
LOG="memory/harness/docker-harness.log"

usage_limit_detected() {
  local path="$1"
  [[ -f "${path}" ]] || return 1
  grep -Eiq "usage limit|rate limit|Switch to another model now|try again at [0-9]{1,2}:[0-9]{2} [AP]M" "${path}"
}

write_status() {
  local reason="$1"
  local session="${2:-}"
  local log="${3:-}"
  {
    printf 'stop_reason=%s\n' "${reason}"
    printf 'stopped_at=%s\n' "$(date -Is)"
    printf 'agent=%s\n' "${AGENT}"
    printf 'agent_session=%s\n' "${session}"
    printf 'agent_log=%s\n' "${log}"
  } > memory/harness/job-status.env
}

build_prompt() {
  local prompt="$1"
  cat program.md > "${prompt}"
  {
    printf '\n\n# Current memory status\n\n'
    if [[ -f memory/results.tsv ]]; then
      tail -n 25 memory/results.tsv
    else
      printf 'No memory/results.tsv exists yet.\n'
    fi
  } >> "${prompt}"
}

start_agent() {
  local prompt="$1"
  local log="$2"
  if [[ "${AGENT}" == "codex" ]]; then
    local args=()
    [[ -n "${AGENT_MODEL}" ]] && args+=(-m "${AGENT_MODEL}")
    [[ -n "${AGENT_REASONING_EFFORT}" ]] && args+=(-c "model_reasoning_effort=\"${AGENT_REASONING_EFFORT}\"")
    codex exec "${args[@]}" --dangerously-bypass-approvals-and-sandbox --ignore-user-config --ephemeral -C /workspace "$(cat "${prompt}")" > "${log}" 2>&1 &
    AGENT_PID=$!
    return
  fi
  local args=(-p --verbose --output-format stream-json --include-partial-messages --include-hook-events --dangerously-skip-permissions --no-session-persistence)
  [[ -n "${AGENT_MODEL}" ]] && args+=(--model "${AGENT_MODEL}")
  [[ -n "${AGENT_REASONING_EFFORT}" ]] && args+=(--effort "${AGENT_REASONING_EFFORT}")
  claude "${args[@]}" "$(cat "${prompt}")" > "${log}" 2>&1 &
  AGENT_PID=$!
}

{
  echo "workspace: $(pwd)"
  echo "container: ${HOSTNAME:-unknown}"
  echo "broker: ${GPU_BROKER_URL}"
  echo "agent: ${AGENT}"
  command -v uv
  command -v git
  uv sync

  export HARNESS_REAL_UV="$(command -v uv)"
  export HARNESS_REAL_GIT="$(command -v git)"
  export HARNESS_DEADLINE_SENTINEL
  printf '%s\n' "${GPU_BROKER_URL}" > memory/harness/gpu-broker-url
  printf '%s\n' "${GPU_BROKER_TOKEN}" > memory/harness/gpu-broker-token
  export PATH="/workspace/memory/harness/bin:${PATH}"
  # Codex may spawn command shells with a sanitized PATH.  Make uv interception
  # robust by replacing the real uv path inside this ephemeral container too.
  if [[ "${HARNESS_REAL_UV}" != "/workspace/memory/harness/bin/uv" && -w "$(dirname "${HARNESS_REAL_UV}")" ]]; then
    mv "${HARNESS_REAL_UV}" /usr/local/bin/uv-real
    ln -sf /workspace/memory/harness/bin/uv "${HARNESS_REAL_UV}"
    export HARNESS_REAL_UV=/usr/local/bin/uv-real
  fi

  session=0
  while (( AGENT_MAX_LOOPS == 0 || session < AGENT_MAX_LOOPS )); do
    if (( HARNESS_CODEX_STOP_AT > 0 )); then
      remaining=$((HARNESS_CODEX_STOP_AT - $(date +%s)))
      if (( remaining < HARNESS_MIN_REMAINING_SECONDS )); then
        write_status "soft_deadline" "${session}" ""
        break
      fi
    fi
    session=$((session + 1))
    prompt="memory/harness/current-prompt-${session}.md"
    agent_log="memory/${AGENT}/${AGENT}-session-$(printf '%05d' "${session}").log"
    build_prompt "${prompt}"
    echo "starting ${AGENT} session ${session} at $(date -Is)"

    set +e
    start_agent "${prompt}" "${agent_log}"
    pid="${AGENT_PID}"
    deadline_stop=0
    usage_stop=0
    while kill -0 "${pid}" >/dev/null 2>&1; do
      if usage_limit_detected "${agent_log}"; then
        usage_stop=1
        write_status "${AGENT}_usage_limit" "${session}" "${agent_log}"
        kill -TERM "${pid}" >/dev/null 2>&1 || true
        break
      fi
      if [[ -f "${HARNESS_DEADLINE_SENTINEL}" ]]; then
        deadline_stop=1
        write_status "soft_deadline" "${session}" "${agent_log}"
        kill -TERM "${pid}" >/dev/null 2>&1 || true
        break
      fi
      if (( HARNESS_CODEX_STOP_AT > 0 && $(date +%s) >= HARNESS_CODEX_STOP_AT )); then
        deadline_stop=1
        write_status "soft_deadline" "${session}" "${agent_log}"
        kill -TERM "${pid}" >/dev/null 2>&1 || true
        break
      fi
      sleep 10
    done
    wait "${pid}"
    status=$?
    set -e
    (( usage_stop == 1 || deadline_stop == 1 )) && break
    (( AGENT_MAX_LOOPS != 0 && session >= AGENT_MAX_LOOPS )) && break
    echo "${AGENT} exited with status ${status}; restarting in ${RESTART_DELAY_SECONDS}s"
    sleep "${RESTART_DELAY_SECONDS}"
  done
} 2>&1 | tee -a "${LOG}"
'''
"""Container entrypoint executed as PID 1 of the agent workload."""
