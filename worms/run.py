"""Run the whole analysis: uv run python -m worms.run   -> results/summary.json (then worms.figures draws it)."""

import json
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

from worms.data import load_worm
from sklearn.metrics import roc_auc_score

from worms.evaluate import leave_one_worm_out
from worms.features import class_activity, frames_since_reversal, reversal_soon, with_change

# Settings fixed in docs/decisions before looking at results. Change them there first, then here.
HORIZON = 8  # frames ahead (~5 s at 1.6 frames/s), the headline           0002
HORIZONS = [2, 4, 8, 12, 16]  # the "how far ahead" curve                  0002
CHANGE_FRAMES = 5  # "is it rising?" window (~3 s)                         0003
MIN_WORMS = 25  # keep neuron classes identified in at least this many worms  0003
STRICT_SCALE_FRAMES = 288  # strict check: scale with the first 3 min only (3 x 60 x 1.6)  0003
GFP_CONTROLS = {"2022-01-07-03", "2022-03-16-01", "2022-03-16-02"}  # GFP is not activity-sensitive: no brain signal
SETS = ["body", "brain", "brain+body"]

DATA = Path("data")


def load_labelled_worms():
    labels = json.loads((DATA / "neuropal_label.json").read_text())["data"]
    return {
        uid: load_worm(DATA / "atanas2023" / f"{uid}-data.h5", labels[uid])
        for uid in sorted(labels)
        if uid not in GFP_CONTROLS
    }


def common_classes(worms) -> list:
    counts = {}
    for w in worms.values():
        for c in {c for c in w.classes if c}:
            counts[c] = counts.get(c, 0) + 1
    return sorted(c for c, n in counts.items() if n >= MIN_WORMS)


def before_heat(worm) -> np.ndarray:
    keep = np.ones(len(worm.reversing), bool)
    if worm.heat_frame is not None:
        keep[worm.heat_frame :] = False  # heat changes behaviour for minutes: use the unheated part only (0002)
    return keep


def samples(worm, classes, horizon, scale_frames=None):
    """Feature sets for one worm, on its usable frames only: body, brain, and both."""
    usable, soon = reversal_soon(worm.reversing, horizon)
    usable &= before_heat(worm)
    body = np.c_[worm.velocity, frames_since_reversal(worm.reversing)]
    brain = with_change(class_activity(worm, classes, scale_frames), CHANGE_FRAMES)
    usable &= ~np.isnan(brain).any(axis=1)
    sets = {"body": body, "brain": brain, "brain+body": np.hstack([brain, body])}
    return {name: (x[usable], soon[usable]) for name, x in sets.items()}


def score(worms, classes, horizon, scale_frames=None):
    per_worm = [samples(w, classes, horizon, scale_frames) for w in worms.values()]
    out = {}
    for name in SETS:
        auc, ap = leave_one_worm_out([s[name] for s in per_worm])
        out[name] = {"auc": auc.tolist(), "ap": ap.tolist(), "rate": [float(s[name][1].mean()) for s in per_worm]}
    return out


def paired_test(a, b):
    """Per-worm improvement of b over a, and Wilcoxon signed-rank p-value."""
    d = np.array(b) - np.array(a)
    d = d[~np.isnan(d)]
    return {"median_gain": float(np.median(d)), "worms_improved": int((d > 0).sum()), "n": len(d),
            "p": float(wilcoxon(d).pvalue)}


def decoding_check(worms, classes):
    """Sanity check only (0002): can the brain tell whether the worm is reversing right now? Should be easy."""
    per_worm = []
    for w in worms.values():
        keep = before_heat(w)
        per_worm.append((class_activity(w, classes)[keep], w.reversing[keep]))
    return leave_one_worm_out(per_worm)[0].tolist()


def neuron_scores(worms, classes):
    """Each feature on its own: median per-worm AUC for predicting a reversal soon (>0.5: higher -> reversal more likely).

    Single-feature scores, not model weights: AVA, AVE and AIB move together, so their weights in a joint model trade off
    arbitrarily and can't be read one by one.
    """
    names = classes + [f"{c} rising" for c in classes]
    per_worm = []
    for w in worms.values():
        x, y = samples(w, classes, HORIZON)["brain"]
        present = [c in w.classes for c in classes] * 2  # a class missing in this worm is all zeros: no score
        if 0 < y.mean() < 1:
            per_worm.append([roc_auc_score(y, x[:, j]) if present[j] else np.nan for j in range(len(names))])
    med = np.nanmedian(per_worm, axis=0)
    return dict(sorted(zip(names, med.tolist()), key=lambda kv: -abs(kv[1] - 0.5)))


def main():
    worms = load_labelled_worms()
    classes = common_classes(worms)
    curve = {h: score(worms, classes, h) for h in HORIZONS}
    head = curve[HORIZON]
    strict = score(worms, classes, HORIZON, STRICT_SCALE_FRAMES)
    summary = {
        "worms": list(worms),
        "classes": classes,
        "headline_horizon": HORIZON,
        "curve": curve,
        "headline_test": paired_test(head["body"]["auc"], head["brain+body"]["auc"]),
        "brain_alone_vs_body": paired_test(head["body"]["auc"], head["brain"]["auc"]),
        "strict_scaling": {**strict, "test": paired_test(strict["body"]["auc"], strict["brain+body"]["auc"])},
        "decoding_check_auc": decoding_check(worms, classes),
        "neuron_scores": neuron_scores(worms, classes),
    }
    Path("results").mkdir(exist_ok=True)
    Path("results/summary.json").write_text(json.dumps(summary, indent=1))

    med = lambda v: np.nanmedian(v)  # noqa: E731
    print(f"{len(worms)} worms, {len(classes)} neuron classes, headline horizon {HORIZON} frames")
    for h, r in curve.items():
        print(f"  horizon {h:2d}: AUC body {med(r['body']['auc']):.3f}  brain {med(r['brain']['auc']):.3f}  "
              f"brain+body {med(r['brain+body']['auc']):.3f}")
    print("headline brain+body vs body:", summary["headline_test"])
    print("brain alone vs body:", summary["brain_alone_vs_body"])
    print("strict scaling, brain+body vs body:", summary["strict_scaling"]["test"],
          f"(median AUC {med(strict['brain+body']['auc']):.3f})")
    print(f"decoding check (reversing now): median AUC {med(summary['decoding_check_auc']):.3f}")
    print("top single signals:", [(k, round(v, 3)) for k, v in list(summary["neuron_scores"].items())[:10]])


if __name__ == "__main__":
    main()
