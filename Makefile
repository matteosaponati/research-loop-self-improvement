UV ?= uv
PYTHON ?= python
PYTHONPATH := research-loop
UV_PROJECT := --project research-loop
export UV_CACHE_DIR ?= .uv-cache
PY_FILES := research-loop/editable research-loop/immutable _evals/val_bpb

.PHONY: setup lint test ci

setup:
	$(UV) sync $(UV_PROJECT)

lint:
	PYTHONPATH=$(PYTHONPATH) $(UV) run --no-sync $(UV_PROJECT) $(PYTHON) -m compileall -q $(PY_FILES)

test: lint

ci: lint test
