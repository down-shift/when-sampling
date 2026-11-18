"""Dataset construction, prompt rendering and independent generative verification."""
import hashlib
import json
import random
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
from .oracle import analytic, likelihood, terminal, enumerate_outcomes


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def truth(w, c):
    pi, pa, pb, qa, qb = (Q(w[k]) for k in ('prior', 'pa', 'pb', 'qa', 'qb'))
    la, lb = likelihood(w['x'], pa), likelihood(w['x'], pb)
    if c == 'R':
        la, lb = la * qa, lb * qb
    return {'posterior_h_a': str(analytic(w['x'], pi, pa, pb, qa if c == 'R' else Q(1), qb if c == 'R' else Q(1))), 'likelihood_h_a': str(la), 'likelihood_h_b': str(lb)}


def canonical(w):
    keys = ('prior', 'pa', 'pb', 'qa', 'qb', 'x', 'a', 'b', 'cap')
    swapped = dict(w, prior=str(1-Q(w['prior'])), pa=w['pb'], pb=w['pa'], qa=w['qb'], qb=w['qa'])
    return min(digest({k:v[k] for k in keys}) for v in (w, swapped))


def generate(dev=16, evaluation=64, dev_seed=1729, eval_seed=2718):
    seen = set()
    splits = {}
    for split, size, seed in [('development', dev, dev_seed), ('evaluation', evaluation, eval_seed)]:
        rng = random.Random(seed)
        worlds = []
        attempts = 0
        while len(worlds) < size:
            attempts += 1
            if attempts > 100000:
                raise ValueError('construction exhausted; reduce size')
            i = len(worlds)
            low, high = rng.choice([(Q(1,4),Q(3,4)), (Q(1,3),Q(2,3)), (Q(2,5),Q(3,5))])
            pa, pb = (low, high) if i % 2 else (high, low)
            qa, qb = rng.choice([(Q(1,4),Q(3,4)), (Q(1,3),Q(2,3)), (Q(2,5),Q(4,5))])
            if i % 3 == 1:
                qa, qb = qb, qa
            elif i % 3 == 2:
                qb = qa
            cap, a, b = rng.randint(3,8), rng.randint(1,4), rng.randint(1,4)
            x = ''
            while len(x) < cap:
                x += rng.choice('HT')
                if terminal(x,a,b,cap):
                    break
            w = dict(prior=str(rng.choice([Q(1,3),Q(1,2),Q(2,3)])),pa=str(pa),pb=str(pb),qa=str(qa),qb=str(qb),x=x,a=a,b=b,cap=cap)
            vals = [Q(truth(w,c)['posterior_h_a']) for c in ('F','R')]
            key = canonical(w)
            if min(vals) < Q(1,20) or max(vals) > Q(19,20) or key in seen:
                continue
            seen.add(key)
            w['id'] = f'{split}-{i:03d}'
            worlds.append(w)
        splits[split] = worlds
    return dict(schema=1, seeds=dict(development=dev_seed,evaluation=eval_seed), splits=splits)


def verify(dataset):
    seen = set()
    checked = 0
    for worlds in dataset['splits'].values():
        for w in worlds:
            key = canonical(w)
            assert key not in seen
            seen.add(key)
            assert terminal(w['x'],w['a'],w['b'],w['cap'])
            for c in ('F','S','R'):
                distributions = []
                n = w['cap'] if c == 'S' else len(w['x'])
                for pk,qk in [('pa','qa'),('pb','qb')]:
                    p = Q(w[pk])
                    q = Q(w[qk]) if c == 'R' else Q(1)
                    # Multiply branch probabilities, then merge by observed outcome.
                    dist = {}
                    for seq in product('HT', repeat=n):
                        weight = Q(1)
                        for toss in seq:
                            weight *= p if toss == 'H' else 1-p
                        record = ''.join(seq)
                        if c == 'S':
                            for length in range(1,n+1):
                                if terminal(record[:length],w['a'],w['b'],n):
                                    record=record[:length]
                                    break
                        dist[record]=dist.get(record,Q(0))+weight*q
                        if c == 'R':
                            dist['NO_REPORT']=dist.get('NO_REPORT',Q(0))+weight*(1-q)
                    assert sum(dist.values()) == 1
                    expected=enumerate_outcomes(p,n,c,a=w['a'],b=w['b'],q=q)
                    assert dist == expected
                    distributions.append(dist)
                la,lb=(d[w['x']] for d in distributions)
                pi=Q(w['prior'])
                enumerated=pi*la/(pi*la+(1-pi)*lb)
                target=truth(w,c)
                assert enumerated == Q(target['posterior_h_a'])
                assert la == Q(target['likelihood_h_a']) and lb == Q(target['likelihood_h_b'])
                checked += 1
    return checked


def prompt(w,c,variant,kind):
    prefix = (f"Two hypotheses are H_A and H_B. P(H_A)={w['prior']}; P(H_B)=1-P(H_A). "
              f"Given H_A, each toss has head probability {w['pa']}; given H_B it is {w['pb']}. "
              "Tosses are independent conditional on the hypothesis. ")
    if c == 'F':
        policy = f"Before any outcomes, the experimenter commits to exactly {len(w['x'])} tosses independently of the hypothesis and outcomes. The complete ordered record is {w['x']}. "
    elif c == 'S':
        policy = f"The experimenter stops as soon as {w['a']} heads or {w['b']} tails have occurred, or after {w['cap']} tosses, whichever comes first. The observer receives the complete ordered terminal record {w['x']}, of length {len(w['x'])}. "
    else:
        policy = f"The experimenter commits to exactly {len(w['x'])} tosses. An apparatus knows the hidden hypothesis and independently forwards the complete record with probability {w['qa']} under H_A or {w['qb']} under H_B. There is exactly one attempt: no resampling, replacement, retries or search. Without forwarding there is no report. The observer received the forwarded complete ordered record {w['x']}. "
    if variant:
        prefix = "Consider the following specified probability model. " + prefix
        policy = "The observation protocol is as follows. " + policy
    if kind == 'table':
        t = truth(w,c)
        prefix = f"P(H_A)={w['prior']}; P(H_B)=1-P(H_A). The complete observation has likelihood {t['likelihood_h_a']} under H_A and {t['likelihood_h_b']} under H_B. "
        policy = "For a forwarded report these likelihoods include both generating the record and forwarding it. " if c == 'R' else ''
        if variant:
            prefix = 'Use this likelihood table. ' + prefix
    if kind == 'extraction':
        question = 'Return only JSON {"likelihood_h_a": <number between 0 and 1>, "likelihood_h_b": <number between 0 and 1>} giving the probability of the complete observation conditional on each hypothesis.'
    else:
        question = 'Given everything the observer was told and observed, return only JSON {"posterior_h_a": <number between 0 and 1>}.'
    return prefix + policy + question


def requests(dataset, split, repeat_worlds=0, order_seed=31415):
    result, answers = [], {}
    for i,w in enumerate(dataset['splits'][split]):
        for c in ('F','S','R'):
            for variant in range(2):
                for kind in ('primary','table','extraction'):
                    for repeat in range(2 if i < repeat_worlds and kind == 'primary' else 1):
                        rid = f"{w['id']}:{c}:{variant}:{kind}:{repeat}"
                        text = prompt(w,c,variant,kind)
                        result.append(dict(id=rid,world=w['id'],condition=c,variant=variant,kind=kind,repeat=repeat,prompt=text,prompt_hash=digest(text)))
                        answers[rid] = truth(w,c)
    random.Random(order_seed).shuffle(result)
    return result, answers
