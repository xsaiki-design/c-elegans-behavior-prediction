"""PROTOTYPE (throwaway): the accuracy follow-up pre-registered in docs/decisions/0005. Not part of the headline.

uv run python -m worms.prototype_accuracy -> results/accuracy_followup.json
"""

import json
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from scipy.stats import wilcoxon
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from worms.features import class_activity, frames_since_reversal, reversal_soon
from worms.run import HORIZON, before_heat, common_classes, load_labelled_worms

CS = [0.01, 0.03, 0.1, 0.3, 1.0]


def change(x, k):
    out = np.full_like(x, np.nan)
    out[k:] = x[k:] - x[:-k]
    return out


def build(w, classes, lags=(5,), body_trend=False):
    """(body, brain+body, labels) on usable frames. lags=(5,) and body_trend=False is exactly the headline."""
    usable, soon = reversal_soon(w.reversing, HORIZON)
    usable &= before_heat(w, HORIZON)
    act = class_activity(w, classes)
    brain = np.hstack([act] + [change(act, k) for k in lags])
    body = np.c_[w.velocity, w.head_angle, frames_since_reversal(w.reversing)]
    if body_trend:
        body = np.c_[body, change(w.velocity[:, None], 5)]
    usable &= ~np.isnan(brain).any(axis=1) & ~np.isnan(body).any(axis=1)
    return body[usable], np.hstack([brain, body])[usable], soon[usable]


def logistic(c=1.0):
    return make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=2000))


def boosted():
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=0)


def tuned_logistic(xs, ys):
    """Pick C by 5-fold grouped CV over the training worms only, then refit on all of them."""
    x, y = np.vstack(xs), np.concatenate(ys)
    groups = np.concatenate([np.full(len(v), i) for i, v in enumerate(ys)])
    scores = []
    for c in CS:
        s = []
        for tr, va in GroupKFold(5).split(x, y, groups):
            s.append(roc_auc_score(y[va], logistic(c).fit(x[tr], y[tr]).predict_proba(x[va])[:, 1]))
        scores.append(np.mean(s))
    best = CS[int(np.argmax(scores))]
    return logistic(best).fit(x, y), best


def held_out(i, xs, ys, kind):
    xtr = [x for j, x in enumerate(xs) if j != i]
    ytr = [y for j, y in enumerate(ys) if j != i]
    if kind == "tuned":
        model, c = tuned_logistic(xtr, ytr)
    else:
        model, c = (logistic() if kind == "default" else boosted()).fit(np.vstack(xtr), np.concatenate(ytr)), None
    return roc_auc_score(ys[i], model.predict_proba(xs[i])[:, 1]), c


def lowo(xs, ys, kind):
    out = Parallel(n_jobs=-1)(delayed(held_out)(i, xs, ys, kind) for i in range(len(xs)))
    return [a for a, _ in out], [c for _, c in out]


def paired(base, new):
    d = np.array(new) - np.array(base)
    return {"median_gain": float(np.median(d)), "worms_improved": int((d > 0).sum()), "p": float(wilcoxon(d).pvalue)}


def holm(ps):
    """Holm-corrected p-values, same order as given."""
    order = np.argsort(ps)
    adj, running = np.empty(len(ps)), 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(ps) - rank) * ps[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def main():
    worms = load_labelled_worms()
    classes = common_classes(worms)
    sets = {
        "headline": [build(w, classes) for w in worms.values()],
        "longer_history": [build(w, classes, lags=(2, 5, 10)) for w in worms.values()],
        "body_history": [build(w, classes, body_trend=True) for w in worms.values()],
    }
    ys = {k: [s[2] for s in v] for k, v in sets.items()}
    both = {k: [s[1] for s in v] for k, v in sets.items()}
    body = {k: [s[0] for s in v] for k, v in sets.items()}

    res = {}
    res["M0"], _ = lowo(both["headline"], ys["headline"], "default")
    summary = json.loads(Path("results/summary.json").read_text())["curve"][str(HORIZON)]["brain+body"]["auc"]
    assert np.allclose(res["M0"], summary, atol=1e-9), "M0 must reproduce the headline exactly"
    print(f"M0 reproduces the headline: median AUC {np.median(res['M0']):.3f}", flush=True)

    res["C1"], c1 = lowo(both["headline"], ys["headline"], "tuned")
    res["C2"], c2 = lowo(both["longer_history"], ys["longer_history"], "tuned")
    res["C3"], c3 = lowo(both["body_history"], ys["body_history"], "tuned")
    res["C3_body"], _ = lowo(body["body_history"], ys["body_history"], "tuned")
    res["C4"], _ = lowo(both["headline"], ys["headline"], "boosted")
    for k in ["C1", "C2", "C3", "C4"]:
        print(f"{k}: median AUC {np.median(res[k]):.3f}", flush=True)

    # C5: combine whichever of C1-C4 pass the rule (decided by the rule, not by eye)
    tests = {k: paired(res["M0"], res[k]) for k in ["C1", "C2", "C3", "C4"]}
    pre = holm([tests[k]["p"] for k in tests])
    passing = [k for k, p in zip(tests, pre) if p < 0.05 and tests[k]["median_gain"] > 0]
    if passing:
        key = "longer_history" if "C2" in passing else "body_history" if "C3" in passing else "headline"
        kind = "boosted" if "C4" in passing else "tuned"
        if "C2" in passing and "C3" in passing:  # both feature changes
            sets["combo"] = [build(w, classes, lags=(2, 5, 10), body_trend=True) for w in worms.values()]
            key = "combo"
        res["C5"], _ = lowo([s[1] for s in sets[key]], [s[2] for s in sets[key]], kind)
        tests["C5"] = paired(res["M0"], res["C5"])
    final = holm([tests[k]["p"] for k in tests])
    for k, p in zip(tests, final):
        tests[k]["p_holm"] = p
        tests[k]["improvement"] = bool(p < 0.05 and tests[k]["median_gain"] > 0)
    tests["C3"]["brain_beats_improved_body"] = paired(res["C3_body"], res["C3"])

    out = {"median_auc": {k: float(np.median(v)) for k, v in res.items()}, "tests_vs_M0": tests,
           "chosen_C": {"C1": c1, "C2": c2, "C3": c3}, "passing_first_round": passing, "per_worm_auc": res}
    Path("results/accuracy_followup.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ["median_auc", "tests_vs_M0", "passing_first_round"]}, indent=1))
    from collections import Counter
    print("chosen C:", {k: dict(Counter(v)) for k, v in out["chosen_C"].items()})


if __name__ == "__main__":
    main()
