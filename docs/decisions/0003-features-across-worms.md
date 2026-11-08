# 0003 — Features: named neuron classes, scaled per worm

**Status:** proposed — review before the analysis is built

## Decision

1. **Use only named neurons, grouped by class.** Average left/right pairs (AVAL + AVAR → AVA). Keep classes found in at
   least ~25 of the 40 labelled worms (this keeps RIM, found in 28, but drops AVB, found in only 11). Where a worm is missing a class, fill with 0 (= that worm's average, after step 2).
2. **Scale each neuron within its own worm** (z-score: subtract its mean, divide by its spread).
3. **Give the model a little history:** each class's current value plus its change over the last ~3 s
   (is AVA *rising*?), not just a snapshot.

## Why

- **The column problem.** Column 12 in worm A is not the same cell as column 12 in worm B. Unlabelled neurons can't be
  lined up across animals at all. Names (from NeuroPAL) are the only reliable bridge, so the feature set is "AVA, AIB,
  RIM, …", identical in every worm. This is what makes a cross-animal test possible.
- **Left/right averaging** halves the missing-data problem (often only one side was identified) and the pairs usually
  behave alike.
- **Scaling per worm** removes differences that are about the microscope or the animal's brightness, not the brain.
  Without it the model can learn "worm 7 is brighter", which doesn't transfer.
- **History** matters because a decision builds up: a rising signal says more than its current level.

## The honest caveat

Z-scoring a held-out worm uses that worm's whole recording to compute its mean, so a little information from later
frames leaks into earlier ones. It doesn't use any labels, and the model never sees the test worm during training, so
the effect is small. A stricter version scales using only the first few minutes. **Mention this in the write-up**; it
is exactly the kind of detail an interviewer probes.

## Alternatives considered

- **PCA per worm, then use the top components:** the components point in different directions in each worm, so
  "component 1" doesn't mean the same thing across animals. Would need an alignment step (e.g. CCA); more complex,
  harder to interpret.
- **All ~140 neurons without names:** impossible to line up across animals.
- **Nonlinear model on raw traces (deep learning):** 40 animals is too little data; would be hard to tell what it learned.

## Interview questions you might get

- *Why not use every neuron?* Unnamed neurons have no counterpart in the next worm, so they can't help a model that
  must work on a new animal.
- *What does z-scoring fix, and what does it cost?* Fixes brightness/expression differences; costs absolute level
  information, and leaks a little future information within a worm (see caveat).
- *How would you handle missing neurons better?* Indicator features, or models trained per available subset; worth
  trying only if missing data turns out to matter.

## Read more

- Cunningham & Yu 2014 — "Dimensionality reduction for large-scale neural recordings". Why PCA axes are per-dataset.
  [doi](https://doi.org/10.1038/nn.3776)
- Yemini et al. 2021 — NeuroPAL, for why names are reliable. [doi](https://doi.org/10.1016/j.cell.2020.12.012)
- James, Witten, Hastie & Tibshirani, *An Introduction to Statistical Learning* — free at <https://www.statlearning.com>.
  Chapter 6 (regularisation) and Chapter 12 (PCA).
