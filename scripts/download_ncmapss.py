"""Télécharge N-CMAPSS (NASA PCoE), extrait DS01 à DS07, écrit docs/data.md.

Usage : python -m scripts.download_ncmapss [--only DS02] [--margin-go 15]
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

import h5py
import numpy as np

from src import config

URL = "https://phm-datasets.s3.amazonaws.com/NASA/17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip"
INNER = "17. Turbofan Engine Degradation Simulation Data Set 2/data_set.zip"
ARCHIVE = config.DATA_RAW / "ncmapss_archive.zip"
MARGIN = 15 * 10**9
CHUNK = 16 * 2**20
DOC = config.PROJECT_ROOT / "docs" / "data.md"


def remote_size() -> int:
    with urllib.request.urlopen(urllib.request.Request(URL, method="HEAD")) as resp:
        return int(resp.headers["Content-Length"])


def download(expected: int) -> None:
    done = ARCHIVE.stat().st_size if ARCHIVE.exists() else 0
    if done == expected:
        return
    free = shutil.disk_usage(config.DATA_RAW).free
    if free < expected - done + MARGIN:
        sys.exit(f"Espace libre insuffisant : {free / 1e9:.1f} Go, il faut {(expected - done + MARGIN) / 1e9:.1f} Go")
    # Reprise depuis la fin du fichier partiel, y compris après une coupure réseau
    for _ in range(10):
        done = ARCHIVE.stat().st_size if ARCHIVE.exists() else 0
        if done == expected:
            break
        req = urllib.request.Request(URL, headers={"Range": f"bytes={done}-"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp, open(ARCHIVE, "ab") as out:
                while chunk := resp.read(CHUNK):
                    out.write(chunk)
                    done += len(chunk)
                    if done % 10**9 < CHUNK:
                        print(f"{done / 1e9:.0f} / {expected / 1e9:.0f} Go", flush=True)
        except OSError as exc:
            print(f"Coupure à {done / 1e9:.1f} Go ({exc}), reprise", flush=True)
    if ARCHIVE.stat().st_size != expected:
        sys.exit(f"Archive incomplète : {ARCHIVE.stat().st_size} octets au lieu de {expected}")


def wanted(name: str, only: str | None = None) -> bool:
    match = re.match(r"N-CMAPSS_(DS\w+?)[-.]", Path(name).name)
    if not match or not name.endswith(".h5"):
        return False
    return match.group(1) == only if only else match.group(1) in config.NCMAPSS_FAULT_MODES


def file_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(CHUNK):
            sha.update(chunk)
    return sha.hexdigest()


def extract(only: str | None = None, margin: int = MARGIN) -> tuple[list[tuple[str, int, str]], list[str]]:
    """Extrait les .h5 retenus sans écrire data_set.zip sur le disque. zipfile vérifie le CRC de chaque fichier lu."""
    config.NCMAPSS_DIR.mkdir(parents=True, exist_ok=True)
    rows, notes = [], []
    with zipfile.ZipFile(ARCHIVE) as outer, outer.open(INNER) as inner_file, zipfile.ZipFile(inner_file) as inner:
        names = [info.filename for info in inner.infolist()]
        print("Contenu de data_set.zip :", *names, sep="\n  ")
        selected = [i for i in inner.infolist() if wanted(i.filename, only)]
        needed = sum(i.file_size for i in selected) + margin
        free = shutil.disk_usage(config.NCMAPSS_DIR).free
        if free < needed:
            sys.exit(f"Espace libre insuffisant : {free / 1e9:.1f} Go, il faut {needed / 1e9:.1f} Go")
        # Ordre des offsets : évite de relire l'archive depuis le début entre deux fichiers
        for info in sorted(selected, key=lambda i: i.header_offset):
            dest = config.NCMAPSS_DIR / Path(info.filename).name
            # Un fichier déjà présent n'est remplacé que s'il diffère de la version officielle
            target = dest.with_name(dest.name + ".tmp") if dest.exists() else dest
            sha = hashlib.sha256()
            with inner.open(info) as src, open(target, "wb") as out:
                while chunk := src.read(CHUNK):
                    sha.update(chunk)
                    out.write(chunk)
            if target != dest:
                identical = file_sha256(dest) == sha.hexdigest()
                notes.append(f"{dest.name} était déjà présent : "
                             + ("identique à la version officielle, conservé." if identical
                                else "différent de la version officielle, remplacé par celle-ci."))
                target.unlink() if identical else target.replace(dest)
            rows.append((dest.name, info.file_size, sha.hexdigest()))
            print(f"{dest.name} : {info.file_size} octets")
    return rows, notes


def describe(ds_id: str) -> dict[str, object]:
    path = next(config.NCMAPSS_DIR.glob(f"N-CMAPSS_{ds_id}*.h5"))
    stats = {}
    with h5py.File(path, "r") as handle:
        for split in ("dev", "test"):
            aux = np.asarray(handle[f"A_{split}"])
            unit_cycle = np.unique(aux[:, :2].astype(int), axis=0)  # A_var : unit, cycle, Fc, hs
            stats[split] = {
                "units": np.unique(unit_cycle[:, 0]).tolist(),
                "cycles": len(unit_cycle),
                "rul_max": int(np.asarray(handle[f"Y_{split}"]).max()),
            }
    return stats


def documented() -> tuple[list[tuple[str, int, str]], list[str]]:
    """Lignes et notes déjà consignées dans docs/data.md, conservées lors d'une extraction partielle."""
    text = DOC.read_text(encoding="utf-8")
    rows = [(n, int(s), h) for n, s, h in re.findall(r"^\| (N-CMAPSS_\S+\.h5) \| (\d+) \| `([0-9a-f]{64})` \|$", text, re.M)]
    return rows, re.findall(r"^N-CMAPSS_\S+\.h5 était déjà présent : .*$", text, re.M)


