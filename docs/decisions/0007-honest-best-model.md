# 0007 — Final accuracy round: an honest number for the best model

**Status:** decided (2026-11-09), before running. This is the last accuracy round (see "Stopping").

## The problem with more rounds

Rounds 0005 and 0006 each picked winners by looking at the 40 held-out worms. Corrections keep any single round honest,
but repeating "try candidates, keep the best" on the same worms slowly turns luck into apparent gains. With 40 animals
and no untouched animals left, the only honest way to go further is to make the choice itself part of what is tested.

## Decision

| | What | How it is chosen |
|---|---|---|
| M0 | Headline model | fixed (the reference) |
| E1 | Boosted trees, settings extended past 0006's edge: 7 or 15 leaves, learning rate 0.01 or 0.03, 300 rounds | 5-fold split of the 39 training worms |
| **E2** | **Selection-aware best model**: inside the 39 training worms, tune the linear model (regularisation 0.0003–0.03) and the trees (E1's settings), try their average, and keep whichever scores best | **everything chosen inside the training worms; the held-out worm only scores the final pick** |

- **E2 is the number to report** as "how accurate a model this search finds", because no choice in it saw the test worm.
- Measures as in 0006: AUC (primary, Wilcoxon over 40 worms vs M0, Holm-corrected over 2 comparisons), average
  precision and alarm precision (share of the riskiest 20 % of moments followed by a reversal within 5 s).

## Grilled before running

- *Isn't E1 just another winner picked on the test worms?* Its settings are tuned inside the training worms, but adding
  it is a choice made after seeing 0006, so it is reported as a check of the "edge of the list" lead only. E2 is the
  honest number.
- *Could E2 look worse than 0006's trees?* Yes. If so, that is the real answer: some of 0006's gain was selection
  luck.
- *Why not new features?* Features are where adaptive fishing hurts most. Model choice is the open question from 0006;
  features stay as pre-registered.
- *Why stop after this?* Each extra round on the same 40 worms costs credibility. A bigger gain now needs new animals
  (another dataset), not more rounds.

## Results (2026-11-09)

| Model | Median AUC | Avg precision | Alarm precision | vs headline (AUC) |
|---|---|---|---|---|
| M0 headline | 0.677 | 0.528 | 0.563 | reference |
| E1 trees, extended settings | 0.710 | 0.583 | 0.604 | +0.029, 32/40, Holm p = 0.00002 |
| **E2 selection-aware best model** | **0.707** | **0.589** | **0.602** | **+0.029, 32/40, Holm p = 0.00002** |

- **The honest number is AUC 0.707** (average precision 0.589): the best model this search finds, with every choice
  made without the held-out worm. It picked trees for 32 worms and the tree + linear average for 8.
- **0006's gain was real, not selection luck:** 0.707 here against 0.711 there. The small drop is the price of honesty.
- **The edge-of-list lead is closed:** extending tree settings changed nothing meaningful (0.710 vs 0.711). The model
  has plateaued around 0.71 with these features and these 40 animals.
- Code: `prototype/accuracy` branch, `worms/prototype_accuracy3.py`; its check reproduces the headline exactly first.

## Stopping

After this round no more accuracy rounds on these 40 worms. The write-up reports E2 as the follow-up result next to
the pre-registered headline.
