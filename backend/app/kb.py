"""Memuat basis pengetahuan hasil scripts/bangun_kb.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
BERKAS_KB = AKAR / "data" / "kb" / "basis_pengetahuan.json"
# Profil minat profesi hasil kalibrasi dengan responden profesional Indonesia.
# Hanya ada kalau scripts/kalibrasi_riasec.py --tulis dijalankan DAN kalibrasi
# terbukti lebih baik daripada profil O*NET murni. Lihat docs/relevansi-riasec.md.
BERKAS_RIASEC_LOKAL = AKAR / "data" / "kb" / "riasec_lokal.json"

RIASEC = "RIASEC"
BIG5 = "OCEAN"


@dataclass(frozen=True)
class BasisPengetahuan:
    mentah: dict

    @property
    def profesi(self) -> list[dict]:
        return self.mentah["profesi"]

    @property
    def skill(self) -> list[dict]:
        return self.mentah["skill"]

    @property
    def jenjang(self) -> list[dict]:
        return self.mentah["jenjang"]

    @property
    def bidang(self) -> list[dict]:
        return self.mentah["bidang"]

    @property
    def kota(self) -> list[str]:
        return self.mentah["kota"]

    @property
    def prodi(self) -> list[dict]:
        return self.mentah["prodi"]

    def skill_profesi(self, profesi_id: str) -> list[dict]:
        return self.mentah["profesi_skill"][profesi_id]

    def cari_profesi(self, profesi_id: str) -> dict | None:
        return next((p for p in self.profesi if p["id"] == profesi_id), None)

    def nama_skill(self) -> dict[str, str]:
        return {s["id"]: s["nama"] for s in self.skill}

    def belajar_skill(self) -> dict[str, list[dict]]:
        """Sumber belajar kurasi per skill; kosong kalau belum ada."""
        return {s["id"]: s.get("belajar", []) for s in self.skill}

    def rank_jenjang(self, kode: str) -> int:
        return next(j["rank"] for j in self.jenjang if j["kode"] == kode)


def dengan_riasec(kb: BasisPengetahuan, profil: dict[str, dict[str, float]],
                  sumber: str = "kalibrasi lokal") -> BasisPengetahuan:
    """Salinan basis pengetahuan dengan profil RIASEC (skala 1 - 7) sebagian profesi diganti.

    Kode Holland ikut dihitung ulang supaya indeks Iachan memakai profil yang sama.
    """
    profesi = []
    for p in kb.profesi:
        if p["id"] in profil:
            r = {t: round(profil[p["id"]][t], 3) for t in RIASEC}
            kode = "".join(sorted(RIASEC, key=lambda t: (-r[t], RIASEC.index(t)))[:3])
            p = {**p, "riasec": r, "kode_holland": kode, "riasec_sumber": sumber}
        profesi.append(p)
    return BasisPengetahuan({**kb.mentah, "profesi": profesi})


def campur_riasec(onet: dict[str, float], lokal: list[dict[str, float]], k: float = 5.0) -> dict[str, float]:
    """Penyusutan (shrinkage) profil O*NET ke rata-rata responden lokal.

    onet: skala 1 - 7. lokal: skor responden profesional skala 0 - 1.
    Bobot lokal = n / (n + k): satu-dua responden hanya menggeser sedikit, dan
    profil O*NET baru benar-benar tergantikan kalau respondennya banyak.
    """
    n = len(lokal)
    if n == 0:
        return dict(onet)
    w = n / (n + k)
    rata = {t: 1 + 6 * sum(x[t] for x in lokal) / n for t in RIASEC}
    return {t: (1 - w) * onet[t] + w * rata[t] for t in RIASEC}


@lru_cache(maxsize=1)
def muat_kb() -> BasisPengetahuan:
    if not BERKAS_KB.exists():
        raise FileNotFoundError(
            f"{BERKAS_KB} belum ada. Jalankan dulu: python scripts/bangun_kb.py"
        )
    kb = BasisPengetahuan(json.loads(BERKAS_KB.read_text(encoding="utf-8")))
    if BERKAS_RIASEC_LOKAL.exists():
        lokal = json.loads(BERKAS_RIASEC_LOKAL.read_text(encoding="utf-8"))
        kb = dengan_riasec(kb, lokal["profil"])
    return kb
