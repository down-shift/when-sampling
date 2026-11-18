# Manual prompt review

Reviewed both primary templates for each condition against the model assumptions. They explicitly retain conditional independence, the prior, the complete ordered record and its length, and the full collection/reporting mechanism. The second version changes introductory wording only; consequently this is a limited robustness check, not broad paraphrase coverage. Neither gives an invariance hint.

For the hand example prior 1/2, head probabilities 3/4 and 1/4, record HHT:

- F specifies exactly three tosses, complete ordered HHT: likelihoods 9/64 and 3/64; posterior 3/4.
- S specifies stopping at four heads, one tail, or three tosses. HHT is terminal with no earlier stopping prefix: likelihoods 9/64 and 3/64; posterior 3/4.
- R specifies exactly three tosses and forwarding probabilities 1/4 and 3/4, with exactly one attempt and no retries: joint likelihoods 9/256 and 9/256; posterior 1/2.

The R observation is the record AND receipt. A delivered-record conditional distribution paired with the original prior would be wrong. Full rendered representative requests are saved in `artifacts/prompt_examples.json`, with private oracle answers in a separate file. Likelihood-table controls intentionally disclose likelihoods; primary and extraction requests do not disclose answers.

Potential design limitations: both template versions are close paraphrases; the selected probability grid and posterior screen constrain generalization. Equal-reporting controls share the same apparatus narrative as informative reporting. The stopping family, arithmetic difficulty and observation lengths are not independently manipulated. Effect direction is set through forwarding odds, not inferred from model performance. These are diagnostic tasks, not evidence of hidden mental processes.
