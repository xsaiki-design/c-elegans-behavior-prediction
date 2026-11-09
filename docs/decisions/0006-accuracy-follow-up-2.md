# 0006 — Second accuracy follow-up: stronger regularisation, tuned trees, and precision

**Status:** decided (2026-11-09), before any of these candidates were run. The headline (0002–0004) is unchanged.

## Why

The first follow-up (0005) left one open lead: tuning always picked the strongest regularisation on its list (0.01), the
edge of the list. It also measured ranking (AUC) but not precision: of the moments a model flags, how many are really
followed by a reversal?

## Candidates

| | Candidate | What changes |
|---|---|---|
| M0 | Headline model | nothing (the reference) |
| D1 | Linear, wider tuning | regularisation picked from 0.0003, 0.001, 0.003, 0.01, 0.03 by 5-fold split of the training worms |
| D2 | Tuned boosted trees | tree size (15 or 31 leaves) and learning rate (0.03 or 0.1) picked the same way |
| D3 | Average of D1 and D2 | the two models' predicted risks averaged |

## Measures

- **Primary: AUC per held-out worm**, compared with M0 by Wilcoxon signed-rank over the 40 worms, Holm-corrected for the
  three comparisons. An improvement needs corrected p < 0.05 and a higher median.
- **Precision, reported for every candidate:** average precision, and alarm precision: the share of a model's riskiest
  20 % of moments (its alarms) that really are followed by a reversal within 5 s.
- Tuning only inside the training worms; the test worm never chooses anything.

## Results (2026-11-09)

| Candidate | Median AUC | Avg precision | Alarm precision | vs headline (AUC) |
|---|---|---|---|---|
| M0 headline | 0.677 | 0.528 | 0.563 | reference |
| D1 linear, wider tuning | 0.677 | 0.531 | 0.553 | +0.004, 25/40, Holm p 0.014: passes, negligible |
| **D2 tuned boosted trees** | **0.711** | **0.589** | 0.601 | **+0.033, 31/40, Holm p < 0.0001** |
| D3 average of D1 and D2 | 0.710 | 0.568 | **0.607** | +0.027, 34/40, Holm p < 0.0001 |

- **Most accurate so far: tuned boosted trees**, +0.033 AUC and +0.06 average precision over the headline.
- **Most consistent: the average of the two**, better in 34 of 40 worms, with the best alarm precision.
- **Wider linear tuning closes 0005's lead**: it settles on 0.001 (38 of 40 worms) and gains almost nothing.
- **New lead:** the trees always chose the smallest, slowest setting (15 leaves, rate 0.03), the edge of the list. A
  further round would have to be pre-registered first.
- Code: [`prototype/accuracy`](https://github.com/xsaiki-design/c-elegans-behavior-prediction/tree/prototype/accuracy)
  branch, `worms/prototype_accuracy2.py`; its check reproduces the headline exactly before testing anything.

## What happens with the result

- If D1 passes, the live page switches to D1. It is still linear, so it still runs exactly in the browser and its "why"
  breakdown stays exact.
- Whatever passes or fails is reported in the write-up, and the headline stays the pre-registered model.
