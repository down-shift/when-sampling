import json
import re
from pathlib import Path

from .project import digest


THRESHOLDS = {
    'primary_posterior_mae:F': 'max',
    'invariance_absolute': 'max',
    'sensitivity_absolute_error': 'max',
    'sensitivity_direction': 'min',
}


def evaluation_lock(plan, config, context, requests):
    revision = plan.get('model_revision') if isinstance(plan, dict) else None
    if not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('model_revision must be a full lowercase commit hash')
    for field in ('server_command', 'vllm_version', 'torch_version', 'cuda_version'):
        if not isinstance(plan.get(field), str) or not plan[field].strip():
            raise ValueError(f'{field} is required')
    thresholds = plan.get('thresholds')
    if not isinstance(thresholds, dict) or thresholds.keys() != THRESHOLDS.keys():
        raise ValueError('thresholds must specify: ' + ', '.join(THRESHOLDS))
    for value in thresholds.values():
        if type(value) not in (int, float) or not 0 <= value <= 1:
            raise ValueError('thresholds must be numbers in [0, 1]')
    if config.get('adapter') != 'http' or config['max_requests'] < len(requests):
        raise ValueError('evaluation requires an HTTP config with enough request budget')
    return dict(
        plan=plan, config_hash=digest(config), requests_hash=digest(requests),
        context=context, protocol_hash=digest(Path('protocol.md').read_text()),
        source_hash=digest({str(p): p.read_text() for p in sorted(Path('sampling').glob('*.py'))}),
    )


def threshold_results(metrics, plan):
    results = {}
    for name, direction in THRESHOLDS.items():
        metric = metrics.get(name)
        threshold = plan['thresholds'][name]
        passed = None
        if metric and metric['worlds'] == metric['total_worlds']:
            mean = metric['mean']
            passed = mean <= threshold if direction == 'max' else mean >= threshold
        results[name] = dict(direction=direction, threshold=threshold, passed=passed)
    return results
