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
