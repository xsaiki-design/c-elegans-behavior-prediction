# 0005 — Follow-up: can the model be made more accurate?

**Status:** decided (2026-11-09), before any of these candidates were run. The headline result (0002–0004) is not
changed by anything here; this is a labelled follow-up.

## Decision

Test a short, fixed list of improvements with the same leave-one-worm-out test (horizon 8 frames, 40 worms), and report
every one of them, including those that don't help.

| | Candidate | What changes | Why it might help |
|---|---|---|---|
| M0 | Headline model | nothing (logistic regression, default settings) | the reference |
| C1 | Tuned regularisation | the model's regularisation strength is picked from 0.01, 0.03, 0.1, 0.3, 1 by a 5-fold split *of the 39 training worms* | default settings may over- or under-fit 92 features |
| C2 | Longer history | adds each neuron type's change over 2 and 10 frames (~1.2 s and ~6 s) beside the 5-frame change; tuned as in C1 | the decision builds over several seconds (the "how far ahead" curve) |
| C3 | Body history | adds the change in speed over the last 5 frames, to **both** the body baseline and the brain model | a fair test needs an equally improved baseline |
| C4 | Gradient-boosted trees | a nonlinear model on the headline features (earlier exploratory run: 0.70) | interactions between neurons |
| C5 | Best combination | the candidates above that pass the rule, combined | |

## Rule for calling something an improvement

- Per worm, the candidate's held-out AUC is compared with M0's; a Wilcoxon signed-rank test over the 40 paired worms.
- Five comparisons are made (C1–C5), so p-values are Holm-corrected for multiple testing. An improvement needs a
  corrected p < 0.05 **and** a higher median AUC.
- For C3 and C5 the brain must also still beat the equally improved body baseline (same test), or the gain belongs to
  the body, not the brain.
- Any tuning happens inside the training worms only. The test worm is never used to choose anything.

## Honest limits

- Choosing the best of several candidates on the same 40 worms makes the winner's number slightly optimistic, even with
  the correction. The write-up says so and keeps the headline as the main result.
- If nothing passes, that is the result: the headline model is already about as good as these data allow with these
  methods.

## Results (2026-11-09)

| Candidate | Median AUC, unseen worms | Better than M0 in | Holm-corrected p | Counts as an improvement |
|---|---|---|---|---|
| M0 headline | 0.677 | – | – | reference |
| C1 tuned regularisation | 0.678 | 29 of 40 | 0.010 | yes, but negligible (+0.0006) |
| C2 longer history | 0.683 | 18 of 40 | 0.51 | no |
| C3 body history (both models) | 0.682 | 23 of 40 | 0.15 | no |
| **C4 gradient-boosted trees** | **0.697** | **30 of 40** | **0.0006** | **yes (+0.03)** |
| C5 combination of passing (C1 + C4) | 0.697 | 30 of 40 | 0.0006 | same as C4 (tuning C doesn't apply to trees) |

- **The one meaningful gain is nonlinearity:** boosted trees add about 0.03 AUC, so neurons carry some information in
  combination that a straight weighted sum misses. With boosted trees on both sides, the brain still beats the body
  alone (0.70 vs 0.65, 33 of 40 worms; `results/explore.json`).
- **The brain's advantage survives a stronger body baseline** (C3: brain + body beats the improved body model in
  29 of 40 worms).
- **Caveat:** tuning picked the strongest regularisation offered (0.01) for every worm, the edge of the list. Stronger
  regularisation might help a little more; testing it now would be choosing after seeing results, so it's left as a
  next step.
- **The live page keeps the linear model on purpose:** it runs exactly in the browser and its "why" breakdown is exact.
  Boosted trees would be +0.03 AUC but neither.
- The throwaway experiment code is on the [`prototype/accuracy`](https://github.com/xsaiki-design/c-elegans-behavior-prediction/tree/prototype/accuracy)
  branch (`worms/prototype_accuracy.py`); its sanity check reproduces the headline exactly before testing anything.

## Interview questions you might get

- *Why not just report the best model?* Picking the best of several on the same test data inflates it; the rule and the
  correction were fixed first, and the headline stays the pre-registered one.
- *What is Holm correction?* A way to keep the chance of any false "win" at 5 % when testing several things at once.
- *Why tune inside the training worms?* Choosing settings by test-worm score would leak the test into the model.

## Read more

- Cawley & Talbot 2010, "On over-fitting in model selection and subsequent selection bias in performance evaluation",
  *JMLR* 11. <https://www.jmlr.org/papers/v11/cawley10a.html>
- Holm 1979, "A simple sequentially rejective multiple test procedure", *Scandinavian Journal of Statistics* 6(2).
- scikit-learn, nested cross-validation example: <https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html>
