import numpy as np

from worms.features import reversal_soon


def test_reversal_soon_labels_forward_frames_only():
    #             frame: 0  1  2  3  4  5  6  7  8  9
    reversing = np.array([0, 0, 0, 1, 1, 0, 0, 0, 0, 0], bool)

    usable, soon = reversal_soon(reversing, horizon=2)

    # forward frames whose next 2 frames exist; 3-4 are reversing, 8-9 lack a full horizon
    assert np.flatnonzero(usable).tolist() == [0, 1, 2, 5, 6, 7]
    # the reversal starts at frame 3: within 2 frames of frames 1 and 2, not of frame 0
    assert soon[usable].tolist() == [False, True, True, False, False, False]


from worms.data import Worm
from worms.features import class_activity, with_change


def test_class_activity_scales_each_neuron_then_averages_left_and_right():
    traces = np.array([
        # AVAL AVAR RIML unnamed
        [1.0, 2.0, 0.0, 9.0],
        [2.0, 4.0, 0.0, 9.0],
        [3.0, 6.0, 3.0, 9.0],
    ])
    worm = Worm(traces, None, None, None, labels=None, classes=["AVA", "AVA", "RIM", None])

    x = class_activity(worm, ["AVA", "RIM", "AIB"])

    # z-scores worked by hand: 1,2,3 -> -1.22, 0, 1.22 (AVAR is AVAL doubled, same z); 0,0,3 -> -0.71, -0.71, 1.41
    assert np.allclose(x[:, 0], [-1.2247, 0, 1.2247], atol=1e-4)
    assert np.allclose(x[:, 1], [-0.7071, -0.7071, 1.4142], atol=1e-4)
    assert x[:, 2].tolist() == [0, 0, 0]  # AIB not identified in this worm: filled with its average, 0


def test_with_change_adds_change_over_last_k_frames():
    x = np.array([[1.0], [2.0], [4.0], [7.0]])

    out = with_change(x, k=2)

    assert out[:, 0].tolist() == [1, 2, 4, 7]
    assert np.isnan(out[:2, 1]).all()  # no history yet
    assert out[2:, 1].tolist() == [3, 5]


from worms.features import frames_since_reversal


def test_frames_since_reversal_counts_from_last_backward_frame():
    reversing = np.array([0, 1, 1, 0, 0, 0], bool)

    assert frames_since_reversal(reversing).tolist() == [0, 0, 0, 1, 2, 3]
