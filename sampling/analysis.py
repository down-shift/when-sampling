import collections
import json
import random
import statistics
from fractions import Fraction
from pathlib import Path
from .project import save, digest
from .evaluation import threshold_results


def analyze(directory, answers, seed=4242, bootstrap=2000):
    out = Path(directory)
    reqs = json.loads((out/'requests.json').read_text())
    rows = {r['id']:r for r in map(json.loads,(out/'responses.jsonl').read_text().splitlines())}
    buckets = collections.defaultdict(list)
    failures = collections.defaultdict(collections.Counter)
    repeats = collections.defaultdict(list)
    for req in reqs:
        row = rows.get(req['id'],{'status':'missing'})
        group = req['kind']+':'+req['condition']
        failures[group][row['status']] += 1
        if row['status'] != 'ok':
            continue
        val = row['parsed']
        target = answers[req['id']]
        w,c,k = req['world'],req['condition'],req['kind']
        if k == 'primary':
            repeats[w,c,req['variant']].append(val['posterior_h_a'])
        # Repetitions estimate variability, not additional primary observations.
        if req['repeat']:
            continue
        if k == 'extraction':
            error = max(abs(val[key]-float(Fraction(target[key]))) for key in val)
            buckets[w,k,c].append(error)
        else:
            buckets[w,k,c].append((val['posterior_h_a'],float(Fraction(target['posterior_h_a']))))
    metrics = collections.defaultdict(dict)
    means = {}
    for (w,k,c),vals in buckets.items():
        # Require both paraphrases for the world-level estimate.
        if len(vals)!=2:
            continue
        if k == 'extraction':
            metrics[f'extraction_max_abs_error:{c}'][w]=statistics.mean(vals)
            metrics[f'extraction_correct_1e-6:{c}'][w]=float(all(v<=1e-6 for v in vals))
        else:
            means[w,k,c] = statistics.mean(v[0] for v in vals)
            metrics[f'{k}_posterior_mae:{c}'][w]=statistics.mean(abs(v[0]-v[1]) for v in vals)
    worlds = sorted({r['world'] for r in reqs})
    targets = {(r['world'],r['condition']):float(Fraction(answers[r['id']]['posterior_h_a'])) for r in reqs}
    for w in worlds:
        if all((w,'primary',c) in means for c in ('F','S')):
            d=means[w,'primary','S']-means[w,'primary','F']
            metrics['invariance_signed'][w]=d
            metrics['invariance_absolute'][w]=abs(d)
        if all((w,'primary',c) in means for c in ('F','R')):
            pred=means[w,'primary','R']-means[w,'primary','F']
            effect=targets[w,'R']-targets[w,'F']
            metrics['sensitivity_signed_error'][w]=pred-effect
            metrics['sensitivity_absolute_error'][w]=abs(pred-effect)
            if effect:
                metrics['sensitivity_direction'][w]=float(pred*effect>0)
    for w in worlds:
        ranges=[max(v)-min(v) for (ww,c,t),v in repeats.items() if ww==w and len(v)>1]
        if ranges:
            metrics['repeated_call_absolute_difference'][w]=statistics.mean(ranges)
    rng=random.Random(seed)
    samples=[[rng.choice(worlds) for _ in worlds] for _ in range(bootstrap)]
    summary={}
    for name,values in metrics.items():
        estimates=[statistics.mean(values[w] for w in sample if w in values) for sample in samples if any(w in values for w in sample)]
        estimates.sort()
        summary[name]=dict(mean=statistics.mean(values.values()),worlds=len(values),total_worlds=len(worlds),ci95=[estimates[int(.025*(len(estimates)-1))],estimates[int(.975*(len(estimates)-1))]])
    variability = {}
    for w in worlds:
        ranges = [max(v)-min(v) for (ww,c,t),v in repeats.items() if ww == w and len(v) == 2]
        if ranges:
            variability[w] = statistics.mean(ranges)
    manifest = json.loads((out/'manifest.json').read_text())
    report=dict(synthetic=manifest['synthetic'],settings=dict(seed=seed,bootstrap=bootstrap,extraction_tolerance=1e-6,paraphrases_required=2),repeat_world_ranges=variability,answers_hash=digest(answers),metrics=summary,status_counts={k:dict(v,total=sum(v.values())) for k,v in failures.items()},world_values=metrics)
    lock = manifest['identity'].get('evaluation_lock')
    if lock:
        report['threshold_results'] = threshold_results(summary, lock['plan'])
    save(out/'analysis.json',report)
    lines=['# '+('SYNTHETIC implementation check' if report['synthetic'] else 'Evaluation report'),'','Mock outputs are not research findings.' if report['synthetic'] else 'Agreement with stipulated posteriors; no empirical calibration claim.','','Intervals resample worlds jointly; missing/invalid answers are excluded from numeric metrics and counted below. Each metric requires both paraphrases. Repeated calls are dependent.','']
    stopping_pairs = len(metrics.get('invariance_signed', {}))
    forwarding_pairs = len(metrics.get('sensitivity_signed_error', {}))
    lines.extend([
        f'Primary comparisons with both paraphrases: stopping vs fixed {stopping_pairs}/{len(worlds)} worlds, '
        f'forwarding vs fixed {forwarding_pairs}/{len(worlds)} worlds.',
        '',
    ])
    for k,v in summary.items():
        lines.append(f"- {k}: {v['mean']:.6g}, 95% bootstrap interval {v['ci95']}, worlds {v['worlds']}/{v['total_worlds']}")
    if lock:
        lines.extend(['', 'Frozen thresholds (point estimates, full world coverage required)', ''])
        for name, result in report['threshold_results'].items():
            outcome = {True: 'pass', False: 'fail', None: 'insufficient coverage'}[result['passed']]
            lines.append(f"- {name} ({result['direction']} {result['threshold']}): {outcome}")
    lines += ['', 'Repeated-call mean ranges by world: '+json.dumps(variability), '', 'Statuses and denominators:', '', '```json',json.dumps(report['status_counts'],indent=2),'```']
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    return report
