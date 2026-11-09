"""Real positions and wiring for the neuron map on the live page: uv run python -m worms.anatomy -> docs/live/anatomy.json

- Positions: cell-body centres from OpenWorm's NeuroML model (CElegansNeuroML, converted from the WormBase Virtual Worm).
- Wiring: Cook et al. 2019 adult hermaphrodite connectome, corrected July 2020 (from OpenWorm's ConnectomeToolbox).
"""

import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from openpyxl import load_workbook

from worms.run import common_classes, load_labelled_worms

NML = "https://raw.githubusercontent.com/openworm/CElegansNeuroML/master/CElegans/generatedNeuroML2/{}.cell.nml"
COOK = ("https://raw.githubusercontent.com/openworm/ConnectomeToolbox/main/cect/data/"
        "SI%205%20Connectome%20adjacency%20matrices%2C%20corrected%20July%202020.xlsx")
CELLS = "https://raw.githubusercontent.com/openworm/ConnectomeToolbox/main/cect/Cells.py"  # read as text, never run
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


def neuron_links(chemical, electrical, names):
    """[a, b, synapses] between individual neurons in `names`, both directions; gap junctions (listed both ways) once."""
    tot = {}
    for table, half in [(chemical, 1), (electrical, 2)]:
        for (pre, post), v in table.items():
            if pre in names and post in names and pre != post:
                key = tuple(sorted((pre, post)))
                tot[key] = tot.get(key, 0) + v / half
    return [[a, b, round(v)] for (a, b), v in sorted(tot.items()) if round(v)]


def roles(text):
    """Cell role labels (Cook et al. 2019 categories) from the toolbox's Cells.py, parsed as text."""
    lists = {m.group(1): re.findall(r'"([^"]+)"', m.group(2)) for m in re.finditer(r"^(\w+)\s*=\s*\[(.*?)\]", text, re.S | re.M)}
    out = {}
    for m in re.finditer(r'^\s*if cell in \[(.*?)\]:\n\s+cell_notes\[cell\] = "([^"]+)"', text, re.S | re.M):
        for c in re.findall(r'"([^"]+)"', m.group(1)):
            out.setdefault(c, m.group(2))
    for m in re.finditer(r'^for cell in (\w+):\n\s+cell_notes\[cell\] = "([^"]+)"', text, re.M):
        for c in lists.get(m.group(1), []):
            out.setdefault(c, m.group(2))
    return out


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
    chemical = read_matrix(wb["hermaphrodite chemical"])
    electrical = read_matrix(wb["hermaphrodite gap jn symmetric"])
    edges = class_edges(chemical, electrical, cls)
    role = roles(fetch(CELLS, CACHE / "Cells.py.txt").read_text())
    neurons = []
    for name in sorted(cls):
        lr, ap, dv = soma_position(name)
        neurons.append({"name": name, "class": cls[name], "role": role.get(name, ""),
                        "ap": round(ap, 1), "dv": round(dv, 1), "lr": round(lr, 1)})
    # every other neuron in the head, so the map shows the model's neurons in context (non-neurons have no model file)
    head_end = max(n["ap"] for n in neurons) + 5
    others = []
    for name in sorted({c for pair in chemical for c in pair} - set(cls)):
        try:
            lr, ap, dv = soma_position(name)
        except urllib.error.HTTPError:
            continue
        if ap <= head_end:
            others.append({"name": name, "role": role.get(name, ""), "ap": round(ap, 1), "dv": round(dv, 1)})
    OUT.write_text(json.dumps({
        "neurons": neurons, "others": others, "edges": edges, "links": neuron_links(chemical, electrical, set(cls)),
        "sources": {
            "positions": "OpenWorm CElegansNeuroML (from the WormBase Virtual Worm), github.com/openworm/CElegansNeuroML",
            "roles": "Cook et al. 2019 cell categories as listed in OpenWorm ConnectomeToolbox cect/Cells.py",
            "wiring": "Cook et al. 2019, Nature 571:63-71, doi:10.1038/s41586-019-1352-7 (SI 5, corrected July 2020), via OpenWorm ConnectomeToolbox",
        },
    }, indent=0))
    print(f"wrote {OUT}: {len(neurons)} model neurons in {len(set(cls.values()))} classes, {len(others)} other head neurons, "
          f"{len(edges)} class-to-class connections")


if __name__ == "__main__":
    main()
