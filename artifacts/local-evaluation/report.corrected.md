# Corrected evaluation report

Reanalysis of the original saved responses and frozen thresholds. Direction coverage uses only worlds with a nonzero oracle forwarding effect. The exploratory paraphrase metrics were added after inspection of the held-out results. They compare the absolute stopping gap with the mean absolute difference between the two paraphrases within fixed and stopping.

Agreement with stipulated posteriors; no empirical calibration claim.

Intervals resample worlds jointly; missing/invalid answers are excluded from numeric metrics and counted below. Each metric requires both paraphrases. Repeated calls are dependent.

Primary comparisons with both paraphrases: stopping vs fixed 64/64 worlds, forwarding vs fixed 64/64 worlds.
Forwarding direction is defined in 43/64 worlds with a nonzero oracle effect.

- primary_posterior_mae:R: 0.274918, 95% bootstrap interval [0.226091247087225, 0.3245572204779709], worlds 64/64
- table_posterior_mae:F: 0.105288, 95% bootstrap interval [0.0887887352160184, 0.1225088146531742], worlds 64/64
- table_posterior_mae:R: 0.11336, 95% bootstrap interval [0.09096981155565592, 0.1376841796608329], worlds 64/64
- extraction_max_abs_error:R: 0.200484, 95% bootstrap interval [0.15459470258396074, 0.24912622998755757], worlds 60/64
- extraction_correct_1e-6:R: 0.0166667, 95% bootstrap interval [0.0, 0.05172413793103448], worlds 60/64
- primary_posterior_mae:F: 0.265456, 95% bootstrap interval [0.2146254212214489, 0.3172244803792292], worlds 64/64
- extraction_max_abs_error:S: 0.22197, 95% bootstrap interval [0.17245529855095615, 0.2736769600443882], worlds 60/64
- extraction_correct_1e-6:S: 0.05, 95% bootstrap interval [0.0, 0.11475409836065574], worlds 60/64
- table_posterior_mae:S: 0.105181, 95% bootstrap interval [0.08868220112510931, 0.12250881465384385], worlds 64/64
- primary_posterior_mae:S: 0.277609, 95% bootstrap interval [0.22632679711109518, 0.3314702103361734], worlds 64/64
- extraction_max_abs_error:F: 0.166518, 95% bootstrap interval [0.1244667616439028, 0.2144602101079979], worlds 63/64
- extraction_correct_1e-6:F: 0.206349, 95% bootstrap interval [0.1111111111111111, 0.3064516129032258], worlds 63/64
- invariance_signed: -0.0254974, 95% bootstrap interval [-0.05538491188073038, 0.0031523809531848936], worlds 64/64
- invariance_absolute: 0.0907597, 95% bootstrap interval [0.07094598798048853, 0.11175338541834078], worlds 64/64
- exploratory_paraphrase_gap: 0.0618546, 95% bootstrap interval [0.047844847104333024, 0.07673185435647231], worlds 64/64
- exploratory_stopping_gap_minus_paraphrase_gap: 0.0289051, 95% bootstrap interval [0.010257452880431553, 0.049454464287795395], worlds 64/64
- sensitivity_signed_error: -0.0109331, 95% bootstrap interval [-0.04111429639579967, 0.01891176504094472], worlds 64/64
- sensitivity_absolute_error: 0.099977, 95% bootstrap interval [0.08195635211530308, 0.11879689255311096], worlds 64/64
- sensitivity_direction: 0.651163, 95% bootstrap interval [0.5102040816326531, 0.7894736842105263], worlds 43/43
- repeated_call_absolute_difference: 0.00297619, 95% bootstrap interval [0.0, 0.005952380949999998], worlds 2/64

Frozen thresholds (point estimates, full world coverage required)

- primary_posterior_mae:F (max 0.1): fail
- invariance_absolute (max 0.05): fail
- sensitivity_absolute_error (max 0.1): pass
- sensitivity_direction (min 0.75): fail

Repeated-call mean ranges by world: {"evaluation-000": 0.005952380949999998, "evaluation-001": 0.0}

Statuses and denominators:

```json
{
  "primary:R": {
    "ok": 132,
    "total": 132
  },
  "table:F": {
    "ok": 128,
    "total": 128
  },
  "table:R": {
    "ok": 128,
    "total": 128
  },
  "extraction:R": {
    "ok": 124,
    "truncation": 3,
    "out_of_range": 1,
    "total": 128
  },
  "primary:F": {
    "ok": 132,
    "total": 132
  },
  "extraction:S": {
    "ok": 124,
    "truncation": 4,
    "total": 128
  },
  "table:S": {
    "ok": 128,
    "total": 128
  },
  "primary:S": {
    "ok": 132,
    "total": 132
  },
  "extraction:F": {
    "ok": 127,
    "truncation": 1,
    "total": 128
  }
}
```
