"""PROTOTYPE (throwaway): final accuracy round, pre-registered in docs/decisions/0007. Not part of the headline.

E2 makes every choice (settings, and linear vs trees vs their average) inside the 39 training worms, so the held-out
worm only scores the final pick: an honest number for the best model this search finds.
uv run python -m worms.prototype_accuracy3 -> results/accuracy_followup3.json
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from scipy.stats import wilcoxon
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from worms.evaluate import model as headline_model
from worms.run import HORIZON, common_classes, load_labelled_worms, samples

LINEAR = [lambda c=c: make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=2000)) for c in (0.0003, 0.001, 0.003, 0.01, 0.03)]
TREES = [lambda l=l, r=r: HistGradientBoostingClassifier(max_leaf_nodes=l, learning_rate=r, max_iter=300, random_state=0)
         for l in (7, 15) for r in (0.01, 0.03)]
TREE_NAMES = ["7 leaves, 0.01", "7 leaves, 0.03", "15 leaves, 0.01", "15 leaves, 0.03"]


def inner(makers, x, y, folds):
    """Out-of-fold predictions on the training worms for each setting; keep the best by mean per-fold AUC."""
    best = (-1, None, None)
    for k, m in enumerate(makers):
        oof = np.zeros(len(y))
        for tr, va in folds:
            oof[va] = m().fit(x[tr], y[tr]).predict_proba(x[va])[:, 1]
        score = np.mean([roc_auc_score(y[va], oof[va]) for _, va in folds])
        if score > best[0]:
            best = (score, k, oof)
    return best


def one_worm(i, xs, ys):
    xtr = np.vstack([x for j, x in enumerate(xs) if j != i])
    ytr = np.concatenate([y for j, y in enumerate(ys) if j != i])
    g = np.concatenate([np.full(len(y), j) for j, y in enumerate(ys) if j != i])
    folds = list(GroupKFold(5).split(xtr, ytr, g))
    s_lin, k_lin, oof_lin = inner(LINEAR, xtr, ytr, folds)
    s_tree, k_tree, oof_tree = inner(TREES, xtr, ytr, folds)
    s_avg = np.mean([roc_auc_score(ytr[va], (oof_lin[va] + oof_tree[va]) / 2) for _, va in folds])
    lin = LINEAR[k_lin]().fit(xtr, ytr).predict_proba(xs[i])[:, 1]
    tree = TREES[k_tree]().fit(xtr, ytr).predict_proba(xs[i])[:, 1]
    pick = ["linear", "trees", "average"][int(np.argmax([s_lin, s_tree, s_avg]))]
    e2 = {"linear": lin, "trees": tree, "average": (lin + tree) / 2}[pick]
    m0 = headline_model().fit(xtr, ytr).predict_proba(xs[i])[:, 1]
    return {"M0": m0, "E1": tree, "E2": e2}, {"tree": TREE_NAMES[k_tree], "pick": pick}


def alarm_precision(y, p, share=0.2):
    return float(y[p >= np.quantile(p, 1 - share)].mean())


def main():
    worms = load_labelled_worms()
    classes = common_classes(worms)
    per = [samples(w, classes, HORIZON)["brain+body"] for w in worms.values()]
    xs, ys = [s[0] for s in per], [s[1] for s in per]
    out = Parallel(n_jobs=-1)(delayed(one_worm)(i, xs, ys) for i in range(len(xs)))
    names = ["M0", "E1", "E2"]
    auc = {n: [roc_auc_score(ys[i], out[i][0][n]) for i in range(len(xs))] for n in names}
    ap = {n: [average_precision_score(ys[i], out[i][0][n]) for i in range(len(xs))] for n in names}
    prec = {n: [alarm_precision(ys[i], out[i][0][n]) for i in range(len(xs))] for n in names}
    head = json.loads(Path("results/summary.json").read_text())["curve"][str(HORIZON)]["brain+body"]["auc"]
    assert np.allclose(auc["M0"], head, atol=1e-9), "M0 must reproduce the headline exactly"
    tests = {}
    for n in ["E1", "E2"]:
        d = np.subtract(auc[n], auc["M0"])
        tests[n] = {"median_gain": float(np.median(d)), "worms_improved": int((d > 0).sum()), "p": float(wilcoxon(d).pvalue)}
    ps = sorted((tests[n]["p"], n) for n in tests)  # Holm over 2
    tests[ps[0][1]]["p_holm"] = min(1.0, 2 * ps[0][0])
    tests[ps[1][1]]["p_holm"] = min(1.0, max(2 * ps[0][0], ps[1][0]))
    res = {"median": {n: {"auc": float(np.median(auc[n])), "average_precision": float(np.median(ap[n])),
                          "alarm_precision": float(np.median(prec[n]))} for n in names},
           "tests_vs_M0_auc": tests,
           "choices": {"E1_setting": dict(Counter(c["tree"] for _, c in out)), "E2_pick": dict(Counter(c["pick"] for _, c in out))},
           "per_worm": {"auc": auc, "average_precision": ap, "alarm_precision": prec}}
    Path("results/accuracy_followup3.json").write_text(json.dumps(res, indent=1))
    print("M0 reproduces the headline exactly")
    for n in names:
        m, t = res["median"][n], tests.get(n)
        print(f"{n}: AUC {m['auc']:.3f}  avg precision {m['average_precision']:.3f}  alarm precision {m['alarm_precision']:.3f}"
              + (f"  | vs M0 +{t['median_gain']:.4f}, {t['worms_improved']}/40, Holm p {t['p_holm']:.5f}" if t else ""))
    print("choices:", res["choices"])


if __name__ == "__main__":
    main()
