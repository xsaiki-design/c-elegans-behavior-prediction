"""Run the analysis: uv run python -m worms.run   (add --smoke to check it runs, without showing any scores)."""

import json
import sys
from pathlib import Path

import numpy as np

from worms.data import load_worm
from worms.evaluate import leave_one_worm_out
from worms.features import class_activity, frames_since_reversal, reversal_soon, with_change

# Settings fixed in docs/decisions before looking at results. Change them there first, then here.
HORIZON = 8  # frames ahead (~5 s at 1.6 frames/s)                         0002
CHANGE_FRAMES = 5  # "is it rising?" window (~3 s)                         0003
MIN_WORMS = 25  # keep neuron classes identified in at least this many worms  0003
HEAT = "before"  # heat-stimulated recordings: "before" = frames before the stimulus only, "drop", or "keep"
GFP_CONTROLS = {"2022-01-07-03", "2022-03-16-01", "2022-03-16-02"}  # GFP is not activity-sensitive: no brain signal

DATA = Path("data")


def load_labelled_worms():
    labels = json.loads((DATA / "neuropal_label.json").read_text())["data"]
    worms = {}
    for uid in sorted(labels):
        if uid in GFP_CONTROLS:
            continue
        worm = load_worm(DATA / "atanas2023" / f"{uid}-data.h5", labels[uid])
        if worm.heat_frame is not None and HEAT == "drop":
            continue
        worms[uid] = worm
    return worms


def common_classes(worms) -> list:
    counts = {}
    for w in worms.values():
        for c in {c for c in w.classes if c}:
            counts[c] = counts.get(c, 0) + 1
    return sorted(c for c, n in counts.items() if n >= MIN_WORMS)


def samples(worm, classes, horizon):
    """Feature sets for one worm, on its usable frames only: body, brain, and both."""
    usable, soon = reversal_soon(worm.reversing, horizon)
    if worm.heat_frame is not None and HEAT == "before":
        usable[worm.heat_frame :] = False
    body = np.c_[worm.velocity, frames_since_reversal(worm.reversing)]
    brain = with_change(class_activity(worm, classes), CHANGE_FRAMES)
    usable &= ~np.isnan(brain).any(axis=1)
    sets = {"body": body, "brain": brain, "brain+body": np.hstack([brain, body])}
    return {name: (x[usable], soon[usable]) for name, x in sets.items()}


def run(horizon=HORIZON, worms=None):
    worms = worms or load_labelled_worms()
    classes = common_classes(worms)
    per_worm = {uid: samples(w, classes, horizon) for uid, w in worms.items()}
    scores = {
        name: leave_one_worm_out([per_worm[uid][name] for uid in worms]).tolist()
        for name in ["body", "brain", "brain+body"]
    }
    return {"horizon": horizon, "worms": list(worms), "classes": classes, "auc": scores}


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        worms = load_labelled_worms()
        classes = common_classes(worms)
        s = samples(next(iter(worms.values())), classes, HORIZON)
        print(f"{len(worms)} worms, {len(classes)} neuron classes; first worm brain features {s['brain'][0].shape}, "
              f"{s['brain'][1].mean():.0%} of usable frames have a reversal coming")
        sys.exit()
    result = run()
    Path("results").mkdir(exist_ok=True)
    Path(f"results/horizon_{HORIZON}.json").write_text(json.dumps(result, indent=1))
    for name, aucs in result["auc"].items():
        print(f"{name:11s} median AUC over held-out worms: {np.nanmedian(aucs):.2f}")
