from fractions import Fraction as Q
import pytest
from sampling.oracle import analytic, enumerated, enumerate_outcomes, likelihood, terminal


def test_hand_example():
    prior, pa, pb = Q(1, 2), Q(3, 4), Q(1, 4)
    assert analytic('HHT', prior, pa, pb) == Q(3, 4)
    assert enumerated('HHT', prior, pa, pb, 'F', 3) == Q(3, 4)
    assert enumerated('HHT', prior, pa, pb, 'S', 3, a=4, b=1) == Q(3, 4)
    assert analytic('HHT', prior, pa, pb, Q(1, 4), Q(3, 4)) == Q(1, 2)
    assert enumerated('HHT', prior, pa, pb, 'R', 3, qa=Q(1, 4), qb=Q(3, 4)) == Q(1, 2)


def test_properties():
    assert analytic('HHT', Q(1, 2), Q(3, 4), Q(1, 4), Q(1, 3), Q(1, 3)) == Q(3, 4)
    assert analytic('HHT', Q(1, 2), Q(1, 4), Q(3, 4)) == Q(1, 4)
    assert not terminal('HTH', 4, 1, 3)
    with pytest.raises(ValueError):
        enumerated('HTH', Q(1, 2), Q(3, 4), Q(1, 4), 'S', 3, a=4, b=1)
    with pytest.raises(ValueError):
        analytic('H', Q(1, 2), Q(0), Q(0))
    assert likelihood('HHT', Q(2, 3)) == likelihood('HTH', Q(2, 3))
    for condition in ('F', 'S', 'R'):
        outcomes = enumerate_outcomes(Q(2, 3), 5, condition, a=2, b=3, q=Q(1, 4))
        assert sum(outcomes.values()) == 1
        if condition == 'R':
            assert outcomes['NO_REPORT'] == Q(3, 4)
