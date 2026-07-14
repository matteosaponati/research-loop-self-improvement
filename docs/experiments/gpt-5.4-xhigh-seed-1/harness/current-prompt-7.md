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

unknown	1.067574	180.0	206.8	19117.0	35.44	252.2	1924	29.4	8	discard	10% LR floor during final warmdown
unknown	1.063527	180.0	207.2	19117.0	35.40	251.9	1922	29.4	8	keep	lower 128K Muon matrix lr to 0.020
unknown	1.061755	180.0	206.9	19117.0	35.42	252.1	1923	29.4	8	keep	lower 128K Muon matrix lr to 0.018
unknown	1.061220	180.1	208.7	19117.0	35.26	251.0	1915	29.4	8	keep	lower 128K Muon matrix lr to 0.016
unknown	1.059726	180.1	208.1	19117.0	35.36	251.7	1920	29.4	8	keep	lower 128K Muon matrix lr to 0.014
unknown	1.059623	180.1	207.8	19117.0	35.32	251.4	1918	29.4	8	keep	lower 128K Muon matrix lr to 0.012
unknown	1.060200	180.0	206.7	19117.0	35.31	251.3	1917	29.4	8	discard	lower 128K Muon matrix lr to 0.010
unknown	1.060159	180.0	207.2	19117.0	35.35	251.5	1919	29.4	8	discard	lower 128K Muon matrix lr to 0.011
unknown	1.060679	180.0	207.0	19117.0	35.37	251.7	1920	29.4	8	discard	lower embed and head AdamW lrs
unknown	1.059327	180.0	206.8	19117.0	35.44	252.2	1924	29.4	8	keep	raise 128K Muon matrix lr to 0.013
unknown	1.059123	180.1	206.9	19117.0	35.49	252.6	1927	29.4	8	keep	raise 128K Muon matrix lr to 0.0135
unknown	1.063016	180.0	211.9	19117.0	35.50	252.6	1927	29.4	8	discard	reduce Muon Newton-Schulz iterations from 5 to 4
unknown	1.063228	180.0	206.8	19117.0	35.42	252.1	1923	29.4	8	discard	shorten LR warmdown from 30% to 20%
unknown	1.058758	180.1	207.1	19117.0	35.39	251.9	1922	29.4	8	keep	raise lm-head AdamW lr from 0.002 to 0.003
unknown	1.057919	180.0	207.6	19117.0	35.29	251.1	1916	29.4	8	keep	raise lm-head AdamW lr from 0.003 to 0.004
unknown	1.058328	180.0	208.0	19117.0	35.31	251.3	1917	29.4	8	discard	raise lm-head AdamW lr from 0.004 to 0.005
unknown	1.057702	180.0	206.8	19117.0	35.35	251.5	1919	29.4	8	keep	raise lm-head AdamW lr from 0.004 to 0.0045
unknown	1.059550	180.1	218.0	14424.3	34.45	244.9	2491	29.4	8	discard	smaller 98K tokens per optimizer update
unknown	1.058231	180.0	207.9	19117.0	35.33	251.4	1918	29.4	8	discard	raise token embedding AdamW lr from 0.30 to 0.35
unknown	1.057613	180.0	207.2	19117.0	35.41	251.9	1922	29.4	8	keep	lower matrix Muon lr from 0.0135 to 0.01325
unknown	1.057620	180.0	207.5	19117.0	35.39	251.8	1921	29.4	8	discard	lower matrix Muon lr from 0.01325 to 0.0131
unknown	1.057559	180.1	206.8	19117.0	35.45	252.3	1925	29.4	8	keep	lower matrix Muon lr from 0.01325 to 0.0132
unknown	1.057821	180.0	207.7	19117.0	35.33	251.4	1918	29.4	8	discard	lower lm-head AdamW lr from 0.0045 to 0.0044
unknown	1.057984	180.0	208.4	19117.0	35.14	250.1	1908	29.4	8	discard	lower matrix Muon weight decay from 0.20 to 0.18
unknown	1.058133	180.0	208.6	19117.0	35.10	249.8	1906	29.4	8	discard	raise lm-head AdamW lr from 0.0045 to 0.0046
