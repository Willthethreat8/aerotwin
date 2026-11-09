"""Télécharge N-CMAPSS (NASA PCoE), extrait DS01 et DS03 à DS07, écrit docs/data.md.

Usage : python -m scripts.download_ncmapss
"""
from __future__ import annotations

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


def wanted(name: str) -> bool:
    match = re.match(r"N-CMAPSS_(DS\w+?)[-.]", Path(name).name)
    return bool(match) and match.group(1) in config.NCMAPSS_FAULT_MODES and name.endswith(".h5")


def file_sha256(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(CHUNK):
            sha.update(chunk)
    return sha.hexdigest()


def extract() -> tuple[list[tuple[str, int, str]], list[str]]:
    """Extrait les .h5 retenus sans écrire data_set.zip sur le disque. zipfile vérifie le CRC de chaque fichier lu."""
    config.NCMAPSS_DIR.mkdir(parents=True, exist_ok=True)
    rows, notes = [], []
    with zipfile.ZipFile(ARCHIVE) as outer, outer.open(INNER) as inner_file, zipfile.ZipFile(inner_file) as inner:
        names = [info.filename for info in inner.infolist()]
        print("Contenu de data_set.zip :", *names, sep="\n  ")
        # Ordre des offsets : évite de relire l'archive depuis le début entre deux fichiers
        for info in sorted((i for i in inner.infolist() if wanted(i.filename)), key=lambda i: i.header_offset):
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
    expected = remote_size()
    print(f"Archive : {expected / 1e9:.2f} Go")
    download(expected)
    rows, notes = extract()
    if len(rows) != len(config.NCMAPSS_FAULT_MODES):
        sys.exit(f"{len(rows)} fichiers extraits au lieu de {len(config.NCMAPSS_FAULT_MODES)}")
    write_doc(rows, notes)
    print(f"Écrit {DOC}. L'archive {ARCHIVE} peut être supprimée.")


if __name__ == "__main__":
    main()
