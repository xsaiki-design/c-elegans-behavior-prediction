# Predicting C. elegans reversals from whole-brain activity

**Question:** while a worm crawls forward, can its brain activity tell us it is about to reverse, in a worm the model
has never seen?

**Status: in progress, no results yet.** The data pipeline is built and tested; the analysis plan is written down
(and dated in git) before any results, in [`docs/decisions/`](docs/decisions).

## Data

Whole-brain calcium imaging of freely moving *C. elegans* from
[Atanas & Kim et al. 2023, *Cell*](https://doi.org/10.1016/j.cell.2023.07.035): 68 recordings of ~16 minutes,
~140 neurons each, 40 with every neuron named (NeuroPAL). Why this dataset: [0001](docs/decisions/0001-dataset.md).

## Approach (planned)

| Step | Choice | Why |
|---|---|---|
| Target | Reversal starts within the next ~5 s, from forward-moving frames only | [0002](docs/decisions/0002-question.md) |
| Features | Named neuron classes, scaled per worm, plus recent change | [0003](docs/decisions/0003-features-across-worms.md) |
| Test | Leave one worm out; must beat a behaviour-only baseline | [0004](docs/decisions/0004-evaluation.md) |

## Results

*Not yet.* Planned: prediction accuracy vs how far ahead (1–10 s), per-worm spread, and which neurons the model uses.

## Run it

Needs [uv](https://docs.astral.sh/uv/).

```bash
uv sync                            # install the exact package versions
uv run python -m worms.download    # fetch and checksum the data (~570 MB) into data/
uv run pytest                      # tests
```

## Layout

```
worms/data.py       load one worm: traces, reversal labels, time, neuron names
worms/download.py   download + verify the dataset
tests/              tests
docs/decisions/     each design decision: why, alternatives, references
docs/reading-list.md
```

## Limitations

Will be filled in with the results. Known so far: 40 animals is a small sample; the signal is calcium, a slow proxy for
neural activity; only named neurons can be compared across worms.

## How this was built

Built with help from Claude Code (an AI coding assistant). Design decisions and their reasoning are in
`docs/decisions/`.

## Data credit

Data: Atanas, Kim et al., *Cell* 186 (2023), Flavell lab, MIT. Please cite the paper, not this repository.
