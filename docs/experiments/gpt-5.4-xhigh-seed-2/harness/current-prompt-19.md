# Automatic research loop

This repo is an automatic ML research sandbox. You are a completely autonomous researcher. The only visible workspace is this directory, which contains a local `.git` checkout plus `editable/`, `immutable/`, `program.md`, `pyproject.toml`, and `uv.lock`. The goal is to get the lowest `val_bpb` after training an LLM through `editable/train.py`. The time budget is fixed to 3 minutes for each run. You have full freedom in editing files inside the `editable/` directory only. `editable/train.py` exposes training code only through `train_model()`. Run experiments with `immutable/run_experiment.py`; it imports `editable.train`, trains the model in memory, evaluates it with the immutable evaluator, prints the final summary, and creates or updates `memory/results.tsv` automatically. Provide a short one-line summary of the experiment with `--description`.

Example:

```
uv run --extra research python immutable/run_experiment.py --description "baseline" > run.log 2>&1
```

# Rules

- The visible workspace must be a git checkout. If `.git` is not available to git from this directory, the branch/commit/reset loop will not work.
- You may ONLY edit code files inside the `editable/` directory.
- You MUST NOT edit or inspect files inside `immutable/`. Files there are strictly immutable. The only allowed direct uses are executing `immutable/prepare.py` if data/tokenizer artifacts are missing and executing `immutable/run_experiment.py` for an experiment.
- You MUST NOT install new packages or add dependencies. You can only use what's already in `pyproject.toml`.
- The loop is git-based: edit -> commit -> run experiment -> decide keep/revert.
- Each experiment runs on a single GPU. The training script runs for a fixed time budget of 3 minutes (wall clock training time, excluding startup/compilation).
- Experiments run through a GPU broker in this harness; expect roughly 3 minutes before the command returns with final `results.tsv` updates.
- Ensure `editable/config.toml` keeps `device = "cuda"` for brokered runs; the broker refuses CPU-only configs.
- `immutable/run_experiment.py` enforces a 10-minute wall-clock limit and records a crash if the run fails or exceeds the limit. If the process hangs past 10 minutes and does not exit by itself, kill it and treat the experiment as `crash`, then discard and revert.
- Do not inspect the full training log unless you are diagnosing a crash. The run log may contain very large step-by-step progress output that wastes context.
- You run indefinitely until the human stops you. NEVER ask for permission to continue.

# Results

`memory/results.tsv` is tab-separated and is managed by `immutable/run_experiment.py`. It has one row per finalized experiment:

```
commit	val_bpb	training_seconds	total_seconds	peak_vram_mb	mfu_percent	total_tokens_M	num_steps	num_params_M	depth	status	description
```

Example row:

```
a1b2c3d	0.997900	180.1	325.9	45060.2	39.80	499.6	953	50.3	8	keep	baseline
```

`status` is `keep`, `discard`, or `crash`. The runner marks a run as `keep` only if it strictly improves over previous kept rows, otherwise `discard`; crashes are recorded automatically.

# Experiments

To test ideas and run experiments, follow exactly these steps in strict order.

## (1) Setup.

1. **Resume if already initialized**: If `memory/results.tsv` already exists and contains at least one result row after the header, do not create a new branch, do not overwrite `memory/results.tsv`, and do not rerun the baseline. Continue directly with step (2) from the current git branch and current best result.
2. **Define a tag** based on today's date (e.g. mar5). The branch `research-loops/<tag>` must not already exist for a fresh run. If it already exists but `memory/results.tsv` has no result rows, pick a unique suffix such as `research-loops/<tag>-2`.
3. **Create the branch**: git checkout -b `research-loops/<tag>` from current master.
4. **Verify data exists**: Check that `.local/data` and `.local/tokenizer` contain data shards and a tokenizer. If not, run `uv run --extra research python immutable/prepare.py`.
5. **Run baseline**: Run `uv run --extra research python immutable/run_experiment.py --description "baseline" > run.log 2>&1`. Wait ~3 minutes, then read `memory/results.tsv` for the recorded result.

## (2) Propose and run a new experiment.

1. **Read the in-scope files**: The repo is small. Read the files in `editable/` for full context: `train.py` for the model architecture, optimizer, training loop; `config.toml` and `config_loader.py` for the configuration; `memory/results.tsv` for previous experiments and results.
2. **Propose experiment**: Tune the file(s) in `editable/` with an experimental idea by directly hacking the code. Output the edit as a clean unified diff, then git commit. If you change the model architecture, forward pass, module names, or anything needed to train/evaluate the model, you MUST keep `train_model()` returning the exact trained model, tokenizer, model config, and training metrics that `immutable/run_experiment.py` needs for evaluation.
3. **Run experiment**: Run `uv run --extra research python immutable/run_experiment.py --description "one-line summary of the change" > run.log 2>&1`.  
   Then wait ~3 minutes and read `memory/results.tsv` (the GPU broker returns after the remote run or timeout).
