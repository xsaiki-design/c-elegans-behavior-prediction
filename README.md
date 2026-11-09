# Predicting C. elegans reversals from whole-brain activity

[![tests](https://github.com/xsaiki-design/c-elegans-behavior-prediction/actions/workflows/tests.yml/badge.svg)](https://github.com/xsaiki-design/c-elegans-behavior-prediction/actions/workflows/tests.yml)
[![The live page: a real worm crawling, its reversal risk, and its neurons](docs/live-demo.gif)](https://xsaiki-design.github.io/c-elegans-behavior-prediction/live/)

**[Try the interactive page](https://xsaiki-design.github.io/c-elegans-behavior-prediction/)**: pick an unseen worm,
watch the model's risk rise before real reversals, and set your own alarm.

**Question:** while a worm crawls forward, can its brain activity tell us it is about to reverse, beyond what its body
already shows, in a worm the model has never seen?

**Answer: yes, modestly.** Predicting a reversal ~5 s ahead, brain + body signals score a median ROC-AUC of **0.68** in
held-out worms vs **0.61** for body signals alone, better in **32 of 40** worms (p = 0.0001). The body's warning fades
within seconds; the brain's lasts at least 10 s.

![How far ahead](figures/horizon_curve.png)

**[Live version](https://xsaiki-design.github.io/c-elegans-behavior-prediction/live/)**: the real worm crawling, its
neurons, and the model running in your browser frame by frame (it checks itself against the offline analysis). Its neuron map puts each neuron at its real position in the head
(OpenWorm) with its real wiring (Cook et al. 2019), and a **Why this risk?** view shows exactly how much each neuron type
and body signal pushes the risk at that moment (the model is linear, so the pushes add up to the risk). A
**Compare** tab races brain + body against body only on the same worm, scored live against its real reversals. The
animation uses worms with clean posture tracking in ≥ 90 % of frames; the remaining glitch frames are blended from the
good frames either side (`worms/showcase_data.py`, display only, the analysis doesn't use posture).

Full write-up: [`docs/writeup.md`](docs/writeup.md) (2–3 pages: method, results, checks, limitations).
Short Q&A: [`docs/faq.md`](docs/faq.md). One-page summary: [`docs/summary.pdf`](docs/summary.pdf).

## Key results

| Signals used | Median AUC, 5 s ahead, unseen worms |
|---|---|
| Body only (speed, head angle, time since last reversal) | 0.61 |
| Brain only (46 named neuron classes) | 0.64 |
| **Brain + body** | **0.68** (better than body in 32/40 worms, p = 0.0001) |

- **Checks:** sliding the brain recording out of sync with behaviour removes the effect (brain alone 0.52, brain + body
  back to 0.61). Stricter scaling gives the same result (0.68, 33/40). Decoding the *current* behaviour is easy (0.89),
  which confirms the pipeline lines up.
- **As an alarm** (same number of alarms for both models): the body is the better *last-second* detector, because the
  worm slows down just before it reverses. With at least 3 s of warning required, the brain model catches more reversals
  in 27 of 40 worms. [Table](docs/writeup.md#as-an-alarm-early-warning-vs-last-second-detection)
- **Which neurons:** AIB rising is the clearest build-up signal. AVA/AVE/RIM look *lower* before reversals, but that
  turns out to be leftover activity from the previous reversal. [Details](docs/writeup.md#results)
- **A stronger model agrees** (exploratory): boosted trees 0.70 vs 0.65, better in 33/40 worms.
- **Accuracy follow-up** (pre-registered, [0005](docs/decisions/0005-accuracy-follow-up.md)): of five fixed candidates,
  only a nonlinear model helps meaningfully (0.70, +0.03, 30/40 worms); longer history and extra body signals don't.
- **Best model, honestly measured** ([0007](docs/decisions/0007-honest-best-model.md)): with every modelling choice made
  without the held-out worm, AUC 0.71 and average precision 0.59 (vs 0.68 / 0.53), better in 32 of 40 worms. Accuracy
  has plateaued there; this was the last accuracy round on these worms.
- **Accuracy follow-up 2** ([0006](docs/decisions/0006-accuracy-follow-up-2.md)): tuned boosted trees reach AUC 0.71
  and average precision 0.59 (vs 0.68 / 0.53), better in 31 of 40 worms.
- **All choices were fixed before any results** and committed in git: [`docs/decisions/`](docs/decisions). One slip
  (head angle missing from the body baseline) was caught in review, fixed and re-run; it's
  [logged](docs/decisions/0004-evaluation.md#correction-log).

<p>
<img src="figures/per_worm.png" width="45%">
<img src="figures/top_neurons.png" width="50%">
</p>

## Data

Whole-brain calcium imaging of freely moving *C. elegans* from
[Atanas & Kim et al. 2023, *Cell*](https://doi.org/10.1016/j.cell.2023.07.035): 40 recordings with every neuron named
(NeuroPAL), ~16 minutes and ~140 neurons each. Why this dataset: [0001](docs/decisions/0001-dataset.md).

## How it works

| Step | Choice | Why |
|---|---|---|
| Target | From forward-moving frames: does a reversal start within ~5 s? | [0002](docs/decisions/0002-question.md) |
| Features | Named neuron classes, scaled per worm, plus recent change | [0003](docs/decisions/0003-features-across-worms.md) |
| Test | Leave one worm out; must beat a body-only baseline | [0004](docs/decisions/0004-evaluation.md) |

## Run it

Needs [uv](https://docs.astral.sh/uv/). About 5 minutes on a laptop. Checked on 2026-11-08: a fresh clone, download and run reproduced
`results/summary.json` exactly.

```bash
uv sync                            # install the exact package versions
uv run python -m worms.download    # fetch and checksum the data (~570 MB) into data/
uv run pytest                      # tests
uv run python -m worms.run         # analysis -> results/summary.json
uv run python -m worms.figures     # figures/ from the results
uv run python -m worms.demo_data   # held-out predictions for the interactive page -> docs/demo-data.json
uv run python -m worms.alarms      # alarm analysis -> results/alarms.json
uv run python -m worms.showcase_data  # typical worms + their held-out models for the live page -> docs/live/
uv run python -m worms.anatomy     # neuron positions + wiring for the live page's map -> docs/live/anatomy.json
```

To view the interactive page locally: `python -m http.server -d docs`, then open http://localhost:8000.

## Layout

```
worms/data.py       load one worm: traces, reversal labels, speed, neuron names, heat-stimulus time
worms/download.py   download + verify the dataset
worms/features.py   prediction target, neuron-class features, body-only baseline features
worms/evaluate.py   leave-one-worm-out scoring
worms/run.py        the pre-set analysis; settings mirror docs/decisions
worms/figures.py    README figures
worms/explore.py    exploratory: a stronger model (boosted trees)
worms/demo_data.py  exports held-out predictions for the interactive page
worms/alarms.py     exploratory: reversals caught with equal alarms, by warning time
docs/index.html     the interactive page (GitHub Pages)
docs/live/          the live page: animation + the model running in the browser
worms/showcase_data.py  exports worms and model weights for the live page
worms/anatomy.py    neuron positions and wiring for the live page's map
tests/              tests
docs/               write-up, decisions with references, reading list
```

## Put it on a website

The pages are static files, so any site can show them. Once GitHub Pages is on (Settings → Pages → Deploy from branch,
`main`, `/docs`), embed the live version with:

```html
<iframe src="https://xsaiki-design.github.io/c-elegans-behavior-prediction/live/" title="Live Worm Forecast"
        width="100%" height="860" style="border:0" loading="lazy"></iframe>
```

Or copy `docs/live/` (two files, about 2 MB) into your own site.

## Next steps

Test whether prediction survives the heat stimulus (a change of state); repeat on a second dataset; try a sequence
model as a pre-registered follow-up.

## Limitations

A modest effect (AUC 0.68 is early warning, not mind reading); one dataset from one lab; only named neurons can be
compared across worms; calcium is a slow proxy for activity; single-neuron scores are associations, not causes. More in
the [write-up](docs/writeup.md#limitations).

## How this relates to the dataset paper

The paper models how each neuron *encodes* ongoing behaviour. This project goes the other way and forward in time: from
the population to an *upcoming* reversal, tested on unseen animals against a body-only baseline. It's a focused
extension of their data, not a new dataset or method. [More](docs/writeup.md#how-this-relates-to-the-dataset-paper)

## How this was built

Built with help from Claude Code (an AI coding assistant). Every design decision, its reasoning and its alternatives are
in [`docs/decisions/`](docs/decisions); the reading list for the concepts is [`docs/reading-list.md`](docs/reading-list.md).

## Data credit

Data: Atanas, Kim et al., *Cell* 186 (2023), Flavell lab, MIT. Please cite the paper, not this repository.
Neuron positions for the live page: [OpenWorm CElegansNeuroML](https://github.com/openworm/CElegansNeuroML) (from the
WormBase Virtual Worm). Wiring: Cook et al., [*Nature* 571 (2019)](https://doi.org/10.1038/s41586-019-1352-7),
corrected July 2020, via OpenWorm's [ConnectomeToolbox](https://github.com/openworm/ConnectomeToolbox).
