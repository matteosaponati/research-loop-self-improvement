#!/usr/bin/env bash
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
