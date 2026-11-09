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

## What happens with the result

- If D1 passes, the live page switches to D1. It is still linear, so it still runs exactly in the browser and its "why"
  breakdown stays exact.
- Whatever passes or fails is reported in the write-up, and the headline stays the pre-registered model.
