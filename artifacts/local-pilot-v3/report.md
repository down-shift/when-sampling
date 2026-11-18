# Evaluation report

Agreement with stipulated posteriors; no empirical calibration claim.

Intervals resample worlds jointly; missing/invalid answers are excluded from numeric metrics and counted below. Each metric requires both paraphrases. Repeated calls are dependent.

Primary comparisons with both paraphrases: stopping vs fixed 2/2 worlds, forwarding vs fixed 2/2 worlds.

- extraction_max_abs_error:R: 0.285431, 95% bootstrap interval [0.28125, 0.2896125], worlds 2/2
- extraction_correct_1e-6:R: 0, 95% bootstrap interval [0.0, 0.0], worlds 2/2
- extraction_max_abs_error:S: 0.399347, 95% bootstrap interval [0.052599999999999994, 0.74609375], worlds 2/2
- extraction_correct_1e-6:S: 0, 95% bootstrap interval [0.0, 0.0], worlds 2/2
- primary_posterior_mae:R: 0.35625, 95% bootstrap interval [0.0625, 0.65], worlds 2/2
- table_posterior_mae:S: 0.075, 95% bootstrap interval [0.0, 0.15000000000000002], worlds 2/2
- table_posterior_mae:R: 0.02145, 95% bootstrap interval [0.0, 0.04290000000000005], worlds 2/2
- primary_posterior_mae:F: 0.309524, 95% bootstrap interval [0.11904761906428574, 0.5], worlds 2/2
- primary_posterior_mae:S: 0.372024, 95% bootstrap interval [0.11904761906428574, 0.625], worlds 2/2
- table_posterior_mae:F: 0.075, 95% bootstrap interval [0.0, 0.15000000000000002], worlds 2/2
- extraction_max_abs_error:F: 0.272, 95% bootstrap interval [0.044000000000000004, 0.5], worlds 2/2
- extraction_correct_1e-6:F: 0, 95% bootstrap interval [0.0, 0.0], worlds 2/2
- invariance_signed: -0.0625, 95% bootstrap interval [-0.125, 0.0], worlds 2/2
- invariance_absolute: 0.0625, 95% bootstrap interval [0.0, 0.125], worlds 2/2
- sensitivity_signed_error: -0.0467262, 95% bootstrap interval [-0.15000000000000002, 0.05654761906428574], worlds 2/2
- sensitivity_absolute_error: 0.103274, 95% bootstrap interval [0.05654761906428574, 0.15000000000000002], worlds 2/2
- sensitivity_direction: 0.5, 95% bootstrap interval [0.0, 1.0], worlds 2/2
- repeated_call_absolute_difference: 0, 95% bootstrap interval [0.0, 0.0], worlds 2/2

Repeated-call mean ranges by world: {"development-000": 0.0, "development-001": 0.0}

Statuses and denominators:

```json
{
  "primary:S": {
    "ok": 8,
    "total": 8
  },
  "extraction:R": {
    "ok": 4,
    "total": 4
  },
  "extraction:S": {
    "ok": 4,
    "total": 4
  },
  "primary:F": {
    "ok": 8,
    "total": 8
  },
  "primary:R": {
    "ok": 8,
    "total": 8
  },
  "table:S": {
    "ok": 4,
    "total": 4
  },
  "table:R": {
    "ok": 4,
    "total": 4
  },
  "table:F": {
    "ok": 4,
    "total": 4
  },
  "extraction:F": {
    "ok": 4,
    "total": 4
  }
}
```
