"""Development-only paired check of posterior comparison wording."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import random

from . import stopping
from .project import digest, save
from .runner import run

OLD = ('From before to after, does the probability of hypothesis A go UP, go DOWN, '
       'or stay the SAME? ')
NEW = ('Compare the probability of A given flip 1 and the additional information with '
       'the probability of A given flip 1 alone. Is the first probability higher (UP), '
       'lower (DOWN), or equal (SAME)? ')


def build():
    cases = stopping.generate()['development']
    items = []
    for case in cases:
        rule = int(case['visible'] == 'T')
        items.append((case['id'] + ':same', stopping.render(case, rule, 'control'), 'SAME'))
    # With identical flip probabilities, opposite outcomes return exactly to the
    # prior. Different probabilities on flip 2 create the intended conflict.
    for i, (first, second, label) in enumerate([
        ('heads', 'tails', 'DOWN'), ('tails', 'heads', 'UP'),
        ('heads', 'tails', 'DOWN'), ('tails', 'heads', 'UP'),
        ('heads', 'tails', 'DOWN'), ('tails', 'heads', 'UP'),
        ('heads', 'tails', 'DOWN'), ('tails', 'heads', 'UP'),
    ]):
        a1, b1, a2, b2 = [(Fraction(3, 4), Fraction(1, 4), Fraction(3, 5), Fraction(2, 5)),
                           (Fraction(4, 5), Fraction(1, 5), Fraction(7, 12), Fraction(5, 12))][(i // 2) % 2]
        if i >= 4:
            a1, b1, a2, b2 = 1-a1, 1-b1, 1-a2, 1-b2
            first = 'tails' if first == 'heads' else 'heads'
            second = 'tails' if second == 'heads' else 'heads'
        f_a, f_b = (a1, b1) if first == 'heads' else (1-a1, 1-b1)
        s_a, s_b = (a2, b2) if second == 'heads' else (1-a2, 1-b2)
        before = f_a / (f_a + f_b)
        after = f_a*s_a / (f_a*s_a + f_b*s_b)
        assert stopping.direction(before, after) == label
        assert stopping.direction(Fraction(1, 2), after) != label
        prompt = (f'Hypotheses A and B are equally likely before any flips. Two flips are '
                  f'generated independently conditional on the hypothesis. On flip 1, the probability '
                  f'of heads is {a1} under A and {b1} under B. On flip 2, the probability '
                  f'of heads is {a2} under A and {b2} under B.\nYou see that flip 1 was {first}.\n'
                  f'A program shows you the result of flip 2: {second}.\n'
                  'Before: you know the result of flip 1 only.\n'
                  'After: you also receive the information given above.\n' + OLD +
                  'Return only JSON with the key "direction" and one of "UP", "DOWN", or "SAME".')
        items.append((f'directional-{i}', prompt, label))
    requests, answers = [], {}
    for item, prompt, label in items:
        assert prompt.count(OLD) == 1
        for variant, text in [('original', OLD), ('revised', NEW)]:
            rendered = prompt.replace(OLD, text)
            rid = f'{item}:{variant}'
            requests.append(dict(id=rid, case=item, pair=item, kind='control', variant=variant,
                                 prompt=rendered, prompt_hash=digest(rendered)))
            answers[rid] = dict(direction=label)
    random.Random(92731).shuffle(requests)
    return requests, answers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--output', type=Path, default=Path('artifacts/stopping-local/reference-check'))
    args = parser.parse_args()
    requests, answers = build()
    config_path = Path('config.stopping.8b.json' if args.live else 'config.mock.json')
    config = json.loads(config_path.read_text())
    if not args.output.resolve().is_relative_to(stopping.LOCAL.resolve()):
        parser.error('output must be under artifacts/stopping-local')
    context = dict(split='reference-development', requests_hash=digest(requests))
    print(json.dumps(dict(requests=len(requests), requests_hash=digest(requests), live=args.live)))
    if args.dry_run:
        return
    run(requests, answers, config, args.output, context, args.live, args.resume)
    save(args.output / 'answers.private.json', answers)
    rows = {row['id']: row for row in map(json.loads, (args.output / 'responses.jsonl').read_text().splitlines())}
    report = []
    corrections = directional = invalid = 0
    for item in dict.fromkeys(r['case'] for r in requests):
        original, revised = (rows[f'{item}:{v}'] for v in ('original', 'revised'))
        expected = answers[f'{item}:original']['direction']
        def prediction(row):
            return row['parsed']['direction'] if row['status'] == 'ok' else 'INVALID'
        old, new = prediction(original), prediction(revised)
        if expected == 'SAME':
            corrections += old != expected and new == expected
        else:
            directional += new == expected
        invalid += new == 'INVALID'
        report.append(dict(item=item, expected=expected, original=old, revised=new))
    result = dict(paired_corrections=corrections, directional_correct=directional,
                  revised_invalid=invalid, passed=corrections >= 6 and directional >= 7 and invalid <= 1,
                  pairs=report)
    save(args.output / 'reference-analysis.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
