"""Turn one worm's recording into prediction samples (see docs/decisions/0002 and 0003)."""

import numpy as np


def reversal_soon(reversing: np.ndarray, horizon: int):
    """For each frame: is it usable (moving forward, full horizon ahead), and does a reversal start within `horizon` frames?"""
    n = len(reversing)
    starts = np.zeros(n, bool)
    starts[1:] = reversing[1:] & ~reversing[:-1]
    # count of starts in frames t+1 .. t+horizon, via a running total
    total = np.concatenate([[0], np.cumsum(starts)])
    t = np.arange(n)
    ahead = total[np.minimum(t + horizon + 1, n)] - total[t + 1]
    usable = ~reversing & (t + horizon < n)
    return usable, ahead > 0


def class_activity(worm, classes: list, scale_frames: int | None = None) -> np.ndarray:
    """(frames, classes): each neuron z-scored within this worm, left/right averaged; a class not found here is 0.

    scale_frames: compute the scaling from only the first N frames (strict check, 0003); default uses the whole recording.
    """
    x = worm.traces
    ref = x[:scale_frames]
    std = ref.std(axis=0)
    z = (x - ref.mean(axis=0)) / np.where(std > 0, std, 1)
    out = np.zeros((len(x), len(classes)))
    for j, c in enumerate(classes):
        cols = [i for i, k in enumerate(worm.classes) if k == c]
        if cols:
            out[:, j] = z[:, cols].mean(axis=1)
    return out


def with_change(x: np.ndarray, k: int) -> np.ndarray:
    """Append each column's change over the last k frames (NaN for the first k frames)."""
    change = np.full_like(x, np.nan)
    change[k:] = x[k:] - x[:-k]
    return np.hstack([x, change])


def frames_since_reversal(reversing: np.ndarray) -> np.ndarray:
    """Frames since the worm was last crawling backwards (since the recording began, before the first reversal)."""
    t = np.arange(len(reversing))
    last = np.maximum.accumulate(np.where(reversing, t, 0))
    return t - last
