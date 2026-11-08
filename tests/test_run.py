import numpy as np

from worms.data import Worm
from worms.run import before_heat


def test_before_heat_also_drops_frames_whose_prediction_window_reaches_the_heat():
    worm = Worm(None, np.zeros(8, bool), None, None, labels=None, classes=None, heat_frame=5)

    # horizon 2: frame 2 looks at frames 3-4 (unheated, kept); frame 3 would look at frame 5 (heated, dropped)
    assert np.flatnonzero(before_heat(worm, horizon=2)).tolist() == [0, 1, 2]


def test_before_heat_keeps_everything_without_a_stimulus():
    worm = Worm(None, np.zeros(4, bool), None, None, labels=None, classes=None)

    assert before_heat(worm, horizon=2).all()