def write_doc(rows: list[tuple[str, int, str]], notes: list[str]) -> None:
    lines = [
        "# Données N-CMAPSS",
        "",
        f"Source : NASA Prognostics Center of Excellence, Prognostics Data Repository, « Turbofan Engine Degradation "
        f"Simulation Data Set-2 » (`{URL}`). Fichiers générés par `python -m scripts.download_ncmapss`.",
        "",
        "## Fichiers",
        "",
        "| Fichier | Taille (octets) | SHA-256 |",
        "|---|---|---|",
        *[f"| {name} | {size} | `{sha}` |" for name, size, sha in rows],
        "",
        *notes,
        "",
        "## Contenu",
        "",
        "| DS | Mode de panne | Unités dev | Unités test | Cycles dev | Cycles test | RUL max dev | RUL max test |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for ds_id, fault in config.NCMAPSS_FAULT_MODES.items():
        s = describe(ds_id)
        lines.append(
            f"| {ds_id} | {fault} | {', '.join(map(str, s['dev']['units']))} | {', '.join(map(str, s['test']['units']))} "
            f"| {s['dev']['cycles']} | {s['test']['cycles']} | {s['dev']['rul_max']} | {s['test']['rul_max']} |"
        )
    DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Téléchargement et extraction de N-CMAPSS")
    parser.add_argument("--only", choices=sorted(config.NCMAPSS_FAULT_MODES), help="Extrait ce seul fichier")
    parser.add_argument("--margin-go", type=float, default=MARGIN / 1e9, help="Espace à laisser libre après extraction")
    args = parser.parse_args()

    expected = remote_size()
    print(f"Archive : {expected / 1e9:.2f} Go")
    download(expected)
    rows, notes = extract(args.only, int(args.margin_go * 1e9))
    count = 1 if args.only else len(config.NCMAPSS_FAULT_MODES)
    if len(rows) != count:
        sys.exit(f"{len(rows)} fichiers extraits au lieu de {count}")
    if args.only:
        old_rows, old_notes = documented()
        new = {name for name, _, _ in rows}
        rows = sorted(rows + [r for r in old_rows if r[0] not in new])
        notes = notes + old_notes
    write_doc(rows, notes)
    print(f"Écrit {DOC}. L'archive {ARCHIVE} peut être supprimée.")


if __name__ == "__main__":
    main()
