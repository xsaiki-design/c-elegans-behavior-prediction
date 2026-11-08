import numpy as np

from worms.evaluate import leave_one_worm_out


def test_each_worm_is_scored_by_a_model_that_never_saw_it():
    rng = np.random.default_rng(0)
    worms = []
    for _ in range(4):
        y = rng.random(200) < 0.3
        x = np.c_[y + 0.1 * rng.standard_normal(200), rng.standard_normal(200)]  # column 0 gives the answer away
        worms.append((x, y))

    aucs = leave_one_worm_out(worms)

    assert aucs.tolist() == [1.0, 1.0, 1.0, 1.0]


def test_a_worm_without_any_positive_frames_gets_no_score():
    x = np.arange(10.0)[:, None]
    worms = [(x, x[:, 0] > 4), (x, x[:, 0] > 4), (x, np.zeros(10, bool))]

    aucs = leave_one_worm_out(worms)

    assert aucs[:2].tolist() == [1.0, 1.0]
    assert np.isnan(aucs[2])  # AUC is undefined with one class; reported as missing, not as 0.5
