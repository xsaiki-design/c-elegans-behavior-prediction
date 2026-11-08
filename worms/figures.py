"""Draw the README figures from results/summary.json: uv run python -m worms.figures"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SECONDS_PER_FRAME = 0.6  # ~1.6 frames/s (0001)
COLORS = {"body": "#999999", "brain": "#0072B2", "brain+body": "#D55E00"}  # colour-blind safe (Okabe-Ito)
LABELS = {"body": "body only", "brain": "brain only", "brain+body": "brain + body"}
OUT = Path("figures")


def horizon_curve(s):
    fig, ax = plt.subplots(figsize=(6, 4))
    hs = sorted(s["curve"], key=int)
    x = np.array([int(h) for h in hs]) * SECONDS_PER_FRAME
    for i, name in enumerate(["body", "brain", "brain+body"]):
        aucs = np.array([s["curve"][h][name]["auc"] for h in hs], float)
        mid, lo, hi = (np.nanpercentile(aucs, q, axis=1) for q in (50, 25, 75))
        dx = (i - 1) * 0.12  # nudge so whiskers don't overlap
        ax.errorbar(x + dx, mid, yerr=[mid - lo, hi - mid], marker="o", capsize=3, color=COLORS[name], label=LABELS[name])
    ax.axhline(0.5, color="black", lw=0.8, ls="--")
    ax.text(x[-1], 0.505, "chance", ha="right", va="bottom", fontsize=8)
    ax.axvline(int(s["headline_horizon"]) * SECONDS_PER_FRAME, color="#cccccc", lw=0.8, zorder=0)
    ax.set(xlabel="How far ahead (seconds)", ylabel="ROC-AUC in unseen worms\n(median, quartiles over 40 worms)",
           title="The body's warning fades; the brain's lasts")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "horizon_curve.png", dpi=150)


def per_worm(s):
    head = s["curve"][str(s["headline_horizon"])]
    body, both = np.array(head["body"]["auc"]), np.array(head["brain+body"]["auc"])
    t = s["headline_test"]
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    ax.scatter(body, both, color=COLORS["brain+body"], s=25)
    lo, hi = 0.35, 1.0
    ax.plot([lo, hi], [lo, hi], color="black", lw=0.8, ls="--")
    ax.set(xlim=(lo, hi), ylim=(lo, hi), xlabel="AUC, body only", ylabel="AUC, brain + body",
           title=f"Each dot is one unseen worm (5 s ahead)\nabove the line in {t['worms_improved']} of {t['n']}, "
                 f"p = {t['p']:.4f}")
    fig.tight_layout()
    fig.savefig(OUT / "per_worm.png", dpi=150)


def top_neurons(s, n=12):
    items = list(s["neuron_scores"].items())[:n][::-1]
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    vals = np.array([v for _, v in items])
    ax.barh([k for k, _ in items], vals - 0.5, left=0.5, color=np.where(vals > 0.5, "#CC79A7", "#009E73"))  # own colours: not the model series
    ax.axvline(0.5, color="black", lw=0.8)
    ax.set(xlabel="AUC of this signal alone (median over worms)\n< 0.5: lower before a reversal   > 0.5: higher",
           title="Signals that differ most before a reversal (5 s ahead)")
    fig.tight_layout()
    fig.savefig(OUT / "top_neurons.png", dpi=150)


def main():
    s = json.loads(Path("results/summary.json").read_text())
    OUT.mkdir(exist_ok=True)
    horizon_curve(s)
    per_worm(s)
    top_neurons(s)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
