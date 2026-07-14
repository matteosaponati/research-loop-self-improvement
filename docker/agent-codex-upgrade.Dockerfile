ARG BASE_IMAGE=research-loop-agent:latest
FROM ${BASE_IMAGE}

ARG CODEX_PACKAGE=@openai/codex@latest
RUN npm install -g "${CODEX_PACKAGE}" && codex --version
