"""Memuat basis pengetahuan hasil scripts/bangun_kb.py."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

AKAR = Path(__file__).resolve().parents[2]
BERKAS_KB = AKAR / "data" / "kb" / "basis_pengetahuan.json"

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


@lru_cache(maxsize=1)
def muat_kb() -> BasisPengetahuan:
    if not BERKAS_KB.exists():
        raise FileNotFoundError(
            f"{BERKAS_KB} belum ada. Jalankan dulu: python scripts/bangun_kb.py"
        )
    return BasisPengetahuan(json.loads(BERKAS_KB.read_text(encoding="utf-8")))
