"""PROTOTYPE (throwaway): second accuracy follow-up, pre-registered in docs/decisions/0006. Not part of the headline.

uv run python -m worms.prototype_accuracy2 -> results/accuracy_followup2.json
"""

import json
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
TREES = [lambda l=l, r=r: HistGradientBoostingClassifier(max_leaf_nodes=l, learning_rate=r, max_iter=200, random_state=0)
         for l in (15, 31) for r in (0.03, 0.1)]


def tuned(makers, xs, ys):
    """Pick a setting by 5-fold grouped CV over the training worms only, then refit on all of them."""
    x, y = np.vstack(xs), np.concatenate(ys)
    g = np.concatenate([np.full(len(v), i) for i, v in enumerate(ys)])
    score = [np.mean([roc_auc_score(y[va], m().fit(x[tr], y[tr]).predict_proba(x[va])[:, 1])
                      for tr, va in GroupKFold(5).split(x, y, g)]) for m in makers]
    k = int(np.argmax(score))
    return makers[k]().fit(x, y), k


def one_worm(i, xs, ys):
    xtr, ytr = [x for j, x in enumerate(xs) if j != i], [y for j, y in enumerate(ys) if j != i]
    m0 = headline_model().fit(np.vstack(xtr), np.concatenate(ytr))
    d1, k1 = tuned(LINEAR, xtr, ytr)
    d2, k2 = tuned(TREES, xtr, ytr)
    p = {name: m.predict_proba(xs[i])[:, 1] for name, m in [("M0", m0), ("D1", d1), ("D2", d2)]}
    p["D3"] = (p["D1"] + p["D2"]) / 2
    return p, (k1, k2)


def alarm_precision(y, p, share=0.2):
    """Share of the riskiest 20% of moments that really are followed by a reversal within 5 s."""
    return float(y[p >= np.quantile(p, 1 - share)].mean())


def holm(ps):
    order, adj, run = np.argsort(ps), np.empty(len(ps)), 0.0
    for rank, i in enumerate(order):
        run = max(run, (len(ps) - rank) * ps[i])
        adj[i] = min(1.0, run)
    return adj.tolist()


def main():
    worms = load_labelled_worms()
    classes = common_classes(worms)
    per = [samples(w, classes, HORIZON)["brain+body"] for w in worms.values()]
    xs, ys = [s[0] for s in per], [s[1] for s in per]
    out = Parallel(n_jobs=-1)(delayed(one_worm)(i, xs, ys) for i in range(len(xs)))
    names = ["M0", "D1", "D2", "D3"]
    auc = {n: [roc_auc_score(ys[i], out[i][0][n]) for i in range(len(xs))] for n in names}
    ap = {n: [average_precision_score(ys[i], out[i][0][n]) for i in range(len(xs))] for n in names}
    prec = {n: [alarm_precision(ys[i], out[i][0][n]) for i in range(len(xs))] for n in names}
    head = json.loads(Path("results/summary.json").read_text())["curve"][str(HORIZON)]["brain+body"]["auc"]
    assert np.allclose(auc["M0"], head, atol=1e-9), "M0 must reproduce the headline exactly"
    tests = {n: {"median_gain": float(np.median(np.subtract(auc[n], auc["M0"]))),
                 "worms_improved": int((np.subtract(auc[n], auc["M0"]) > 0).sum()),
                 "p": float(wilcoxon(np.subtract(auc[n], auc["M0"])).pvalue)} for n in ["D1", "D2", "D3"]}
    for n, p in zip(tests, holm([tests[n]["p"] for n in tests])):
        tests[n]["p_holm"] = p
        tests[n]["improvement"] = bool(p < 0.05 and tests[n]["median_gain"] > 0)
    res = {"median": {n: {"auc": float(np.median(auc[n])), "average_precision": float(np.median(ap[n])),
                          "alarm_precision": float(np.median(prec[n]))} for n in names},
           "tests_vs_M0_auc": tests,
           "chosen": {"D1_C": [[0.0003, 0.001, 0.003, 0.01, 0.03][k1] for _, (k1, _) in out],
                      "D2_setting": [["15 leaves, 0.03", "15 leaves, 0.1", "31 leaves, 0.03", "31 leaves, 0.1"][k2] for _, (_, k2) in out]},
           "per_worm": {"auc": auc, "average_precision": ap, "alarm_precision": prec}}
    Path("results/accuracy_followup2.json").write_text(json.dumps(res, indent=1))
    print("M0 reproduces the headline exactly")
    for n in names:
        m = res["median"][n]
        t = tests.get(n, {})
        print(f"{n}: AUC {m['auc']:.3f}  avg precision {m['average_precision']:.3f}  alarm precision {m['alarm_precision']:.3f}  "
              + (f"| vs M0: +{t['median_gain']:.4f}, {t['worms_improved']}/40, Holm p {t['p_holm']:.4f}, improvement {t['improvement']}" if t else ""))
    from collections import Counter
    print("chosen:", {k: dict(Counter(v)) for k, v in res["chosen"].items()})


if __name__ == "__main__":
    main()
