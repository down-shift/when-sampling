#!/usr/bin/env bash
# Run on the Ubuntu GPU host, from the repository root.
serve_sampling_model() {
    local sampling_vllm="${VLLM_BIN:-.venv-vllm/bin/vllm}"
    local sampling_model="${SAMPLING_MODEL:-Qwen/Qwen3-4B}"
    if [ ! -x "$sampling_vllm" ]; then
        echo 'Set VLLM_BIN to your existing vLLM executable (see README.md).' >&2
        return 1
    fi
    "$sampling_vllm" serve "$sampling_model" \
        --host 127.0.0.1 --port 8000 \
        --dtype "${SAMPLING_DTYPE:-bfloat16}" --max-model-len "${SAMPLING_MAX_MODEL_LEN:-4096}" \
        --gpu-memory-utilization 0.85 --max-num-seqs "${SAMPLING_MAX_NUM_SEQS:-2}" \
        --generation-config vllm "$@"
}
serve_sampling_model "$@"
