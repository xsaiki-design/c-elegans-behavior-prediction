import numpy as np

from worms.evaluate import model
from worms.showcase_data import linear_params, risk_from_params


def test_exported_weights_reproduce_the_model_exactly():
    rng = np.random.default_rng(1)
    x = rng.standard_normal((300, 4)) * [1, 5, 0.1, 2] + [0, 3, 1, -1]
    y = x[:, 0] + 0.2 * x[:, 1] + rng.standard_normal(300) > 0.5
    fitted = model().fit(x, y)

    params = linear_params(fitted)

    # the browser applies exactly this formula; it must match scikit-learn's own predictions
    assert np.allclose(risk_from_params(params, x), fitted.predict_proba(x)[:, 1])


from worms.showcase_data import bad_frames, clean_posture


def test_glitch_frames_are_filled_in_from_the_good_frames_around_them():
    bend = np.linspace(0, 0.5, 6)                   # a gentle curve along the body
    raw = np.array([bend + 0.1 * t for t in range(5)])
    raw[1] += 2 * np.pi                             # same shape written one full turn higher: not a glitch
    raw[2, 5] = raw[2, 4] + 2.5                     # tail folded back in one frame: a tracking glitch
    raw[3, 5] = np.nan                              # tail point missing

    assert bad_frames(raw).tolist() == [False, False, True, True, False]
    cleaned = clean_posture(raw)
    assert np.abs(np.diff(cleaned, axis=0)).max() < 0.2                     # smooth over time, no spins
    assert np.abs(np.diff(cleaned, axis=1)).max() < 0.2                     # no kinks along the body
    assert np.allclose(cleaned[2], bend + 0.2, atol=0.05)                   # glitch frame = blend of its neighbours
