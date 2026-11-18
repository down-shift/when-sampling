# SYNTHETIC implementation check

Mock outputs are not research findings.

Intervals resample worlds jointly; missing/invalid answers are excluded from numeric metrics and counted below. Each metric requires both paraphrases. Repeated calls are dependent.

- extraction_max_abs_error:S: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- extraction_correct_1e-6:S: 1, 95% bootstrap interval [1.0, 1.0], worlds 16/16
- table_posterior_mae:S: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- extraction_max_abs_error:R: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- extraction_correct_1e-6:R: 1, 95% bootstrap interval [1.0, 1.0], worlds 16/16
- primary_posterior_mae:R: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- primary_posterior_mae:F: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- table_posterior_mae:F: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- primary_posterior_mae:S: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- table_posterior_mae:R: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- extraction_max_abs_error:F: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- extraction_correct_1e-6:F: 1, 95% bootstrap interval [1.0, 1.0], worlds 16/16
- invariance_signed: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- invariance_absolute: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- sensitivity_signed_error: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- sensitivity_absolute_error: 0, 95% bootstrap interval [0.0, 0.0], worlds 16/16
- sensitivity_direction: 1, 95% bootstrap interval [1.0, 1.0], worlds 11/16
- repeated_call_absolute_difference: 0, 95% bootstrap interval [0.0, 0.0], worlds 2/16

Repeated-call mean ranges by world: {"development-000": 0.0, "development-001": 0.0}

Statuses and denominators:

```json
{
  "primary:S": {
    "ok": 36,
    "total": 36
  },
  "extraction:S": {
    "ok": 32,
    "total": 32
  },
  "table:S": {
    "ok": 32,
    "total": 32
  },
  "extraction:R": {
    "ok": 32,
    "total": 32
  },
  "primary:R": {
    "ok": 36,
    "total": 36
  },
  "primary:F": {
    "ok": 36,
    "total": 36
  },
  "table:F": {
    "ok": 32,
    "total": 32
  },
  "table:R": {
    "ok": 32,
    "total": 32
  },
  "extraction:F": {
    "ok": 32,
    "total": 32
  }
}
```
