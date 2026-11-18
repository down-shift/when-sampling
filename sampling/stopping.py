"""Two-flip stopping pilot. Cases and answer keys are generated locally."""
import argparse
from collections import Counter
from fractions import Fraction as Q
from itertools import combinations, permutations, product
import json
from pathlib import Path
import random

from .oracle import likelihood, posterior
from .project import digest, save
from .runner import DIRECTIONS, run

RULES = ((0, 'H'), (0, 'T'), (1, 'H'), (1, 'T'))
OUTCOME = {'H': 'heads', 'T': 'tails'}
KINDS = ('decision', 'control')
SEEDS = dict(development=8191, evaluation=131071, order=524287, bootstrap=4242)
WORKED = dict(pa='3/4', pb='1/4', visible='H', ids='KLMN', order=[0, 1, 2, 3])
LOCAL = Path('artifacts/stopping-local')
PLAN = Path('stopping-plan.md')
LIVE_CONFIG = Path('config.stopping.json')


def canonical(case):
    # Group label swaps, mirrors and changes to presentation or the visible flip.
    a, b = sorted((Q(case['pa']), Q(case['pb'])))
    return min((a, b), (1 - b, 1 - a))


def balanced_placements(rng, orientations, values):
    base = rng.sample(list(values), 4)
    restate = [int(visible == 'T') for visible, _ in orientations]
    schedules = [
        shifts for shifts in permutations(range(4))
        if len({rule ^ shift for rule, shift in zip(restate, shifts)}) == 4
    ]
    return [[base[rule ^ shift] for rule in range(4)] for shift in rng.choice(schedules)]


def generate():
    seen = {canonical(WORKED)}
    grid = sorted({Q(n, d) for d in (10, 12, 16, 20) for n in range(1, d)
                   if Q(1, 10) <= Q(n, d) <= Q(9, 10)})
    splits = {}
    for split, size in (('development', 8), ('evaluation', 40)):
        rng = random.Random(SEEDS[split])
        pairs = list(combinations(grid, 2))
        rng.shuffle(pairs)
        cases = []
        for a, b in pairs:
            key = canonical(dict(pa=a, pb=b))
            if key in seen:
                continue
            seen.add(key)
            if len(cases) % 4 == 0:
                orientations = list(product('HT', (False, True)))
                rng.shuffle(orientations)
                ids = balanced_placements(rng, orientations, 'KLMN')
                positions = balanced_placements(rng, orientations, range(4))
            slot = len(cases) % 4
            visible, favors_a = orientations[slot]
            pa, pb = (b, a) if favors_a else (a, b)
            if rng.choice((False, True)):
                pa, pb = 1 - pb, 1 - pa
            cases.append(dict(id=f'{split}-{len(cases):03d}', pa=str(pa), pb=str(pb),
                              visible=visible, ids=''.join(ids[slot]),
                              order=sorted(range(4), key=positions[slot].__getitem__)))
            if len(cases) == size:
                break
        if len(cases) != size:
            raise ValueError('insufficient distinct probability pairs')
        splits[split] = cases
    return splits


def direction(before, after):
    return 'UP' if after > before else 'DOWN' if after < before else 'SAME'


def implication(rule):
    return None if RULES[rule][0] == 0 else RULES[rule][1]


def oracle(case, rule):
    """Enumerate all four outcomes under each hypothesis and verify event equality."""
    index, target = RULES[rule]
    before = {seq for seq in product('HT', repeat=2) if seq[0] == case['visible']}
    stopped = {seq for seq in before if seq[index] == target}
    if not stopped:
        raise ValueError('STOP is impossible for this visible outcome')
    hidden = implication(rule)
    explicit = {seq for seq in before if hidden is None or seq[1] == hidden}
    if stopped != explicit:
        raise ValueError('STOP and explicit evidence admit different outcomes')
    pa, pb = Q(case['pa']), Q(case['pb'])
    if not (0 < pa < 1 and 0 < pb < 1 and pa != pb):
        raise ValueError('invalid hypothesis probabilities')
    weights = []
    for p in (pa, pb):
        outcome = {'H': p, 'T': 1 - p}
        weights.append({(first, second): outcome[first] * outcome[second]
                        for first, second in product('HT', repeat=2)})
    base, stop, control = (posterior(Q(1, 2), *(sum(w[s] for s in event) for w in weights))
                           for event in (before, stopped, explicit))
    record = case['visible'] + (hidden or '')
    analytic = posterior(Q(1, 2), likelihood(record, pa), likelihood(record, pb))
    if stop != control or stop != analytic:
        raise ValueError('enumeration disagrees with explicit evidence likelihood')
    return direction(base, stop)


