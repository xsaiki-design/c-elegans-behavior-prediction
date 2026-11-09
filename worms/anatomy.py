"""Real positions and wiring for the neuron map on the live page: uv run python -m worms.anatomy -> docs/live/anatomy.json

- Positions: cell-body centres from OpenWorm's NeuroML model (CElegansNeuroML, converted from the WormBase Virtual Worm).
- Wiring: Cook et al. 2019 adult hermaphrodite connectome, corrected July 2020 (from OpenWorm's ConnectomeToolbox).
"""

import hashlib
import json
import re
import urllib.request
from pathlib import Path

from openpyxl import load_workbook

from worms.run import common_classes, load_labelled_worms

NML = "https://raw.githubusercontent.com/openworm/CElegansNeuroML/master/CElegans/generatedNeuroML2/{}.cell.nml"
COOK = ("https://raw.githubusercontent.com/openworm/ConnectomeToolbox/main/cect/data/"
        "SI%205%20Connectome%20adjacency%20matrices%2C%20corrected%20July%202020.xlsx")
COOK_SHA = "1f4fdbf84746b69b49a8da0816f52787860ce349b638dce37924ba80f90c70c9"
CACHE = Path("data/anatomy")
OUT = Path("docs/live/anatomy.json")


def fetch(url, dest):
    if not dest.exists():
        urllib.request.urlretrieve(url, dest)
    return dest


def soma_position(name):
    """(left-right, anterior-posterior, dorsal-ventral) of the cell body in micrometres, from the soma segment."""
    text = fetch(NML.format(name), CACHE / "nml" / f"{name}.cell.nml").read_text()
    m = re.search(r'<segment id="0"[^>]*>\s*<proximal x="([-\d.e]+)" y="([-\d.e]+)" z="([-\d.e]+)"', text)
    return tuple(float(v) for v in m.groups())


def read_matrix(ws):
    """{(pre, post): count} from a Cook 2019 sheet: names in row 3 (columns) and column C (rows), counts in the grid."""
    rows = ws.iter_rows(values_only=True)
    next(rows), next(rows)
    cols = next(rows)
    out = {}
    for r in rows:
        pre = r[2]
        for post, v in zip(cols[3:], r[3:]):
            if pre and post and v:
                out[(str(pre).strip(), str(post).strip())] = v
    return out


def class_edges(chemical, electrical, cls):
    """Synapse totals between neuron classes, both directions; electrical junctions (listed both ways) counted once."""
    tot = {}
    for table, kind, both_ways in [(chemical, "chemical", False), (electrical, "electrical", True)]:
        for (pre, post), v in table.items():
            a, b = cls.get(pre), cls.get(post)
            if a and b and a != b:
                key = tuple(sorted((a, b)))
                tot.setdefault(key, {"chemical": 0, "electrical": 0})[kind] += v / (2 if both_ways else 1)
    return [{"a": a, "b": b, "chemical": round(c["chemical"]), "electrical": round(c["electrical"])}
            for (a, b), c in sorted(tot.items())]


def main():
    (CACHE / "nml").mkdir(parents=True, exist_ok=True)
    worms = load_labelled_worms()
    classes = common_classes(worms)
    # every individual neuron named in our recordings that belongs to one of the 46 classes
    # ("AIB?" etc. are labels where the annotator wasn't sure which cell; they aren't real neuron names)
    cls = {lab: c for w in worms.values() for lab, c in zip(w.labels, w.classes) if c in classes and "?" not in lab}
    xlsx = fetch(COOK, CACHE / "cook2019_SI5_corrected_2020.xlsx")
    if hashlib.sha256(xlsx.read_bytes()).hexdigest() != COOK_SHA:
        raise SystemExit(f"{xlsx}: checksum mismatch")
    wb = load_workbook(xlsx, read_only=True, data_only=True)
    edges = class_edges(read_matrix(wb["hermaphrodite chemical"]), read_matrix(wb["hermaphrodite gap jn symmetric"]), cls)
    neurons = []
    for name in sorted(cls):
        lr, ap, dv = soma_position(name)
        neurons.append({"name": name, "class": cls[name], "ap": round(ap, 1), "dv": round(dv, 1), "lr": round(lr, 1)})
    OUT.write_text(json.dumps({
        "neurons": neurons, "edges": edges,
        "sources": {
            "positions": "OpenWorm CElegansNeuroML (from the WormBase Virtual Worm), github.com/openworm/CElegansNeuroML",
            "wiring": "Cook et al. 2019, Nature 571:63-71, doi:10.1038/s41586-019-1352-7 (SI 5, corrected July 2020), via OpenWorm ConnectomeToolbox",
        },
    }, indent=0))
    print(f"wrote {OUT}: {len(neurons)} neurons in {len(set(cls.values()))} classes, {len(edges)} class-to-class connections")


if __name__ == "__main__":
    main()
