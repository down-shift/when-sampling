# Protocol draft

## Question and assumptions

We measure reported posterior probabilities under explicit Bayesian generative models. Tosses are conditionally independent given the hypothesis. Fixed-length and deterministic stopping tasks reveal the complete ordered record; stopping records must be terminal. Reporting tasks consist of one attempt, with a hypothesis-dependent independent forwarding probability; receipt is evidence. No retries or selection of experiments occur.

## Comparisons

Compare absolute posterior error in F, S and R. Compare within-world S minus F (oracle zero), with baseline accuracy and repeated-call variability. Compare R minus F against its exact signed effect, including direction accuracy when the effect is nonzero. Likelihood-table and likelihood-extraction requests are independent diagnostics.

## Dataset and use

Generate rational, nondegenerate worlds with explicit seeds, balanced hypothesis labels and reporting effects in both directions; select by oracle properties alone. Keep development and held-out evaluation worlds distinct including label swaps. Development is for checking prompts and pipeline; do not modify held-out tasks after inspecting results. Two paraphrases per condition are aggregated within each world before inference.

## Failure handling and analysis

Keep malformed, out-of-range, refusal, truncation and transport failures distinct; report denominators and do not silently reprompt. Report absolute errors, paired differences and diagnostic accuracy with world-level paired bootstrap intervals and a fixed seed. Repeated requests are dependent within worlds. Any accuracy-restricted analysis is secondary and accompanies unconditional results and subset size.

## Decisions and limitations

Practically meaningful success thresholds must be decided before held-out evaluation. This is a draft, not a frozen protocol or public preregistration. Hand-selected observations do not establish empirical calibration. Hosted model outputs can vary even at temperature zero. Stopping-rule irrelevance and Bayesian updating are established results; evidence-selection research already studies failures to account for selection.
