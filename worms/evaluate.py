"""Leave-one-worm-out testing (see docs/decisions/0004)."""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def leave_one_worm_out(worms: list) -> np.ndarray:
    """worms: list of (features, labels). Returns one ROC-AUC per worm, from a model trained on all the others."""
    aucs = []
    for i, (x_test, y_test) in enumerate(worms):
        if y_test.all() or not y_test.any():
            aucs.append(np.nan)
            continue
        x_train = np.vstack([x for j, (x, _) in enumerate(worms) if j != i])
        y_train = np.concatenate([y for j, (_, y) in enumerate(worms) if j != i])
        model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        model.fit(x_train, y_train)
        aucs.append(roc_auc_score(y_test, model.predict_proba(x_test)[:, 1]))
    return np.array(aucs)
