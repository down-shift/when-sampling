from fractions import Fraction

import pytest

from sampling import stopping


def test_exact_oracle_and_label_swap():
    case = stopping.WORKED
    assert [stopping.oracle(case, rule) for rule in (0, 2, 3)] == ['SAME', 'UP', 'DOWN']
    swapped = dict(case, pa=case['pb'], pb=case['pa'])
    assert [stopping.oracle(swapped, rule) for rule in (0, 2, 3)] == ['SAME', 'DOWN', 'UP']
    with pytest.raises(ValueError, match='STOP is impossible'):
        stopping.oracle(case, 1)


def test_split_audit_rejects_an_equivalent():
    splits = stopping.generate()
    assert stopping.verify(splits) == {'development': 48, 'evaluation': 240}
    first = splits['development'][0]
    evaluation = splits['evaluation'][0]
    pa, pb = sorted(1 - Fraction(first[k]) for k in ('pa', 'pb'))
    if Fraction(evaluation['pa']) > Fraction(evaluation['pb']):
        pa, pb = pb, pa
    evaluation.update(pa=str(pa), pb=str(pb), irrelevant='ignored')
    with pytest.raises(ValueError, match='duplicate case family'):
        stopping.verify(splits)


def test_split_audit_checks_rendered_controls(monkeypatch):
    splits = stopping.generate()
    render = stopping.render
    cases = {splits[split][0]['id'] for split in splits}

    def duplicate_control(case, rule, kind):
        if case.get('id') in cases and rule == 2 and kind == 'control':
            return 'same rendered control in both splits'
        return render(case, rule, kind)

    monkeypatch.setattr(stopping, 'render', duplicate_control)
    with pytest.raises(ValueError, match='duplicate exact rendered prompt'):
        stopping.verify(splits)
