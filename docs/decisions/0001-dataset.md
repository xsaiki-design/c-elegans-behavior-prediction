# 0001 — Dataset: Atanas & Kim et al. 2023 (Flavell lab), freely moving worms

**Status:** decided (2026-11-08)

## Decision

Use the processed recordings from [Atanas & Kim et al. 2023, *Cell*](https://doi.org/10.1016/j.cell.2023.07.035),
downloaded from [Zenodo record 19388374](https://zenodo.org/records/19388374) (`processed_h5.tar.bz2`, 569 MB)
plus the neuron names (`neuropal_label.json.bz2`). `uv run python -m worms.download` fetches and checks both.

What is in it (checked by loading every file, not taken from the paper):

| | |
|---|---|
| Animals | 68 recordings; **40 have named neurons** (NeuroPAL) |
| Neurons per animal | 105–163 (median 139) |
| Length | ~1,600 frames each, ≈ 16 min |
| Frame rate | ≈ 1.6 frames/s (one frame ≈ 0.6 s) |
| Behaviour | velocity, head angle, body posture, feeding (`pumping`), and `reversal_vec` (1 = crawling backwards) |
| Reversals | ≈ 35–60 per animal, typically 6–10 frames long; 15–55 % of frames are backwards |

## Why this one

- **The worms move freely.** Behaviour is measured, not inferred. In the other well-known dataset
  ([Kato et al. 2015](https://doi.org/10.1016/j.cell.2015.09.034)) worms are held still in a chip and "behaviour"
  is read from motor-neuron activity, which would make "predict behaviour from neurons" partly circular.
- **Neurons have names in 40 animals.** NeuroPAL colours every neuron so it can be identified
  ([Yemini et al. 2021](https://doi.org/10.1016/j.cell.2020.12.012)). Names are what let us line up
  neuron *k* in worm A with the same neuron in worm B, which cross-animal prediction needs (see 0003).
- **Already processed.** Traces are extracted from the images, so the project fits on a laptop (600 MB unpacked).
- **Many animals.** 40 labelled worms give 40 independent test cases, enough to show spread, not one lucky number.

## Alternatives considered

- **Kato et al. 2015 (Zimmer lab):** classic and widely re-analysed, but immobilised worms and only 5 animals.
- **Larval zebrafish (Ahrens lab):** ~100× more neurons, but raw data is huge and neurons can't be matched by name
  across fish. Good as a later "does it generalise?" extension, not a starting point.
- **Raw images (DANDI 000776, ~1 TB):** would mean redoing cell extraction. Out of scope; the question is about
  behaviour, not image processing.

## Things to know about this data

- The neuron-label file was written in Julia, which counts from 1. Index `"5"` means trace column 4 in Python.
  `tests/test_data.py` guards this, and a check on real data confirmed it: AVA (backward command neuron) correlates
  +0.36 with reversing, AVB/RIB (forward neurons) −0.50/−0.60, and shifting labels by one column drops AVA to −0.06.
- Each recording has two halves (`gcamp/idx_splits`). Some recordings in the paper got a heat stimulus partway;
  **open question:** which files, and whether to drop or mark them.
- `trace_array` is the authors' processed signal (normalised fluorescence). How they normalised it matters for
  comparing worms (see 0003). Read the paper's STAR Methods section on trace processing.

## Interview questions you might get

- *Why not just use the bigger zebrafish data?* Because the question needs neurons matched across animals and
  behaviour measured directly; the worm gives both, at a size I can analyse properly.
- *What does the signal actually measure?* Calcium-sensitive fluorescence (GCaMP), a slow proxy for electrical
  activity. Most worm neurons don't spike; they change voltage gradually, and calcium follows that.
- *How do you know the labels are right?* Checked against known biology (AVA vs AVB) and against a deliberately
  shifted control.

## Read more

- Atanas & Kim et al. 2023 — the dataset paper. Read the Summary, Figure 1 (setup) and the methods on trace
  processing and NeuroPAL. [doi](https://doi.org/10.1016/j.cell.2023.07.035)
- Yemini et al. 2021 — how NeuroPAL identifies neurons. Figure 1 is enough. [doi](https://doi.org/10.1016/j.cell.2020.12.012)
- Grienberger & Konnerth 2012 — "Imaging calcium in neurons", the review to understand what the signal is.
  [doi](https://doi.org/10.1016/j.neuron.2012.02.011)
- Chen et al. 2013 — GCaMP6, the indicator family used in these worms. [doi](https://doi.org/10.1038/nature12354)
