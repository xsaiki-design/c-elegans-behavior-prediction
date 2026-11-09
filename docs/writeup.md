# Whole-brain activity gives early warning of reversals in unseen worms

*Write-up, 2026-11. Code and decisions: this repository. Data: Atanas & Kim et al. 2023.*

## Question

While a *C. elegans* worm crawls forward, does its whole-brain activity show that it is about to reverse, beyond what its
body already shows, in an animal the model has never seen?

## Answer

**Yes, modestly.** Predicting whether a reversal starts in the next ~5 s, a model using brain activity plus body signals
scored a median ROC-AUC of **0.68** in held-out worms, against **0.61** for body signals alone. It did better in
**32 of 40** worms (median gain +0.06, Wilcoxon signed-rank p = 0.0001). The early warning from the body fades within a
few seconds; the brain's stays above chance at least 10 s ahead.

![How far ahead](../figures/horizon_curve.png)

## Data

Whole-brain GCaMP imaging of freely moving worms ([Atanas & Kim et al. 2023](https://doi.org/10.1016/j.cell.2023.07.035)),
processed traces from [Zenodo](https://zenodo.org/records/19388374). 40 recordings have NeuroPAL neuron identities; those
are the ones used. ~16 min each at ~1.6 frames/s, ~140 neurons per worm. 18 of the 40 received a heat stimulus partway;
only frames whose 5-second window ends before it are used. Details and caveats: [decision 0001](decisions/0001-dataset.md).

## Method

All choices below were written down and committed before any results were computed (decisions
[0002](decisions/0002-question.md), [0003](decisions/0003-features-across-worms.md), [0004](decisions/0004-evaluation.md)).

- **Samples:** every frame where the worm is moving forward. **Label:** does a reversal start within the next 8 frames
  (≈ 5 s)? A median 35 % of frames say yes (17–64 % across
  worms).
- **Brain features:** the 46 neuron classes named in at least 25 of 40 worms, each neuron z-scored within its worm,
  left/right averaged; plus each class's change over the last ~3 s. Classes not found in a worm are set to its average (0).
- **Body features:** current velocity, head angle (sign made consistent across recordings using the authors' dataset
  list) and time since the last reversal.
- **Model:** logistic regression, scikit-learn defaults.
- **Test:** leave one worm out: train on 39, score the 40th, for every worm. ROC-AUC and average precision per worm.
- **Headline comparison:** brain + body vs body alone, paired over worms.

## Results

| Signals used | Median AUC, 5 s ahead | Median average precision | Notes |
|---|---|---|---|
| Body only | 0.61 | 0.50 | velocity, head angle, time since last reversal |
| Brain only | 0.64 | 0.48 | not significantly better than body alone (25 of 40 worms, p = 0.22) |
| **Brain + body** | **0.68** | **0.53** | AUC better than body in 32 of 40 worms, p = 0.0001 |

Average precision (chance ≈ 0.34, the share of "reversal coming" frames) shows a smaller gain: better in 26 of 40 worms.
The brain helps most with *ranking* moments by risk, less with picking out the highest-risk moments cleanly.

![Per worm](../figures/per_worm.png)

**How far ahead (figure above).** At 1 s ahead the body is already a strong predictor (AUC 0.81): the worm slows
before it reverses (slowing alone scores 0.82). Its value drops fast, to near chance (0.52) at ~10 s. Brain-only accuracy falls much less, from
0.70 to 0.63. Brain information about an upcoming reversal seems to build up over several seconds, ahead of anything
visible in the body.

**Which signals (figure below).** Scoring each signal on its own:

- **AIB rising** (AUC 0.57) is the clearest build-up signal: AIB is an interneuron known to promote reversals
  ([Gray et al. 2005](https://doi.org/10.1073/pnas.0409009101)), and its activity climbs in the seconds before a reversal.
  RME, I3 and AUA are also slightly higher (0.57–0.58).
- **AVA, AVE and RIM are *lower* before a reversal** (0.42), which looks backwards for "reversal neurons". The data
  explains it: their level mostly tracks time since the *previous* reversal (rank correlation −0.67 for AVA). They're
  still winding down after one, and another reversal is unlikely that soon. Away from recent reversals (≥ 9 s), AVA
  alone is near chance (0.47). So their low level is mostly a timing signal, not a decision signal.
- Lesson for reading these scores: a single neuron's score mixes "what's coming" with "what just happened".

![Top neurons](../figures/top_neurons.png)

**Checks.**
- *Pipeline sanity (decoding):* telling whether the worm is reversing *right now* from brain activity gives AUC 0.89. As
  expected it's easy, which shows the features and labels line up. It isn't the finding.
- *Stricter scaling:* scaling each neuron with only the first 3 minutes (no information from later frames) gives the same
  answer: AUC 0.68, better in 33 of 40 worms, p < 0.0001.
- *Time-shift control:* sliding each worm's brain recording at least 2 minutes out of line with its behaviour removes
  the effect. Brain alone drops to chance (AUC 0.52) and brain + body falls to body-alone level (0.61, better in only
  16 of 40 worms). The brain's contribution depends on its timing matching behaviour, not on something static about
  each worm.
- *Stronger model (exploratory, not pre-planned):* gradient-boosted trees reach 0.70 with brain + body vs 0.65 with
  body alone, better in 33 of 40 worms (`worms/explore.py`). The finding doesn't depend on the simple model.
- *Label alignment:* AVA correlates with reversing (+0.36) and the forward neurons AVB and RIB against it (−0.50, −0.60);
  shifting labels by one column removes this (−0.06).

## As an alarm: early warning vs last-second detection

*Exploratory, added after the headline results (`worms/alarms.py`).* AUC scores every moment. A practical question is
different: if each model raises the same number of alarms, how many reversals does it warn of? Each model alarms on its
own riskiest 20 % of a worm's moments (other budgets in `results/alarms.json` show the same pattern):

| Warning required before the reversal | Body only catches | Brain + body catches | Brain + body catches more in |
|---|---|---|---|
| any (≥ 0.6 s) | **86 %** | 71 % | 4 of 40 worms (fewer in 31) |
| ≥ 1.8 s | 42 % | **46 %** | 23 of 40 (fewer in 13) |
| ≥ 3 s | 31 % | **36 %** | 27 of 40 (fewer in 11) |

The body is the better last-second detector: the worm slows down just before it reverses, and speed shows that. Once
real advance warning is required, the brain model catches more. This is the same story as the "how far ahead" curve,
told as an alarm, and it is the honest answer to "is the brain model better?": for early warning, yes; for
last-moment detection, no. The interactive page lets you change both settings.

## Accuracy follow-up

*Pre-registered separately before running ([decision 0005](decisions/0005-accuracy-follow-up.md)); the headline above is
unchanged.* Five fixed candidates, each tested on unseen worms, with tuning only inside the training worms and a
Holm correction for testing five things at once:

| Candidate | Median AUC, unseen worms | Better than M0 in | Holm-corrected p | Counts as an improvement |
|---|---|---|---|---|
| M0 headline | 0.677 | – | – | reference |
| C1 tuned regularisation | 0.678 | 29 of 40 | 0.010 | yes, but negligible (+0.0006) |
| C2 longer history | 0.683 | 18 of 40 | 0.51 | no |
| C3 body history (both models) | 0.682 | 23 of 40 | 0.15 | no |
| **C4 gradient-boosted trees** | **0.697** | **30 of 40** | **0.0006** | **yes (+0.03)** |
| C5 combination of passing (C1 + C4) | 0.697 | 30 of 40 | 0.0006 | same as C4 (tuning C doesn't apply to trees) |

Only a nonlinear model gives a meaningful gain (+0.03). Longer neural history and extra body history don't help; tuning
the linear model barely moves it. With the stronger model on both sides, the brain still beats the body alone
(0.70 vs 0.65, 33 of 40 worms). Picking the best of several candidates on the same worms makes its number slightly
optimistic, which is why the pre-registered model stays the headline.

## Accuracy follow-up 2

*Pre-registered before running ([decision 0006](decisions/0006-accuracy-follow-up-2.md)).* Alarm precision is the
share of a model's riskiest 20 % of moments really followed by a reversal within 5 s.

| Candidate | Median AUC | Avg precision | Alarm precision | vs headline (AUC) |
|---|---|---|---|---|
| M0 headline | 0.677 | 0.528 | 0.563 | reference |
| D1 linear, wider tuning | 0.677 | 0.531 | 0.553 | +0.004, 25/40, Holm p 0.014: passes, negligible |
| **D2 tuned boosted trees** | **0.711** | **0.589** | 0.601 | **+0.033, 31/40, Holm p < 0.0001** |
| D3 average of D1 and D2 | 0.710 | 0.568 | **0.607** | +0.027, 34/40, Holm p < 0.0001 |

Tuned boosted trees are the most accurate model so far (AUC 0.71, average precision 0.59). As planned, the live page now
uses the tuned linear model (D1): its gain is negligible, but it stays linear, so it runs exactly in the browser and its
"why" breakdown stays exact.

## Limitations

- **The effect is modest.** AUC 0.68 means the model ranks a "reversal coming" moment above a "no reversal" moment 68 %
  of the time. It's useful early warning, not mind reading.
- **One dataset, one lab, one microscope.** Whether it holds elsewhere is untested.
- **Only named neurons.** About a third of each worm's neurons have no name and can't be matched across animals, so
  they're unused. Missing classes are filled with an average, which hides some differences between worms.
- **Calcium is a slow proxy** for neural activity. Its delay works against early warning, so if anything the lead time
  is underestimated.
- **Single-signal scores show association, not cause.** A neuron that rises before reversals may be reacting to the
  same inputs rather than driving the decision.
- **Heat-stimulated worms contribute fewer frames** (before the stimulus only), so they weigh less.
- **Labels come from the authors' pipeline.** Their reversal labels contain some 1–2-frame forward gaps inside reversals,
  which count here as new reversal starts (118 across all worms). These are easy for the body baseline, so if anything
  they shrink the brain's advantage.
- **One pre-planned model.** A stronger model was tried only as an exploratory extra (above).
- **One correction after the first results run:** head angle had been left out of the body baseline, against the plan.
  It was restored and everything re-run; the numbers here use the planned baseline
  ([correction log](decisions/0004-evaluation.md#correction-log)).

## How this relates to the dataset paper

Atanas & Kim et al. 2023 asked how each neuron *encodes* behaviour. They modelled each neuron's activity as a function of
the worm's ongoing behaviour (velocity, head curvature, feeding), mapping which neurons represent what, over which
timescales, and how that changes with state. This project goes the other way and forward in time: from the population
to an *upcoming* behavioural event. It tests that on unseen animals against a body-only baseline, to measure how much
early warning the brain adds. The finding that brain information outlasts body information fits their multi-timescale
picture; it is a small, focused extension of their data, not a new dataset or method. *(The comparison is based on the
paper's summary; check its decoding analyses before claiming that nobody has done this.)*

## How this was built

Code written with help from Claude Code (an AI coding assistant). Every design decision, with its reasoning and the
alternatives, is in [`docs/decisions/`](decisions); the plan was committed to git before results were computed, and
the one deviation is logged.
