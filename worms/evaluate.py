"""Leave-one-worm-out testing (see docs/decisions/0004)."""

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def model():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))


def leave_one_worm_out(worms: list):
    """worms: list of (features, labels). Returns ROC-AUC and average precision per worm, each from a model trained on all the others."""
    aucs, aps = [], []
    for i, (x_test, y_test) in enumerate(worms):
        if y_test.all() or not y_test.any():
            aucs.append(np.nan)
            aps.append(np.nan)
            continue
        x_train = np.vstack([x for j, (x, _) in enumerate(worms) if j != i])
        y_train = np.concatenate([y for j, (_, y) in enumerate(worms) if j != i])
        p = model().fit(x_train, y_train).predict_proba(x_test)[:, 1]
        aucs.append(roc_auc_score(y_test, p))
        aps.append(average_precision_score(y_test, p))
    return np.array(aucs), np.array(aps)
