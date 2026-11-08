# 0004 — Evaluation: leave one worm out, beat a behaviour-only baseline

**Status:** decided (2026-11-08), before any results were looked at

## Decision

- **Test on unseen worms.** Train on 39 labelled worms, test on the 40th, repeat for every worm
  (the same as scikit-learn's `LeaveOneGroupOut` with group = worm). Report the spread over 40 worms, not one pooled number.
- **Model:** logistic regression with scikit-learn's default regularisation, for the headline. Simple, and its weights
  say which neurons it relies on. Anything fancier is labelled exploratory.
- **Headline comparison: brain + body vs body alone.** The question is whether the brain adds anything beyond what the
  body already shows. Brain alone is reported too.
- **Metric:** ROC-AUC per held-out worm (0.5 = guessing, 1.0 = perfect), plus average precision, because
  "reversal starts soon" is the rarer class.
- **Baselines the brain model must beat:**
  1. *Chance:* AUC 0.5.
  2. *Behaviour only:* the same model given only what the body shows — current velocity and time since the last
     reversal. (Head angle was left out: its sign convention differs between recordings, a per-file correction the
     authors document; not worth the risk for a baseline.) **This is the real bar.** Reversal timing isn't random, so timing alone predicts some of them. *(Results note: it's a cool-down, a reversal is less likely right after another; time since the last one alone scores AUC 0.63.)*
- **Compare fairly:** for each worm, brain model AUC vs behaviour-only AUC; test the 40 paired differences
  (Wilcoxon signed-rank).
- **Fix settings in advance.** Horizon, features and model settings are chosen in these documents before looking at
  test results. Any tuning happens inside the 39 training worms only.

## Why

- **Frames are not independent.** Neighbouring frames 0.6 s apart are nearly identical. A random train/test split over
  frames puts near-copies on both sides and gives a falsely high score. Splitting by worm prevents that and answers the
  question that matters: does it work on a new animal?
- **One number hides failure.** 40 per-worm scores show whether it works for most worms or only a few.
- **Without the behaviour baseline, a good score proves nothing about the brain.** If timing alone gets AUC 0.70 and the
  brain model gets 0.72, the brain adds very little.
- **Choosing after looking is the most common way analyses fool themselves.** Writing the plan down first
  (these files, dated in git) is a light form of pre-registration.

## Alternatives considered

- **Random frame split:** inflated, see above.
- **Train and test within the same worm (first half / second half):** a useful secondary result, but answers a weaker
  question.
- **Accuracy as metric:** misleading when classes are unbalanced (always saying "no reversal" scores high).

## Interview questions you might get

- *What is data leakage, and where could it happen here?* Information from the test set reaching training: frame
  splits, scaling with statistics from all worms, choosing the horizon by test score.
- *Why AUC and not accuracy?* AUC doesn't depend on picking a threshold or on class balance.
- *How confident are you in the number?* Show the per-worm spread and the paired test; with 40 worms the error bars are
  real and should be shown.

## Read more

- Roberts et al. 2017 — cross-validation for data with time and group structure; the clearest argument for group splits.
  [doi](https://doi.org/10.1111/ecog.02881)
- Kaufman et al. 2012 — "Leakage in data mining". [doi](https://doi.org/10.1145/2382577.2382579)
- Varoquaux 2018 — "Cross-validation failure: small sample sizes lead to large error bars".
  [doi](https://doi.org/10.1016/j.neuroimage.2017.06.061)
- Glaser et al. 2020 — "Machine learning for neural decoding", practical guide from neuroscience.
  [doi](https://doi.org/10.1523/ENEURO.0506-19.2020)
- Saito & Rehmsmeier 2015 — when precision-recall beats ROC. [doi](https://doi.org/10.1371/journal.pone.0118432)
- scikit-learn user guide, "Cross-validation iterators for grouped data":
  <https://scikit-learn.org/stable/modules/cross_validation.html>
- *An Introduction to Statistical Learning*, Chapter 4 (logistic regression) and Chapter 5 (cross-validation):
  <https://www.statlearning.com>
