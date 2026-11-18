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
from .runner import DIRECTIONS, parse, run

RULES = ((0, 'H'), (0, 'T'), (1, 'H'), (1, 'T'))
OUTCOME = {'H': 'heads', 'T': 'tails'}
KINDS = ('decision', 'control')
FIRST_PILOT_SEEDS = dict(development=8191, evaluation=131071, order=524287, bootstrap=4242)
SEEDS = dict(development=81911, evaluation=1310711, order=5242871, bootstrap=4242)
WORKED = dict(pa='3/4', pb='1/4', visible='H', ids='KLMN', order=[0, 1, 2, 3])
LOCAL = Path('artifacts/stopping-local')
PLAN = Path('stopping-plan.md')
LIVE_CONFIG = Path('config.stopping.json')
DEVELOPMENT_RUN = LOCAL / 'live-development-thinking'


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


def generate(seeds=None):
    if seeds is None:
        previous = generate(FIRST_PILOT_SEEDS)
        return generate_cases(SEEDS, {canonical(case) for cases in previous.values() for case in cases})
    return generate_cases(seeds, set())


def generate_cases(seeds, excluded):
    seen = {canonical(WORKED)} | excluded
    grid = sorted({Q(n, d) for d in (10, 12, 16, 20) for n in range(1, d)
                   if Q(1, 10) <= Q(n, d) <= Q(9, 10)})
    splits = {}
    for split, size in (('development', 8), ('evaluation', 40)):
        rng = random.Random(seeds[split])
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
        evidence = (f'A program shows you the result of flip 2: {OUTCOME[hidden]}.' if hidden else
                    f'A program copies the already-visible result of flip 1: {visible}. '
                    'The program never reads flip 2, and flip 2 remains hidden from you.')
    return (prefix + evidence + '\nBefore: you know the result of flip 1 only.\n'
            'After: you also receive the information given above.\n'
            'From before to after, does the probability of hypothesis A go UP, go DOWN, '
            'or stay the SAME? '
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
    seen_cases = {canonical(worked)} | {
        canonical(case) for cases in generate(FIRST_PILOT_SEEDS).values() for case in cases
    }
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


def analyze(directory, requests, answers, cases, bootstrap=5000, reparse=False):
    manifest = json.loads((directory / 'manifest.json').read_text())
    if manifest['identity']['requests_hash'] != digest(requests):
        raise ValueError('requests do not match the run manifest')
    suffix = '.corrected' if reparse else ''
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
    recovered = 0
    paired = {}
    prior_update = {}
    for case in cases:
        pa, pb = Q(case['pa']), Q(case['pb'])
        prior_update[case['id']] = direction(
            likelihood(case['visible'], pb), likelihood(case['visible'], pa)
        )
    baseline = Counter()
    for request in requests:
        rid = request['id']
        row = rows[rid]
        label = answers[rid]['direction']
        kind = request['kind']
        status, parsed = row['status'], row['parsed']
        if reparse and status == 'malformed_json':
            status, parsed = parse(row['raw'], kind)
            recovered += status == 'ok'
        predicted = parsed['direction'] if status == 'ok' else 'INVALID'
        matrix[kind][label][predicted] += 1
        statuses[status] += 1
        paired.setdefault(request['case'], {}).setdefault(label, {})[kind] = int(label == predicted)
        if kind == 'decision':
            baseline[label] += int(label == prior_update[request['case']])

    accuracy = {kind: {label: matrix[kind][label][label] / sum(matrix[kind][label].values())
                       for label in DIRECTIONS} for kind in KINDS}
    differences = {
        label: [case[label]['control'] - case[label]['decision'] for case in paired.values()]
        for label in DIRECTIONS
    }
    differences['overall'] = [sum(case) / 3 for case in zip(*(differences[x] for x in DIRECTIONS))]
    rng = random.Random(SEEDS['bootstrap'])
    n = len(paired)
    prior_baseline = dict(overall=sum(baseline.values()) / (3 * n),
                          by_class={label: baseline[label] / n for label in DIRECTIONS})
    draws = [rng.choices(range(n), k=n) for _ in range(bootstrap)]
    gaps = {}
    for label, values in differences.items():
        means = sorted(sum(values[i] for i in draw) / n for draw in draws)
        gaps[label] = dict(estimate=sum(values) / n,
                           ci95=[means[int((bootstrap - 1) * q)] for q in (.025, .975)])

    save(directory / f'analysis{suffix}.json', dict(
        accuracy=accuracy, confusion=matrix, response_status=dict(statuses),
        baseline=dict(overall=1 / 3, by_class=dict(UP=0, DOWN=0, SAME=1)),
        flip1_vs_prior_baseline=prior_baseline,
        control_minus_decision=gaps, base_cases=n, bootstrap_draws=bootstrap,
        bootstrap_seed=SEEDS['bootstrap'], recovered_responses=recovered,
    ))
    report = ['# Stopping pilot', '', f'{n} base cases, {len(requests)} requests.', '']
    if manifest['synthetic']:
        report += ['Synthetic oracle mock. These results check the pipeline only.', '']
    if reparse:
        report += [f'Reparsed saved raw responses and recovered {recovered} final answers. '
                   'Truncated responses count as incorrect.', '']
    for kind in KINDS:
        total = sum(sum(row.values()) for row in matrix[kind].values())
        invalid = sum(row['INVALID'] for row in matrix[kind].values())
        report.append(f'{kind.title()} invalid responses: {invalid}/{total} ({invalid / total:.1%}).')
    report.append('')
    report += ['| Correct label | Decision accuracy | Control accuracy | Always-SAME | Flip 1 vs prior |',
               '| --- | ---: | ---: | ---: | ---: |']
    for label in DIRECTIONS:
        report.append(f'| {label} | {accuracy["decision"][label]:.1%} | '
                      f'{accuracy["control"][label]:.1%} | {int(label == "SAME"):.1%} | '
                      f'{prior_baseline["by_class"][label]:.1%} |')
    report += ['', f'Always-SAME overall accuracy is 33.3%. The flip 1 vs prior baseline '
               f'scores {prior_baseline["overall"]:.1%} and ignores the extra information.', '',
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
    report_path = directory / f'report{suffix}.md'
    report_path.write_text('\n'.join(report) + '\n')
    return report_path


def check_development(directory, context, config, cases):
    manifest = json.loads((directory / 'manifest.json').read_text())
    identity = manifest['identity']
    requests, _ = build(cases)
    expected = dict(context, split='development', requests_hash=digest(requests), live=True)
    if manifest['synthetic'] or manifest['config'] != config or any(
        identity.get(key) != value for key, value in expected.items()
    ):
        raise ValueError('development run must match the revised live plan and configuration')
    analysis = json.loads((directory / 'analysis.json').read_text())
    for kind in KINDS:
        invalid = sum(analysis['confusion'][kind][label]['INVALID'] for label in DIRECTIONS)
        if invalid / (len(cases) * 3) > .05:
            raise ValueError(f'development {kind} invalid rate exceeds 5%')
    if min(analysis['accuracy']['control'].values()) < .90:
        raise ValueError('development controls must reach 90% accuracy in each class')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('verify', 'example', 'run', 'reanalyze'))
    parser.add_argument('--split', choices=('development', 'evaluation'), default='evaluation')
    parser.add_argument('--config', type=Path, default=Path('config.mock.json'))
    parser.add_argument('--output', type=Path, default=LOCAL / 'mock-revised')
    parser.add_argument('--development-run', type=Path, default=DEVELOPMENT_RUN)
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

    if args.command == 'reanalyze':
        identity = json.loads((args.output / 'manifest.json').read_text())['identity']
        if identity['dataset_hash'] != digest(splits):
            splits = generate(FIRST_PILOT_SEEDS)
        if identity['dataset_hash'] != digest(splits):
            parser.error('unknown dataset in the run manifest')
        cases = splits[identity['split']]
        requests = json.loads((args.output / 'requests.json').read_text())
        _, answers = build(cases)
        print(analyze(args.output, requests, answers, cases, reparse=True))
        return
    cases = splits[args.split]
    requests, answers = build(cases)
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
        if args.split == 'evaluation' and not args.dry_run:
            if args.reviewed_plan_hash != plan_hash:
                parser.error('live evaluation requires the reviewed plan hash from the dry run')
            try:
                check_development(args.development_run, context, config, splits['development'])
            except (OSError, ValueError, KeyError) as exc:
                parser.error(f'development gate failed: {exc}')
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
    print(analyze(args.output, requests, answers, cases))


if __name__ == '__main__':
    main()
