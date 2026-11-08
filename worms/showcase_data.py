"""Export a few worms plus their held-out models for the live page: uv run python -m worms.showcase_data -> docs/live/showcase.json

The page runs the model itself in the browser: it rebuilds the features each frame and applies these weights.
"""

import json
from pathlib import Path

import h5py
import numpy as np

from worms.evaluate import fit_without
from worms.features import class_activity
from worms.run import CHANGE_FRAMES, DATA, HORIZON, common_classes, frames, load_labelled_worms, samples

N_WORMS = 3
POSTURE_POINTS = slice(0, 40, 2)  # head to ~3/4 of the body, every other point (the tail end is often missing)
OUT = Path("docs/live/showcase.json")


def linear_params(fitted) -> dict:
    """Scaler + logistic regression as plain numbers: risk = 1 / (1 + exp(-(((x - mean) / scale) . coef + intercept)))."""
    scaler, logreg = fitted[0], fitted[-1]
    return {"mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
            "coef": logreg.coef_[0].tolist(), "intercept": float(logreg.intercept_[0])}


def risk_from_params(p, x):
    z = ((x - np.array(p["mean"])) / np.array(p["scale"])) @ np.array(p["coef"]) + p["intercept"]
    return 1 / (1 + np.exp(-z))


def posture_and_path(uid, velocity):
    """Body angles (head first) and the head's path in mm, with gaps filled from the previous frame."""
    with h5py.File(DATA / "atanas2023" / f"{uid}-data.h5", "r") as f:
        angles = f["behavior/body_angle_absolute"][:, POSTURE_POINTS]
        x, y = f["behavior/zeroed_x_confocal"][:], f["behavior/zeroed_y_confocal"][:]
    for t in range(1, len(angles)):
        gaps = np.isnan(angles[t])
        angles[t, gaps] = angles[t - 1, gaps]
    angles = np.nan_to_num(angles)
    # stage units -> mm, calibrated so the stage's speed matches the dataset's velocity (mm/s) while crawling forward
    step = np.hypot(np.diff(x), np.diff(y))
    fwd = velocity[:-1] > 0.01
    units_per_mm = np.median(step[fwd]) / np.median(velocity[:-1][fwd] * 0.6)
    return angles, (x - x[0]) / units_per_mm, (y - y[0]) / units_per_mm


def main():
    worms = load_labelled_worms()
    classes = common_classes(worms)
    uids = list(worms)
    per_worm = [samples(w, classes, HORIZON) for w in worms.values()]
    summary = json.loads(Path("results/summary.json").read_text())
    assert summary["worms"] == uids, "results/summary.json is from a different set of worms: re-run worms.run"
    head = summary["curve"][str(HORIZON)]
    gain = np.array(head["brain+body"]["auc"]) - np.array(head["body"]["auc"])
    # showcase rule: recordings without heat, closest to the median improvement (typical, not best)
    no_heat = [i for i, u in enumerate(uids) if worms[u].heat_frame is None]
    picked = sorted(no_heat, key=lambda i: abs(gain[i] - np.median(gain)))[:N_WORMS]

    out = []
    for i in picked:
        uid, w = uids[i], worms[uids[i]]
        models = {name: fit_without([s[name] for s in per_worm], i) for name in ["body", "brain+body"]}
        sets, _, usable = frames(w, classes, HORIZON)
        reference = np.full(len(usable), np.nan)
        reference[usable] = models["brain+body"].predict_proba(sets["brain+body"][usable])[:, 1]
        angles, px, py = posture_and_path(uid, w.velocity)
        r = lambda a, d: np.round(np.asarray(a, float), d).tolist()  # noqa: E731
        out.append({
            "uid": uid,
            "auc": {"body": head["body"]["auc"][i], "brain_body": head["brain+body"]["auc"][i]},
            "seconds_per_frame": round(float(np.median(np.diff(w.time_s))), 4),
            "activity": r(class_activity(w, classes), 3),  # frames x classes, scaled within this worm
            "velocity": r(w.velocity, 4),
            "head_angle": r(w.head_angle, 3),
            "reversing": w.reversing.astype(int).tolist(),
            "posture": r(angles, 3),
            "x_mm": r(px, 4), "y_mm": r(py, 4),
            "models": {name: linear_params(m) for name, m in models.items()},
            "reference_risk": [None if np.isnan(v) else round(float(v), 4) for v in reference],
        })
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"classes": classes, "change_frames": CHANGE_FRAMES, "worms": out}, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB): {[uids[i] for i in picked]}")


if __name__ == "__main__":
    main()
