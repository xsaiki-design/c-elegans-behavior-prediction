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


MAX_BEND = 1.2  # radians between neighbouring drawn points; tighter than a worm can bend, so it's a tracking glitch
MAX_JUMP = 0.8  # radians of average whole-body change in one frame (0.6 s); more is a tracking jump, not movement
MAX_BAD = 0.10  # showcase worms need clean posture tracking in at least 90% of frames


def _filled(raw):
    """Missing points carried forward from the previous frame, angles continuous along the body and over time."""
    a = raw.copy()
    for t in range(1, len(a)):
        gaps = np.isnan(a[t])
        a[t, gaps] = a[t - 1, gaps]
    return np.unwrap(np.unwrap(np.nan_to_num(a), axis=1), axis=0)


def bad_frames(raw):
    """Frames whose posture can't be trusted: a point missing, an impossible kink, or an impossible whole-body jump."""
    a = _filled(raw)
    kink = (np.abs((np.diff(a, axis=1) + np.pi) % (2 * np.pi) - np.pi) > MAX_BEND).any(axis=1)
    jump = np.r_[0, np.abs(np.diff(a, axis=0)).mean(axis=1)] > MAX_JUMP
    return np.isnan(raw).any(axis=1) | kink | jump


def clean_posture(raw):
    """Body angles fit to animate: bad frames replaced by blending the good frames either side.

    Blends the shape, not raw angles: the mid-body direction plus each bend between neighbouring points. Good frames have
    no bend sharper than MAX_BEND, so no blend of them can, and the mid-body direction is continuous, so nothing spins.
    """
    a, bad = _filled(raw), bad_frames(raw)
    mid = a.shape[1] // 2
    shape = np.column_stack([a[:, mid], (np.diff(a, axis=1) + np.pi) % (2 * np.pi) - np.pi])
    t = np.arange(len(a))
    for _ in range(5):  # a frame can look fine alone but still jump impossibly far from the blended frame before it
        good = np.flatnonzero(~bad)
        s = np.column_stack([np.interp(t, good, shape[good, k]) for k in range(shape.shape[1])])
        out = np.empty_like(a)
        out[:, mid] = s[:, 0]
        for k in range(mid + 1, a.shape[1]):
            out[:, k] = out[:, k - 1] + s[:, k]
        for k in range(mid - 1, -1, -1):
            out[:, k] = out[:, k + 1] - s[:, k + 1]
        jump = np.r_[0, np.abs(np.diff(out, axis=0)).mean(axis=1)] > MAX_JUMP
        if not (jump & ~bad).any():
            break
        bad |= jump
    return out


def posture_and_path(uid, velocity):
    """Body angles (head first, cleaned for drawing) and the head's path in mm."""
    with h5py.File(DATA / "atanas2023" / f"{uid}-data.h5", "r") as f:
        angles = f["behavior/body_angle_absolute"][:, POSTURE_POINTS]
        x, y = f["behavior/zeroed_x_confocal"][:], f["behavior/zeroed_y_confocal"][:]
    angles = clean_posture(angles)
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
    def posture_ok(uid):
        with h5py.File(DATA / "atanas2023" / f"{uid}-data.h5", "r") as f:
            return bad_frames(f["behavior/body_angle_absolute"][:, POSTURE_POINTS]).mean() <= MAX_BAD

    # showcase rule: no heat stimulus, clean posture tracking, then closest to the median improvement (typical, not best)
    candidates = [i for i, u in enumerate(uids) if worms[u].heat_frame is None and posture_ok(u)]
    picked = sorted(candidates, key=lambda i: abs(gain[i] - np.median(gain)))[:N_WORMS]

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
    OUT.write_text(json.dumps({"classes": classes, "change_frames": CHANGE_FRAMES, "horizon_frames": HORIZON, "worms": out}, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1e6:.1f} MB): {[uids[i] for i in picked]}")


if __name__ == "__main__":
    main()
