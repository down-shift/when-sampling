from fractions import Fraction
from itertools import product


def likelihood(x: str, p: Fraction) -> Fraction:
    if not x or any(c not in 'HT' for c in x):
        raise ValueError('record must be a nonempty H/T sequence')
    if not 0 <= p <= 1:
        raise ValueError('invalid coin probability')
    return p ** x.count('H') * (1 - p) ** x.count('T')


def terminal(x: str, a: int, b: int, cap: int) -> bool:
    if min(a, b, cap) < 1 or not x or len(x) > cap or any(c not in 'HT' for c in x):
        return False
    def stopped(s: str) -> bool:
        return s.count('H') >= a or s.count('T') >= b or len(s) >= cap
    return stopped(x) and not any(stopped(x[:i]) for i in range(1, len(x)))


def posterior(prior: Fraction, la: Fraction, lb: Fraction) -> Fraction:
    if not 0 < prior < 1 or min(la, lb) < 0:
        raise ValueError('invalid prior or likelihood')
    denominator = prior * la + (1 - prior) * lb
    if not denominator:
        raise ValueError('impossible observation')
    return prior * la / denominator


def analytic(x: str, prior: Fraction, pa: Fraction, pb: Fraction, qa: Fraction = Fraction(1), qb: Fraction = Fraction(1)) -> Fraction:
    if not (0 <= qa <= 1 and 0 <= qb <= 1):
        raise ValueError('invalid reporting probability')
    return posterior(prior, likelihood(x, pa) * qa, likelihood(x, pb) * qb)


def enumerate_outcomes(p: Fraction, n: int, condition: str, *, a: int = 1, b: int = 1, q: Fraction = Fraction(1)) -> dict[str, Fraction]:
    if not 0 <= p <= 1 or not 0 <= q <= 1 or n < 1 or condition not in ('F', 'S', 'R'):
        raise ValueError('invalid parameters')
    outcomes = {}
    if condition == 'S':
        for length in range(1, n + 1):
            for seq in product('HT', repeat=length):
                x = ''.join(seq)
                if terminal(x, a, b, n):
                    outcomes[x] = likelihood(x, p)
    else:
        for seq in product('HT', repeat=n):
            x = ''.join(seq)
            outcomes[x] = likelihood(x, p) * (q if condition == 'R' else 1)
        if condition == 'R':
            outcomes['NO_REPORT'] = 1 - q
    return outcomes


def enumerated(x: str, prior: Fraction, pa: Fraction, pb: Fraction, condition: str, n: int, *, a: int = 1, b: int = 1, qa: Fraction = Fraction(1), qb: Fraction = Fraction(1)) -> Fraction:
    oa = enumerate_outcomes(pa, n, condition, a=a, b=b, q=qa)
    ob = enumerate_outcomes(pb, n, condition, a=a, b=b, q=qb)
    if x not in oa or x not in ob:
        raise ValueError('observation not in sample space')
    return posterior(prior, oa[x], ob[x])
