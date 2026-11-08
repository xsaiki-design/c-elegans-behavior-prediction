"""Exploratory, after the headline (0004): does a nonlinear model or more history do better? Not part of the pre-set plan.

uv run python -m worms.explore   -> results/explore.json
"""

import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from worms.evaluate import leave_one_worm_out
from worms.run import HORIZON, common_classes, load_labelled_worms, paired_test, samples


def main():
    worms = load_labelled_worms()
    classes = common_classes(worms)
    per = [samples(w, classes, HORIZON) for w in worms.values()]
    boost = lambda: HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=0)  # noqa: E731
    head = json.loads(Path("results/summary.json").read_text())["curve"][str(HORIZON)]
    out = {
        "boosted_trees": {name: leave_one_worm_out([p[name] for p in per], boost)[0].tolist() for name in ["body", "brain+body"]},
    }
    out["boosted_vs_logistic_brain+body"] = paired_test(head["brain+body"]["auc"], out["boosted_trees"]["brain+body"])
    out["boosted_brain+body_vs_boosted_body"] = paired_test(out["boosted_trees"]["body"], out["boosted_trees"]["brain+body"])
    Path("results/explore.json").write_text(json.dumps(out, indent=1))
    for k, v in out["boosted_trees"].items():
        print(f"boosted {k}: median AUC {np.nanmedian(v):.3f}")
    print("boosted vs logistic (brain+body):", out["boosted_vs_logistic_brain+body"])
    print("boosted brain+body vs boosted body:", out["boosted_brain+body_vs_boosted_body"])


if __name__ == "__main__":
    main()
