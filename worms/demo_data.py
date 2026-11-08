"""Export held-out predictions for the interactive page: uv run python -m worms.demo_data -> docs/demo-data.json"""

import json
from pathlib import Path

import numpy as np

from worms.evaluate import fit_without
from worms.run import HORIZON, common_classes, frames, load_labelled_worms, samples

SHOWN_NEURONS = ["AIB", "AVA", "AVE", "RIM", "RME"]  # the signals discussed in docs/writeup.md
OUT = Path("docs/demo-data.json")


def runs(mask: np.ndarray) -> list:
    """[start, end) frame pairs where mask is True."""
    edges = np.flatnonzero(np.diff(np.r_[0, mask.astype(int), 0]))
    return edges.reshape(-1, 2).tolist()


def rounded(x, digits):
    return [None if np.isnan(v) else round(float(v), digits) for v in x]


def main():
    worms = load_labelled_worms()
    classes = common_classes(worms)
    uids = list(worms)
    per_worm = [samples(w, classes, HORIZON) for w in worms.values()]
    # per-worm AUCs from the analysis itself, so the page can't drift from the README
    summary = json.loads(Path("results/summary.json").read_text())
    assert summary["worms"] == uids, "results/summary.json is from a different set of worms: re-run worms.run"
    head = summary["curve"][str(HORIZON)]
    out = []
    for i, uid in enumerate(uids):
        w = worms[uid]
        sets, _, usable = frames(w, classes, HORIZON)
        risk = {}
        for name in ["body", "brain+body"]:
            m = fit_without([s[name] for s in per_worm], i)  # never saw this worm
            p = np.full(len(usable), np.nan)
            p[usable] = m.predict_proba(sets[name][usable])[:, 1]
            risk[name] = rounded(p, 3)
        brain = sets["brain"]
        out.append({
            "uid": uid,
            "auc": {"body": head["body"]["auc"][i], "brain_body": head["brain+body"]["auc"][i]},
            "seconds_per_frame": round(float(np.median(np.diff(w.time_s))), 4),
            "heat_frame": w.heat_frame,
            "reversals": runs(w.reversing),
            "velocity": rounded(w.velocity, 4),
            "risk_body": risk["body"],
            "risk_brain_body": risk["brain+body"],
            "neurons": {c: rounded(brain[:, classes.index(c)], 2) for c in SHOWN_NEURONS if c in w.classes},
        })
    OUT.write_text(json.dumps({"horizon_frames": HORIZON, "worms": out}, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB, {len(out)} worms)")


if __name__ == "__main__":
    main()
