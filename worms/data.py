"""Load the Atanas & Kim et al. 2023 whole-brain recordings (one HDF5 file per worm)."""

from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np


@dataclass
class Worm:
    traces: np.ndarray  # (frames, neurons) GCaMP activity, as processed by the authors
    reversing: np.ndarray  # (frames,) True while the worm crawls backwards
    velocity: np.ndarray  # (frames,) forward speed; negative when reversing
    time_s: np.ndarray  # (frames,) seconds since the first frame
    labels: list  # one entry per trace column: NeuroPAL name like "AVAL", or None if unidentified
    classes: list  # same, but the neuron class like "AVA" (taken from the file: "AVL" is its own class, not "AV" + L)
    heat_frame: int | None = None  # frame a heat stimulus began, if this recording had one


def load_worm(path: Path, neuropal: dict | None = None) -> Worm:
    with h5py.File(path, "r") as f:
        traces = f["gcamp/trace_array"][:]
        reversing = f["behavior/reversal_vec"][:].astype(bool)
        velocity = f["behavior/velocity"][:]
        t = f["timing/timestamp_confocal"][:]
        heat = f["timing/stim_begin_confocal"][()] if "timing/stim_begin_confocal" in f else None

    labels = [None] * traces.shape[1]
    classes = [None] * traces.shape[1]
    for idx, info in (neuropal or {}).get("idx_neuron-label", {}).items():
        col = int(idx) - 1  # the source files were written in Julia, which counts from 1
        labels[col], classes[col] = info["label"], info.get("neuron_class")
    heat_frame = None if heat is None else int(np.ravel(heat)[0]) - 1  # 1-based in the file, like the labels
    return Worm(traces, reversing, velocity, t - t[0], labels, classes, heat_frame)