def render(case, rule, kind):
    visible = OUTCOME[case['visible']]
    prefix = (
        f'Hypotheses A and B are equally likely before any flips. Two flips are '
        f'generated independently conditional on the hypothesis. On each flip, '
        f'the probability of heads is {case["pa"]} under A and {case["pb"]} under B.\n'
        f'You see that flip 1 was {visible}.\n'
    )
    if kind == 'decision':
        menu = '\n'.join(
            f'{case["ids"][i]}: STOP if flip {RULES[i][0] + 1} is {OUTCOME[RULES[i][1]]}; '
            'otherwise CONTINUE.' for i in case['order']
        )
        evidence = (
            'Both flips have already been generated. Flip 2 is hidden from you. '
            'Before the flips, one rule was fixed independently of the hypothesis and both outcomes.\n'
            f'{menu}\nThe active rule is {case["ids"][rule]}. The observed decision is STOP.'
        )
    else:
        hidden = implication(rule)
        evidence = (f'You are told that flip 2 was {OUTCOME[hidden]}.' if hidden else
                    f'You are told again that flip 1 was {visible}. Flip 2 remains unobserved.')
    return (prefix + evidence + '\nRelative to seeing flip 1 alone, does the probability '
            'of hypothesis A go UP, go DOWN, or stay the SAME? '
            'Return only JSON with the key "direction" and one of "UP", "DOWN", or "SAME".')


def build(cases):
    requests, answers = [], {}
    for case in cases:
        for rule in (int(case['visible'] == 'T'), 2, 3):
            answer = oracle(case, rule)
            pair = f'{case["id"]}:{rule}'
            for kind in KINDS:
                prompt = render(case, rule, kind)
                rid = f'{pair}:{kind}'
                requests.append(dict(id=rid, case=case['id'], pair=pair, kind=kind,
                                     prompt=prompt, prompt_hash=digest(prompt)))
                answers[rid] = dict(direction=answer)
    random.Random(SEEDS['order']).shuffle(requests)
    return requests, answers


