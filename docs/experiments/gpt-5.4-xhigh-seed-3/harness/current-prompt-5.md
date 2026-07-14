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

commit	val_bpb	training_seconds	total_seconds	peak_vram_mb	mfu_percent	total_tokens_M	num_steps	num_params_M	depth	status	description
unknown	1.902140	180.3	214.1	42204.0	38.40	252.7	482	33.6	8	keep	baseline
unknown	1.467173	180.2	209.1	42084.0	38.10	248.0	946	33.6	8	keep	halve total batch to double update count
unknown	1.496917	180.1	209.1	42084.0	38.03	247.5	944	33.6	8	discard	delay LR decay and keep a 10% LR floor
unknown	1.269935	180.1	207.3	21289.0	37.35	241.7	1844	33.6	8	keep	halve batch again to 131k total tokens
unknown	1.228778	180.0	207.4	10891.5	34.69	223.9	3416	33.6	8	keep	halve batch again to 65k total tokens
unknown	1.244813	180.0	207.9	5692.8	26.57	171.3	5228	33.6	8	discard	halve batch again to 33k total tokens
unknown	1.246786	180.0	222.3	13446.7	38.97	177.2	2704	49.8	8	discard	widen model to 640d at 65k batch
unknown	1.234556	180.0	219.1	8292.2	30.30	195.5	3977	33.6	8	discard	49k total batch with 24 seq/device
unknown	1.239556	180.0	219.8	10912.0	34.38	221.9	3386	33.6	8	discard	8 heads at 512d instead of 4x128
unknown	1.253385	180.0	218.5	9654.7	28.94	229.1	3496	26.6	8	discard	shrink to 448d with 7 heads
unknown	1.234815	180.1	206.7	10891.5	34.29	221.4	3378	33.6	8	discard	halve weight decay at 65k batch
unknown	1.232878	180.0	218.7	10241.7	33.36	215.3	3504	33.6	8	discard	61k total batch with 30 seq/device
unknown	1.240883	180.0	207.1	10891.5	34.14	220.3	3362	33.6	8	discard	shorten LR cooldown to last 30% at 65k batch
unknown	1.222383	180.0	206.6	10891.5	34.98	225.7	3444	33.6	8	keep	reduce all AdamW LRs 10% at 65k batch
unknown	1.223034	180.0	206.9	10891.5	34.60	223.3	3408	33.6	8	discard	reduce all AdamW LRs 20% at 65k batch
unknown	1.235204	180.0	206.9	10891.5	33.85	218.5	3334	33.6	8	discard	reduce all AdamW LRs 15% at 65k batch
unknown	1.215541	180.0	206.6	10891.5	34.50	222.6	3397	33.6	8	keep	start LR cooldown earlier over final 60% at 65k batch
unknown	1.216856	180.0	206.6	10891.5	34.73	224.1	3420	33.6	8	discard	start LR cooldown earlier over final 65% at 65k batch
unknown	1.214849	180.0	206.6	10891.5	34.23	220.9	3371	33.6	8	keep	restore embedding and lm head LRs with lower matrix LR
unknown	1.208927	180.0	207.0	10891.5	34.47	222.4	3394	33.6	8	keep	lower matrix LR further with earlier cooldown
unknown	1.211533	180.0	207.1	10891.5	34.41	222.1	3389	33.6	8	discard	lower matrix LR again with earlier cooldown
