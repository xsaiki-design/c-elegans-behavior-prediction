# Questions and answers

## In 30 seconds

I took a public whole-brain imaging dataset of freely moving *C. elegans* and asked whether the brain shows a reversal
coming before the body does. Testing on worms the model never saw, adding brain activity to body signals raised the
AUC from 0.61 to 0.68, better in 32 of 40 worms. The body's warning fades within a few seconds; the brain's lasts longer.
I wrote the analysis plan down and committed it before computing any results, and logged the one deviation.

## Numbers to know

| | |
|---|---|
| Data | 40 worms with named neurons (NeuroPAL), ~16 min each, ~1.6 frames/s, 46 neuron classes used |
| Headline | brain + body AUC 0.68 vs body 0.61, 5 s ahead, 32/40 unseen worms, p = 0.0001 |
| Brain alone | 0.64 (not significantly better than body alone) |
| Time-shift control | brain slid out of sync: brain alone 0.52, brain + body 0.61, advantage gone |
| Alarm framing | same number of alarms: body wins at the last second; brain wins with ≥ 1.8–3 s of warning |
| Decoding sanity check | "reversing now?" AUC 0.89 |

## Common questions

**Why predict reversals, not decode current behaviour?** Decoding is nearly circular: AVA's activity is the reversal
command, so of course it decodes. Predicting a few seconds ahead asks whether the decision is visible before the movement.

**Why leave one worm out?** Frames 0.6 s apart are near copies, so a random split puts near-duplicates in train and test
and inflates the score. Holding out whole animals is also the claim that matters: does it work on a new individual?

**Why a body-only baseline?** Reversal timing isn't random (there's a cool-down after each one) and the worm slows just
before reversing. A brain model that only beats chance could be learning that. The question is what the brain adds.

**How did you line up neurons across worms?** Only by name. NeuroPAL colour-codes neurons so they can be identified; I
used the 46 classes named in at least 25 of 40 worms, averaged left/right, and scaled each neuron within its worm.

**What's the most interesting finding?** Two. The brain's information lasts further ahead than the body's. And AVA, the
classic reversal neuron, is *lower* before reversals: it's still winding down from the previous one, so its level is a
timing signal. AIB rising is the real build-up signal.

**How do you know it isn't an artefact?** Shifting the brain recording out of sync with behaviour removes the effect;
stricter scaling and a stronger model give the same answer; shifting neuron labels by one column kills the AVA signal.

**What went wrong?** The first results run left head angle out of the body baseline, against my written plan. A review
caught it; I restored it, re-ran, and logged it. The result held. Also, the "alarm" analysis showed the brain model loses
at last-second detection, which I report rather than hide.

**Limitations?** Modest effect (0.68 is early warning, not mind reading); one dataset from one lab; only named neurons;
calcium is a slow proxy for activity; single-neuron scores are associations.

**What would you do next?** Test after the heat stimulus (does prediction survive a state change?); try a second dataset;
model time properly (a sequence model) as a pre-registered follow-up rather than a fishing trip.

**Was AI used?** Yes, Claude Code helped write the code. Every design choice, its reasoning and its alternatives are in
[`docs/decisions/`](decisions).
