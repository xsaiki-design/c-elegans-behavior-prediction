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
