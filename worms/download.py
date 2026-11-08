"""Download the processed dataset (~570 MB) and neuron labels into data/. Run: uv run python -m worms.download"""

import bz2
import hashlib
import tarfile
import urllib.request
from pathlib import Path

RECORD = "https://zenodo.org/api/records/19388374/files"  # Zenodo v4 of Atanas & Kim et al. 2023
FILES = {
    "processed_h5.tar.bz2": "c93e0cea3941b9e72bd7f09a36d7d26c8c5eca0e26fc2694dac739bbfa51c3c8",
    "neuropal_label.json.bz2": None,  # small; checksum not published, file pinned by the record version
}
DATA = Path("data")
# Official per-recording list (heat events, head-angle sign), linked from the Zenodo record
DATASET_LIST = "https://raw.githubusercontent.com/flavell-lab/WormWideWeb-data/main/activity/raw/atanas_kim_2023.csv"
DATASET_LIST_SHA = "2376e4d5a6a45e35393689ea573f64da0cd5d8e0423ab5a75c1649b0949ecbba"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    DATA.mkdir(exist_ok=True)
    for name, expected in FILES.items():
        dest = DATA / name
        if not dest.exists():
            print(f"downloading {name} ...")
            urllib.request.urlretrieve(f"{RECORD}/{name}/content", dest)
        if expected and sha256(dest) != expected:
            raise SystemExit(f"{name}: checksum mismatch, delete it and re-run")

    csv = DATA / "atanas_kim_2023.csv"
    if not csv.exists():
        urllib.request.urlretrieve(DATASET_LIST, csv)
    if sha256(csv) != DATASET_LIST_SHA:
        raise SystemExit(f"{csv.name}: checksum mismatch (the list may have been updated upstream)")

    with tarfile.open(DATA / "processed_h5.tar.bz2") as tar:
        tar.extractall(DATA / "atanas2023", filter="data")  # "data" filter blocks unsafe paths in the archive
    (DATA / "neuropal_label.json").write_bytes(bz2.decompress((DATA / "neuropal_label.json.bz2").read_bytes()))
    print("done:", len(list((DATA / "atanas2023").glob("*.h5"))), "worm files in data/atanas2023")


if __name__ == "__main__":
    main()
