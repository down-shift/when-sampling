# When Should the Sampling Policy Matter?

A compact diagnostic of reported posterior agreement under fixed sampling (F), deterministic stopping (S), and hypothesis-dependent forwarding (R). See `protocol.md` for the draft research protocol. No model evidence has been collected. The checked-in mock run contains synthetic oracle answers.

Python 3.11+; production code uses only the standard library. Use uv. The following commands avoid dependency downloads and work in a fresh checkout:

```sh
uv run --offline --no-project python -m unittest discover -s tests -p 'test_pipeline.py' -v
uv run --offline --no-project python -m sampling verify
uv run --offline --no-project python -m sampling preview
uv run --offline --no-project python -m sampling run --output artifacts/my-mock
uv run --offline --no-project python -m sampling run --output artifacts/my-mock --resume
uv run --offline --no-project python -m sampling analyze --output artifacts/my-mock
```

Generate a new reproducible dataset with `python -m sampling generate --dataset artifacts/new-dataset.json`. Defaults: 16 development worlds, 64 evaluation worlds, seeds 1729 and 2718; sizes/seeds configurable through CLI flags. Existing datasets are never overwritten. `--dataset` selects the same file for subsequent commands. `--help` lists all options. The historical pytest tests in `tests/test_oracle.py` are also covered by the dependency-free unittest suite.

Each world has 18 base requests: three conditions, two paraphrases, three task types. The first two worlds additionally receive one repeat of each primary request (12 extra requests). Defaults: development 300, evaluation 1164, combined 1464 logical requests. With retry limit two, maximum HTTP attempts are three times these counts. A two-world development pilot has 48 requests. Each request has fresh conversation state. Repeat selection is prespecified by world index, before request shuffling. Means use the original requests; repeat ranges estimate variability within each world. No power claim is attached to sample sizes.

The runner defaults to mock. To prepare an authorized live pilot, copy `config.live.example.json` to `config.live.json`, fill in endpoint and model identifier, and set the named key environment variable without committing it. The endpoint is the complete chat-completions URL. Do not add secrets to configuration files. No model names or pricing are assumed.

```sh
uv run --offline --no-project python -m sampling run --config config.live.json --world-limit 2 --output artifacts/pilot --live --dry-run
# Execute only after authorizing the pilot:
uv run --offline --no-project python -m sampling run --config config.live.json --world-limit 2 --output artifacts/pilot --live
uv run --offline --no-project python -m sampling analyze --world-limit 2 --output artifacts/pilot
```

Use the same selection, repeat and order flags when analyzing or resuming. `--resume` skips all completed logical requests, including failures. It refuses configuration, dataset, protocol, source or request changes. Retry bounds apply per process; an interrupted in-flight request may have reached the server without a saved response, so crash recovery cannot guarantee exactly-once billing. Completed responses are flushed and fsynced individually. Do not run two processes against one output directory. A corrupt partial JSONL tail causes an explicit failure and requires inspection rather than silent recovery.

Model-visible requests are built from an explicit payload allowlist. Oracle answers are saved separately in `answers.private.json` and are never serialized into HTTP requests. Likelihood-table inputs intentionally contain the observation likelihoods. Manifest, request hashes, dataset/config/source/protocol hashes, timestamps, seeds, raw responses, parsed responses, attempts and settings provide provenance. Git revision is null outside a git repository. HTTP error codes are retained; error bodies and headers are discarded to avoid credential exposure. Text refusals without a structured refusal signal are classified by their JSON validity; no heuristic extracts probabilities from prose.

Analysis reports per-condition posterior MAE, signed and absolute S-minus-F differences, R-minus-F effect errors and direction correctness, likelihood diagnostics, repeated-call ranges and all status denominators. Numeric metrics require both paraphrases; missing answers remain in the status counts. Bootstrap samples whole worlds with one common resampling scheme per metric; intervals describe the selected collection of worlds, not a population guarantee. Primary thresholds and the model/decoding choice remain investigator decisions before held-out evaluation. The protocol is a draft, not frozen.

No local GPU is needed for mock checks or HTTP inference. A remote GPU would only host a separately chosen model server. Model selection, server setup and large evaluation require a separate decision.

## Ubuntu GPU: vLLM

This uses the same serving approach documented in [which-program](https://github.com/down-shift/which-program#run-a-local-gpu-model): a separate vLLM environment and Qwen3-4B in BF16. It reuses the existing HTTP runner. There is no GPU Python dependency in this project, automatic installation, server supervisor, or automatic evaluation. The reference's exact launcher/dependency pins could not be fetched; this is the same serving approach, not a copy of its launcher.

If vLLM is already installed for `which-program`, reuse it:

```sh
export VLLM_BIN=/absolute/path/to/which-program/.venv-vllm/bin/vllm
bash scripts/serve-local.sh
```

Otherwise install a **chosen, pinned version** in a separate environment on Ubuntu. Set `VLLM_VERSION` to your validated version; the guard prevents an accidental unpinned install. Consult the [vLLM GPU installation instructions](https://docs.vllm.ai/en/stable/getting_started/installation/gpu/) for CUDA/driver requirements.

```sh
uv venv --python 3.11 .venv-vllm
uv pip install --python .venv-vllm/bin/python "vllm==${VLLM_VERSION:?Set your validated vLLM version}"
bash scripts/serve-local.sh
```

The foreground server binds only to localhost, uses BF16, a 4096-token context, two concurrent sequences and an 85% GPU-memory budget. Stop it with Ctrl-C. These are conservative starting settings, not a GPU-tested memory guarantee. You can pass additional vLLM flags, e.g. `bash scripts/serve-local.sh --revision MODEL_COMMIT --tokenizer-revision MODEL_COMMIT`. Record the resolved model commit, vLLM/CUDA versions and server command with pilot artifacts before comparing runs. `--generation-config vllm` avoids checkpoint generation defaults silently changing sampling settings.

In a second terminal on that same Ubuntu machine:

```sh
uv run --offline --no-project python -m sampling run --config config.local.json --world-limit 2 --output artifacts/local-pilot-v3 --live --dry-run
# After authorizing the 48-request development pilot:
uv run --offline --no-project python -m sampling run --config config.local.json --world-limit 2 --output artifacts/local-pilot-v3 --live
uv run --offline --no-project python -m sampling analyze --world-limit 2 --output artifacts/local-pilot-v3
```

The local config caps collection at 48 requests and needs no API key. Add `--resume` to the identical run command to skip completed requests. Qwen's [documented non-thinking mode](https://huggingface.co/Qwen/Qwen3-4B#switching-between-thinking-and-non-thinking-mode) is set explicitly through `chat_template_kwargs`; this is a pilot configuration to finalize before held-out evaluation. The local pilot allows 512 output tokens and uses vLLM [structured outputs](https://docs.vllm.ai/en/v0.20.1/features/structured_outputs/) to constrain each answer to its task-specific JSON schema. The parser independently checks that each probability is in [0, 1]. Constrained decoding changes the measurement setup. Check that both primary paired comparisons cover both development worlds before moving to held-out evaluation. The parser accepts bare JSON or a single Markdown code fence containing the JSON object. Prose and truncated responses still count as failures. After changing the configuration or parser, use a fresh output directory for collection. To use an existing different model, set `SAMPLING_MODEL` for the server and change `model` in a copied config to match. Keep model selection separate from evaluation results.
