# Evaluation report

Agreement with stipulated posteriors; no empirical calibration claim.

Intervals resample worlds jointly; missing/invalid answers are excluded from numeric metrics and counted below. Each metric requires both paraphrases. Repeated calls are dependent.

- primary_posterior_mae:R: 0.7125, 95% bootstrap interval [0.7125, 0.7125], worlds 1/2
- table_posterior_mae:S: 0.0375, 95% bootstrap interval [0.0, 0.07500000000000001], worlds 2/2
- table_posterior_mae:R: 0.0214286, 95% bootstrap interval [0.0, 0.04285714289999998], worlds 2/2
- primary_posterior_mae:F: 0.5, 95% bootstrap interval [0.5, 0.5], worlds 1/2
- table_posterior_mae:F: 0.0375, 95% bootstrap interval [0.0, 0.07500000000000001], worlds 2/2
- extraction_max_abs_error:R: 0.1875, 95% bootstrap interval [0.1875, 0.1875], worlds 1/2
- extraction_correct_1e-6:R: 0, 95% bootstrap interval [0.0, 0.0], worlds 1/2
- extraction_max_abs_error:F: 0.5, 95% bootstrap interval [0.5, 0.5], worlds 1/2
- extraction_correct_1e-6:F: 0, 95% bootstrap interval [0.0, 0.0], worlds 1/2
- sensitivity_signed_error: -0.2125, 95% bootstrap interval [-0.21250000000000002, -0.21250000000000002], worlds 1/2
- sensitivity_absolute_error: 0.2125, 95% bootstrap interval [0.21250000000000002, 0.21250000000000002], worlds 1/2
- sensitivity_direction: 0, 95% bootstrap interval [0.0, 0.0], worlds 1/2
- repeated_call_absolute_difference: 0, 95% bootstrap interval [0.0, 0.0], worlds 1/2

Repeated-call mean ranges by world: {"development-001": 0.0}

Statuses and denominators:

```json
{
  "primary:S": {
    "truncation": 8,
    "total": 8
  },
  "extraction:R": {
    "truncation": 2,
    "ok": 2,
    "total": 4
  },
  "extraction:S": {
    "truncation": 3,
    "malformed_json": 1,
    "total": 4
  },
  "primary:F": {
    "ok": 4,
    "truncation": 4,
    "total": 8
  },
  "primary:R": {
    "ok": 4,
    "truncation": 4,
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
    "ok": 2,
    "malformed_json": 2,
    "total": 4
  }
}
```