def verify_placements(rules, split):
    ids = Counter(case['ids'][rule] for case, rule in rules)
    positions = Counter(case['order'].index(rule) for case, rule in rules)
    expected = [len(rules) // 4] * 4
    if sorted(ids.values()) != expected or sorted(positions.values()) != expected:
        raise ValueError(f'unbalanced rule placement in {split}')


def verify(splits):
    worked = dict(WORKED, id='worked')
    example_requests, _ = build([worked])
    seen_prompts = {r['prompt'] for r in example_requests}
    seen_cases = {canonical(worked)}
    reversed_label = dict(UP='DOWN', DOWN='UP', SAME='SAME')
    for split, cases in splits.items():
        n = len(cases)
        orientations = Counter((c['visible'], Q(c['pa']) > Q(c['pb'])) for c in cases)
        if sorted(orientations.values()) != [n // 4] * 4:
            raise ValueError(f'unbalanced orientations in {split}')
        for rules in ([(c, rule) for c in cases] for rule in range(4)):
            verify_placements(rules, split)
        verify_placements([(c, int(c['visible'] == 'T')) for c in cases], split)
        for case in cases:
            key = canonical(case)
            if key in seen_cases:
                raise ValueError('duplicate case family or worked-example equivalent')
            seen_cases.add(key)
            swapped = dict(case, pa=case['pb'], pb=case['pa'])
            valid = [int(case['visible'] == 'T'), 2, 3]
            labels = [oracle(case, rule) for rule in valid]
            if set(labels) != set(DIRECTIONS) or labels[0] != 'SAME':
                raise ValueError('incorrect class design')
            for rule, label in zip(valid, labels):
                if oracle(swapped, rule) != reversed_label[label]:
                    raise ValueError('label reversal failed')
        requests, _ = build(cases)
        for request in requests:
            if request['prompt'] in seen_prompts:
                raise ValueError('duplicate exact rendered prompt')
            seen_prompts.add(request['prompt'])
    return {split: len(cases) * 6 for split, cases in splits.items()}


def analyze(directory, requests, answers, bootstrap=5000):
    rows = {}
    for line in (directory / 'responses.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['id'] in rows:
            raise ValueError('duplicate response')
        rows[row['id']] = row
    if set(rows) != set(answers):
        raise ValueError('response IDs do not match planned requests')
    predictions = (*DIRECTIONS, 'INVALID')
    matrix = {kind: {label: dict.fromkeys(predictions, 0) for label in DIRECTIONS}
              for kind in KINDS}
    statuses = Counter()
    paired = {}
    for request in requests:
        rid = request['id']
        row = rows[rid]
        label = answers[rid]['direction']
        predicted = row['parsed']['direction'] if row['status'] == 'ok' else 'INVALID'
        kind = request['kind']
        matrix[kind][label][predicted] += 1
        statuses[row['status']] += 1
        paired.setdefault(request['case'], {}).setdefault(label, {})[kind] = int(label == predicted)

    accuracy = {kind: {label: matrix[kind][label][label] / sum(matrix[kind][label].values())
                       for label in DIRECTIONS} for kind in KINDS}
    differences = {
        label: [case[label]['control'] - case[label]['decision'] for case in paired.values()]
        for label in DIRECTIONS
    }
    differences['overall'] = [sum(case) / 3 for case in zip(*(differences[x] for x in DIRECTIONS))]
    rng = random.Random(SEEDS['bootstrap'])
    n = len(paired)
    draws = [rng.choices(range(n), k=n) for _ in range(bootstrap)]
    gaps = {}
    for label, values in differences.items():
        means = sorted(sum(values[i] for i in draw) / n for draw in draws)
        gaps[label] = dict(estimate=sum(values) / n,
                           ci95=[means[int((bootstrap - 1) * q)] for q in (.025, .975)])

    save(directory / 'analysis.json', dict(
        accuracy=accuracy, confusion=matrix, response_status=dict(statuses),
        baseline=dict(overall=1 / 3, by_class=dict(UP=0, DOWN=0, SAME=1)),
        control_minus_decision=gaps, base_cases=n, bootstrap_draws=bootstrap,
        bootstrap_seed=SEEDS['bootstrap'],
    ))
    manifest = json.loads((directory / 'manifest.json').read_text())
    report = ['# Stopping pilot', '', f'{n} base cases, {len(requests)} requests.', '']
    if manifest['synthetic']:
        report += ['Synthetic oracle mock. These results check the pipeline only.', '']
    report += ['| Correct label | Decision accuracy | Control accuracy | Always-SAME |',
               '| --- | ---: | ---: | ---: |']
    for label in DIRECTIONS:
        report.append(f'| {label} | {accuracy["decision"][label]:.1%} | '
                      f'{accuracy["control"][label]:.1%} | {int(label == "SAME"):.1%} |')
    report += ['', 'Always-SAME overall accuracy is 33.3%.', '',
               'Control minus decision accuracy with 95% percentile intervals resampled over base cases.', '',
               '| Label | Gap | 95% interval |', '| --- | ---: | ---: |']
    for label, gap in gaps.items():
        low, high = gap['ci95']
        report.append(f'| {label} | {gap["estimate"]:+.1%} | [{low:+.1%}, {high:+.1%}] |')
    for kind in KINDS:
        report += ['', f'## {kind.title()} confusion matrix', '',
                   '| Correct label | UP | DOWN | SAME | INVALID |', '| --- | ---: | ---: | ---: | ---: |']
        for label, counts in matrix[kind].items():
            report.append(f'| {label} | ' + ' | '.join(str(counts[p]) for p in predictions) + ' |')
    (directory / 'report.md').write_text('\n'.join(report) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('verify', 'example', 'run'))
    parser.add_argument('--split', choices=('development', 'evaluation'), default='evaluation')
    parser.add_argument('--config', type=Path, default=Path('config.mock.json'))
    parser.add_argument('--output', type=Path, default=LOCAL / 'mock')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--reviewed-plan-hash')
    args = parser.parse_args()
    if args.command == 'example':
        print(render(WORKED, 0, 'decision'))
        print('\nOracle:', oracle(WORKED, 0))
        print('\n' + render(WORKED, 0, 'control'))
        return
    splits = generate()
    counts = verify(splits)
    if args.command == 'verify':
        print(json.dumps(dict(requests=counts, seeds=SEEDS, dataset_hash=digest(splits))))
        return

    requests, answers = build(splits[args.split])
    config = json.loads(args.config.read_text())
    checkpoint = json.loads(LIVE_CONFIG.read_text())['checkpoint']
    plan_hash = digest(PLAN.read_text())
    context = dict(dataset_hash=digest(splits), split=args.split, seeds=SEEDS,
                   plan_hash=plan_hash, checkpoint=checkpoint if args.live else None)
    if (config.get('adapter') != ('http' if args.live else 'mock')
            or len(requests) > config['max_requests']):
        parser.error('adapter or request cap does not match this run')
    if args.live:
        pinned = json.loads(LIVE_CONFIG.read_text())
        if config != pinned:
            parser.error('live runs use the pinned stopping configuration')
        if args.split == 'evaluation' and not args.dry_run and args.reviewed_plan_hash != plan_hash:
            parser.error('live evaluation requires the reviewed plan hash from the dry run')
    print(json.dumps(dict(context, requests=len(requests), requests_hash=digest(requests),
                          maximum_attempts=len(requests) * (config['retry_limit'] + 1),
                          model=config['model']), indent=2))
    if args.dry_run:
        return
    # Any rendered evaluation artifacts stay under the ignored local directory.
    if not args.output.resolve().is_relative_to(LOCAL.resolve()):
        parser.error(f'output must be under {LOCAL}')
    run(requests, answers, config, args.output, context, args.live, args.resume)
    save(args.output / 'answers.private.json', answers)
    analyze(args.output, requests, answers)
    print(args.output / 'report.md')


if __name__ == '__main__':
    main()
