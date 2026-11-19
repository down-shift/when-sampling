# Two-flip stopping pilot

## Design

Under either hypothesis, both flips are generated independently with the same probability of heads. The prior is 1/2. The observer sees flip 1, the rule menu and active rule, and STOP. The active rule is fixed before either flip and independently of the hypothesis. There is one trial and STOP reports the rule's output.

Each case yields three decision/control pairs. One active rule repeats the visible outcome, and the other two reveal heads or tails on flip 2. The repeated-evidence control uses a deterministic copy of the visible flip 1 result. The program never reads flip 2. Both formats state explicitly what the observer knows before and after receiving the extra information. All prompts ask for the direction of the posterior change relative to flip 1 alone. The three contrasts are constructed conditional on STOP being possible. The pilot makes no estimate of accuracy under naturally occurring STOP frequencies.

Use eight development cases and 40 evaluation cases, with one fresh conversation per request and no planned repeats. Each split balances visible outcome crossed with which hypothesis favors heads. Rule IDs and menu positions are counterbalanced for each of the four predicates and for the active restatement. Exact enumeration checks the STOP event, the control event and their implied posterior. Swapping A and B must reverse UP and DOWN and preserve SAME. Split construction groups label swaps, heads/tails mirrors and presentation edits. It also groups cases that vary only in the first flip. The local audit checks exact decision and control prompt overlap against both splits and the worked example. Both revised splits also exclude every case family from the first pilot.

The worked example uses A = 3/4 and B = 1/4 for heads, shows heads on flip 1 and activates the rule that stops on heads on flip 1. The answer is SAME. The example and all variants of its probability pair are excluded. The example is available via the `example` command.

## Proposed interpretation criteria for review

- Treat at least 90% control accuracy in each class and at most 5% invalid responses in each format as a prerequisite for interpreting a gap as difficulty with the STOP prompts. Include every planned request in accuracy and score invalid final responses as incorrect.
- Look for at least 80% decision accuracy in **each** class as preliminary evidence that the checkpoint can distinguish the three cases in this menu. The always-SAME baseline scores 33.3% overall and 100% on SAME, so aggregate accuracy alone is insufficient. The flip 1 vs prior baseline predicts the direction of the update from the prior after flip 1 and ignores the additional information. It tests the alternative comparison observed in the first pilot.
- Treat a positive control-minus-decision gap with a 95% interval wholly above zero as preliminary evidence of a cost associated with the decision format, conditional on the control and validity criteria. Use the overall gap as the primary contrast. Inspect class gaps and confusion matrices for failure patterns. UP/DOWN answers on SAME are consistent with treating a restatement as new evidence. SAME answers on UP/DOWN are consistent with missing a reveal. An interval overlapping zero leaves the size of the gap unresolved.
- The decision format adds a menu, rule lookup and more text. A gap cannot isolate inference about stopping from those demands. The task can also be solved by comparing the head probabilities and recognizing which flip the rule references. Accuracy cannot establish a general Bayesian reasoning mechanism or generalize beyond this checkpoint and prompt family.

Resample 40 whole base cases with replacement per bootstrap draw, preserving all six outcomes per case. Report percentile intervals with 5,000 draws. Per-class intervals are descriptive. These intervals cover variation across constructed cases at fixed model settings.

## Local commands

From the repository root:

```sh
uv run --no-sync python -m sampling.stopping verify
uv run --no-sync python -m sampling.stopping run
uv run --no-sync python -m sampling.stopping run --split evaluation --config config.stopping.json --live --dry-run
```

The mock run writes the existing runner's artifacts and the paired report under `artifacts/stopping-local/mock-revised`. The dry run performs the split audit, prints request counts and hashes, and makes no HTTP requests. Keep the generator and rendered evaluation material local before collection. Outputs are ignored by Git.

Live evaluation requires explicit approval of this plan. After review, use the server command recorded in `config.stopping.json` on the GPU host, and record its actual vLLM, PyTorch and CUDA versions alongside the run. Check formatting and output budget on development cases before authorizing evaluation. For collection, use the dry-run command without `--dry-run` and supply `--reviewed-plan-hash` with the printed plan hash and a fresh `--output artifacts/stopping-local/live-evaluation-thinking`. Use a distinct output directory for any live development run.

## Revised development run

The first live batch used a 2,048-token completion cap. Reanalyze its saved responses with `uv run --no-sync python -m sampling.stopping reanalyze --output artifacts/stopping-local/mock`. This writes `analysis.corrected.json` and `report.corrected.md` beside the original files. The parser accepts a completed leading `<think>…</think>` block followed by valid final JSON and still counts truncations as invalid. The original collection remains subject to the validity criterion above.

The revised batch with thinking disabled returned 48 valid responses. Explicit controls scored 1/8 on UP, 8/8 on DOWN, and 0/8 on SAME. Every decision answer was DOWN.

Run one more development batch with the same 48 prompts, pinned checkpoint, and categorical JSON schema. Enable thinking and allow 8,192 completion tokens within a 9,216-token server context. Restart the GPU server with the command recorded in the config, then run:

```sh
uv run --no-sync python -m sampling.stopping run --split development --config config.stopping.json --live --output artifacts/stopping-local/live-development-thinking
```

The live evaluation command requires a matching live development run with at most one invalid response in each format and all eight controls correct in each class. If development passes, review this plan and use the hash printed by the evaluation dry run. If development fails, stop tuning this checkpoint for the pilot and test a stronger checkpoint on development only.

## Qwen3-8B development follow-up

The thinking-mode 4B run passed the validity threshold but scored 0/8 on the SAME controls. Test the same 48 development requests with the official Qwen3-8B checkpoint in bfloat16. The configuration preserves thinking, the JSON schema, and the 8,192-token completion limit. Four concurrent requests let vLLM batch decoding. Compare elapsed time from the runner logs and keep the control and validity thresholds above.

Start the server using the command in `config.stopping.8b.json`, then run:

```sh
uv run --no-sync python -m sampling.stopping run --split development --config config.stopping.8b.json --live --output artifacts/stopping-local/live-development-8b
```

This configuration budgets 48 requests and is development only. Review the result before selecting a configuration for held-out evaluation.
