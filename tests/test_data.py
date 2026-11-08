import h5py
import numpy as np

from worms.data import load_worm


def make_worm_file(path):
    # 3 frames x 4 neurons; column j holds the value 10*j so columns are easy to tell apart
    with h5py.File(path, "w") as f:
        f["gcamp/trace_array"] = np.array([[0.0, 10, 20, 30]] * 3)
        f["behavior/reversal_vec"] = np.array([0, 1, 1])
        f["timing/timestamp_confocal"] = np.array([100.0, 100.6, 101.2])


def test_neuropal_labels_count_from_one(tmp_path):
    path = tmp_path / "worm.h5"
    make_worm_file(path)
    neuropal = {"idx_neuron-label": {"1": {"label": "AVAL"}, "4": {"label": "RIML"}}}

    worm = load_worm(path, neuropal)

    assert worm.labels == ["AVAL", None, None, "RIML"]
    assert worm.traces[:, worm.labels.index("RIML")].tolist() == [30, 30, 30]


def test_reversals_and_time(tmp_path):
    path = tmp_path / "worm.h5"
    make_worm_file(path)

    worm = load_worm(path)

    assert worm.reversing.tolist() == [False, True, True]
    assert np.allclose(worm.time_s, [0.0, 0.6, 1.2])
    assert worm.labels == [None] * 4