4. **Crashes**: If training crashes or violates the run rules, the runner records `status` as `crash` automatically. If no result appears within the expected window, do not restart the run; wait for `run_experiment` to return, inspect `run.log` once, and if it was just a broker/timeout hang, mark/reset as `crash`.
5. **Read out the results**: Read only `memory/results.tsv` for the final metrics and status. Do not inspect `run.log` unless you need to diagnose a crash.
6. **If status is `keep`**: advance the branch, keeping the git commit.
7. **If status is `discard` or `crash`**: reset back to where you started before this experiment.

# Start the job

Now you are in the loop. Follow these instructions and start running experiments.


# Current memory status

unknown	1.749429	180.3	211.8	42200.5	35.82	287.3	548	33.6	8	keep	1k context, 256 batch
unknown	1.727727	180.0	211.1	42200.5	35.79	286.8	547	33.6	8	keep	1k context, shorter cooldown
unknown	1.764726	180.0	215.6	42199.3	27.62	249.6	476	33.6	8	discard	512 context, 512 batch
unknown	1.743283	180.0	211.9	42200.5	35.80	286.8	547	33.6	8	discard	1k context, matrix lr 0.05
unknown	1.708505	180.3	211.6	42200.5	35.74	286.8	547	33.6	8	keep	1k context, head lr 0.008
unknown	1.669717	180.1	211.2	42200.5	35.71	286.3	546	33.6	8	keep	1k context, head lr 0.012
unknown	1.646926	180.2	211.6	42200.5	35.69	286.3	546	33.6	8	keep	1k context, head lr 0.016
unknown	1.649636	180.1	211.9	42200.5	35.59	285.2	544	33.6	8	discard	2x residual projection lr
unknown	1.622533	180.2	212.7	42200.5	35.63	285.7	545	33.6	8	keep	1k context, head lr 0.020
unknown	1.683603	180.1	211.5	42200.5	35.71	286.3	546	33.6	8	discard	1k context, head lr 0.024
unknown	1.517630	180.2	222.4	62879.5	36.21	289.0	735	33.6	8	keep	1k context, 384 microbatch
unknown	1.324750	180.0	209.1	42080.5	35.83	284.4	1085	33.6	8	keep	1k context, 256 microbatch
unknown	1.221407	180.1	208.7	21285.5	33.48	264.8	2020	33.6	8	keep	1k context, 128 microbatch
unknown	1.230166	180.0	208.3	10888.0	27.86	219.8	3354	33.6	8	discard	1k context, 64 microbatch
unknown	1.225563	180.1	219.7	16090.8	31.05	245.3	2495	33.6	8	discard	1k context, 96 microbatch
unknown	1.226251	180.0	207.5	16090.8	31.06	245.3	2495	33.6	8	discard	1k context, 96 microbatch
unknown	1.235344	180.0	220.2	18686.7	32.14	253.9	2214	33.6	8	discard	1k context, 112 microbatch
unknown	1.217119	180.0	207.7	21285.5	33.83	267.4	2040	33.6	8	keep	1k context, 128 microbatch, 5% cooldown
unknown	1.246403	180.0	207.7	21285.5	33.15	262.0	1999	33.6	8	discard	1k context, 128 microbatch, 2% cooldown
unknown	1.223817	180.1	207.7	21285.5	33.89	267.9	2044	33.6	8	discard	1k context, 128 microbatch, 5% cooldown, final lr 0.05
unknown	1.227582	180.1	207.6	21285.5	33.79	267.1	2038	33.6	8	discard	1k context, 128 microbatch, 7% cooldown
unknown	1.241511	180.1	207.6	21285.5	33.25	262.9	2006	33.6	8	discard	1k context, 128 microbatch, head lr 0.018, 5% cooldown
unknown	1.264887	180.0	209.1	21285.5	33.12	261.8	1997	33.6	8	discard	1k context, 128 microbatch, matrix lr 0.035, 1% warmup
unknown	1.243209	180.0	214.6	16581.0	28.05	285.0	2174	27.3	6	discard	6 layers, keep 512 width
unknown	1.244401	180.1	208.0	21285.5	33.28	263.1	2007	33.6	8	discard	1k context, 128 microbatch, embedding lr 0.5
