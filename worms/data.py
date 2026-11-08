"""Load the Atanas & Kim et al. 2023 whole-brain recordings (one HDF5 file per worm)."""

from dataclasses import dataclass
from pathlib import Path

import h5py
import numpy as np


@dataclass
class Worm:
    traces: np.ndarray  # (frames, neurons) GCaMP activity, as processed by the authors
    reversing: np.ndarray  # (frames,) True while the worm crawls backwards
    time_s: np.ndarray  # (frames,) seconds since the first frame
    labels: list  # one entry per trace column: NeuroPAL name like "AVAL", or None if unidentified


def load_worm(path: Path, neuropal: dict | None = None) -> Worm:
    with h5py.File(path, "r") as f:
        traces = f["gcamp/trace_array"][:]
        reversing = f["behavior/reversal_vec"][:].astype(bool)
        t = f["timing/timestamp_confocal"][:]

    labels = [None] * traces.shape[1]
    for idx, info in (neuropal or {}).get("idx_neuron-label", {}).items():
        labels[int(idx) - 1] = info["label"]  # the source files were written in Julia, which counts from 1
    return Worm(traces, reversing, t - t[0], labels)
