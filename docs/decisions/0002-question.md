# 0002 — The question: can brain activity predict a reversal before it starts?

**Status:** proposed — review before the analysis is built

## Decision

> While a worm is crawling forward, can its whole-brain activity predict that it will **start a reversal within
> the next ~5 seconds** — in a worm the model has never seen?

- One sample = one frame where the worm is moving forward.
- Label = 1 if a reversal starts in the next 8 frames (≈ 5 s), else 0.
- Frames already in a reversal are left out: there is nothing to predict, the worm is already doing it.

## Why this framing (the key idea)

There are two very different questions that both sound like "predict behaviour from the brain":

1. **Decoding:** *is the worm reversing right now?* This is easy and close to circular: AVA is the neuron that drives
   reversals, so its activity *is* the reversal. High accuracy here proves little.
2. **Prediction:** *will it reverse soon, given it is going forward now?* This asks whether the brain shows the
   decision building up before the movement. That is the interesting question, and it can fail, which makes a
   positive answer worth something.

Reversals are the right behaviour to pick: discrete, frequent (≈ 50 per worm), easy to label, and the worm's main
way to change direction, with a well-studied circuit (AIB, RIM, AVA, AVE; [Gray et al. 2005](https://doi.org/10.1073/pnas.0409009101);
[Gordus et al. 2015](https://doi.org/10.1016/j.cell.2015.02.018)).

## The best result figure

Repeat the prediction with different horizons (1, 2, 4, 8, 16 frames ahead) and plot accuracy against horizon.
"How far ahead can we see it coming?" is one clear picture with a clear answer, even if the answer is "only ~1 s".

## Alternatives considered

- **Predict velocity (a continuous number):** done well by [Hallinen et al. 2021](https://doi.org/10.7554/eLife.66135),
  mostly within the same animal. Less crisp to explain than "sees the reversal coming".
- **"Does activity collapse onto a few patterns?" (PCA):** already shown ([Kato et al. 2015](https://doi.org/10.1016/j.cell.2015.09.034));
  no single answer to test.
- **"Same neurons, same job across animals?":** good, but becomes part of this project anyway when we look at which
  neurons the model relies on.

## Open choices (decide before running, not after)

- Horizon for the headline number: 8 frames (≈ 5 s) proposed.
- Whether to also skip a short gap after each reversal ends (the worm often turns, then goes forward).

## Interview questions you might get

- *Why isn't 95 % accuracy on "is it reversing" impressive?* Because the input contains the answer (AVA). Prediction
  ahead of time is the real test.
- *What counts as success?* Beating a behaviour-only baseline in held-out worms (see 0004). Failing to beat it is
  also a result: it would mean the brain gives no early warning beyond what the body already shows.

## Read more

- Gray, Hill & Bargmann 2005 — the reversal/turning circuit. [doi](https://doi.org/10.1073/pnas.0409009101)
- Gordus et al. 2015 — why the same input sometimes causes a reversal and sometimes not (AIB/RIM/AVA network state).
  [doi](https://doi.org/10.1016/j.cell.2015.02.018)
- Kato et al. 2015 — whole-brain dynamics follow the forward → reverse → turn sequence. Figures 1–3.
  [doi](https://doi.org/10.1016/j.cell.2015.09.034)
- Hallinen et al. 2021 — decoding locomotion in moving worms; note how they handle across-animal tests.
  [doi](https://doi.org/10.7554/eLife.66135)
- WormAtlas — look up AVA, AVB, AIB, RIM by name: <https://www.wormatlas.org>
