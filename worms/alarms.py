"""Exploratory, after the headline: as an alarm, how many reversals does each model warn of, given equal alarms?

Reads the held-out predictions (docs/demo-data.json, from worms.demo_data). uv run python -m worms.alarms -> results/alarms.json
"""

import json
from pathlib import Path

import numpy as np

SHARES = [0.1, 0.2, 0.3]  # alarm on this share of each worm's moments, for both models
MIN_LEADS = [1, 3, 5]  # frames of warning required (~0.6, 1.8, 3.0 s)
MODELS = {"body": "risk_body", "brain+body": "risk_brain_body"}


def caught(risk, reversals, threshold, min_lead, horizon):
    """(warned, total): reversals with an alarm min_lead..horizon frames before they start; total = those with any score there."""
    warned = total = 0
    for start, _ in reversals:
        window = [risk[t] for t in range(max(0, start - horizon), start - min_lead + 1) if risk[t] is not None]
        if window:
            total += 1
            warned += any(r > threshold for r in window)
    return warned, total


def main():
    d = json.loads(Path("docs/demo-data.json").read_text())
    rows = []
    for share in SHARES:
        for lead in MIN_LEADS:
            per = {m: [] for m in MODELS}
            for w in d["worms"]:
                for m, key in MODELS.items():
                    scores = np.sort([r for r in w[key] if r is not None])
                    per[m].append(caught(w[key], w["reversals"], scores[int((1 - share) * len(scores))], lead, d["horizon_frames"]))
            body, both = np.array(per["body"]), np.array(per["brain+body"])
            rows.append({
                "share": share, "min_lead_s": round(lead * 0.6, 1), "total": int(body[:, 1].sum()),
                "body": float(body[:, 0].sum() / body[:, 1].sum()), "brain+body": float(both[:, 0].sum() / both[:, 1].sum()),
                "worms_brain_more": int((both[:, 0] > body[:, 0]).sum()), "worms_brain_fewer": int((both[:, 0] < body[:, 0]).sum()),
            })
    Path("results/alarms.json").write_text(json.dumps(rows, indent=1))
    print("| alarms on | warning needed | body catches | brain+body catches | brain+body more / fewer (of 40 worms) |")
    print("|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['share']:.0%} of moments | ≥ {r['min_lead_s']} s | {r['body']:.0%} | {r['brain+body']:.0%} | "
              f"{r['worms_brain_more']} / {r['worms_brain_fewer']} |")


if __name__ == "__main__":
    main()
