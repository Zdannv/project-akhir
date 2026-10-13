"""Tahap 2a — Knowledge-Based Filtering.

Dua lapis, mengikuti buku proposal:

  1. Penyaring mutlak (hard filter). Profesi yang syaratnya tidak mungkin
     dipenuhi dikeluarkan sebelum diberi skor, lengkap dengan alasannya:
       * pendidikan  — jenjang pengguna di bawah syarat minimum profesi;
       * relokasi    — pengguna tidak bersedia pindah, sedangkan profesinya
                       tidak ada di kota domisili dan tidak bisa dikerjakan
                       jarak jauh.

  2. Skor kecocokan berbobot dari empat komponen, masing-masing 0 - 1:

       komponen              punya tanggungan   tanpa tanggungan
       kongruensi RIASEC           0,50              0,60
       kecocokan Big Five          0,20              0,25
       kecocokan finansial         0,15              0,15
       stabilitas kerja            0,15              0,00

     Bobot stabilitas hanya aktif untuk pengguna yang menanggung keluarga;
     bagi yang lain bobotnya dialihkan ke minat dan kepribadian.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .kb import BIG5, RIASEC, BasisPengetahuan
from .kuesioner import kode_holland

BOBOT_TANGGUNGAN = {"riasec": 0.50, "big5": 0.20, "finansial": 0.15, "stabilitas": 0.15}
BOBOT_TANPA = {"riasec": 0.60, "big5": 0.25, "finansial": 0.15, "stabilitas": 0.00}

# Indeks M Iachan (1984): bobot kecocokan posisi huruf pada kode tiga huruf.
# Baris = posisi huruf di kode orang, kolom = posisinya di kode pekerjaan.
IACHAN = ((22, 10, 4), (10, 5, 2), (4, 2, 1))
IACHAN_MAKS = 28  # 22 + 5 + 1, ketiga huruf sama dan sama urutannya

DOMISILI_LAIN = "Lainnya"


@dataclass(frozen=True)
class ProfilPengguna:
    """Hasil profiling, masukan tahap matching."""

    riasec: dict[str, float]           # 0 - 1 per tipe
    big5: dict[str, float]             # 0 - 1 per dimensi
    rank_pendidikan: int
    domisili: str
    bersedia_relokasi: bool
    ekspektasi_gaji: int               # rupiah per bulan; 0 = tidak diisi
    punya_tanggungan: bool
    skill: dict[str, int]              # skill_id -> tingkat 1..3


# ── Penyaring mutlak ────────────────────────────────────────────────────────
def alasan_tersaring(profil: ProfilPengguna, profesi: dict) -> list[dict]:
    """Daftar kosong berarti profesi lolos."""
    alasan = []
    if profil.rank_pendidikan < profesi["pendidikan_min_rank"]:
        alasan.append({
            "kode": "pendidikan",
            "pesan": f"Syarat pendidikan minimum {profesi['pendidikan_min_label']}.",
        })
    if not profil.bersedia_relokasi and not _terjangkau(profil.domisili, profesi):
        kota = ", ".join(profesi["lokasi"])
        alasan.append({
            "kode": "relokasi",
            "pesan": f"Lowongannya terpusat di {kota} dan tidak bisa dikerjakan jarak jauh.",
        })
    return alasan


def _terjangkau(domisili: str, profesi: dict) -> bool:
    return (
        profesi["semua_kota"]
        or "remote" in profesi["pola_kerja"]
        or domisili in profesi["lokasi"]
    )


# ── Komponen skor ───────────────────────────────────────────────────────────
def kongruensi_iachan(kode_orang: str, kode_profesi: str) -> float:
    m = sum(
        IACHAN[i][kode_profesi.index(huruf)]
        for i, huruf in enumerate(kode_orang)
        if huruf in kode_profesi
    )
    return m / IACHAN_MAKS


def kongruensi_korelasi(riasec_orang: dict[str, float], riasec_profesi: dict[str, float]) -> float:
    """Korelasi Pearson keenam skor minat, dipetakan ke 0 - 1. Ukuran bawaan.

    Memakai seluruh bentuk profil, bukan hanya tiga huruf teratas. Dua akibatnya:
    profesi yang kode tiga hurufnya sama tetap bisa dibedakan, dan orang yang
    minatnya merata tidak dijatuhkan hanya karena huruf pertamanya berbeda
    tipis. Indeks Iachan (di atas) adalah ukuran di buku proposal dan tetap
    dipakai sebagai pembanding.
    """
    a = [riasec_orang[t] for t in RIASEC]
    b = [riasec_profesi[t] for t in RIASEC]
    ra, rb = sum(a) / 6, sum(b) / 6
    va = math.sqrt(sum((x - ra) ** 2 for x in a))
    vb = math.sqrt(sum((x - rb) ** 2 for x in b))
    if va == 0 or vb == 0:
        return 0.5  # profil rata: tidak ada informasi arah minat
    r = sum((x - ra) * (y - rb) for x, y in zip(a, b)) / (va * vb)
    return (r + 1) / 2


def kecocokan_big5(orang: dict[str, float], ideal: dict[str, float]) -> float:
    """1 - jarak Euclid ternormalisasi (jarak maksimum di ruang 5 dimensi: akar 5)."""
    d = math.sqrt(sum((orang[k] - ideal[k]) ** 2 for k in BIG5))
    return 1 - d / math.sqrt(len(BIG5))


def kecocokan_finansial(ekspektasi: int, gaji_min: int, gaji_maks: int) -> float:
    """1 kalau ekspektasi tidak melebihi batas bawah rentang gaji profesi,
    turun linear sampai 0 di batas atas. Tidak diisi dianggap netral (1)."""
    if ekspektasi <= 0 or ekspektasi <= gaji_min:
        return 1.0
    if ekspektasi >= gaji_maks:
        return 0.0
    return (gaji_maks - ekspektasi) / (gaji_maks - gaji_min)


# ── Skor KBF ────────────────────────────────────────────────────────────────
def skor_kbf(profil: ProfilPengguna, profesi: dict, metode_riasec: str = "korelasi") -> dict:
    if metode_riasec == "iachan":
        riasec = kongruensi_iachan(kode_holland(profil.riasec), profesi["kode_holland"])
    elif metode_riasec == "korelasi":
        riasec = kongruensi_korelasi(profil.riasec, profesi["riasec"])
    else:
        raise ValueError(f"metode_riasec tidak dikenal: {metode_riasec}")

    komponen = {
        "riasec": riasec,
        "big5": kecocokan_big5(profil.big5, profesi["big5_ideal"]),
        "finansial": kecocokan_finansial(profil.ekspektasi_gaji, profesi["gaji_min"], profesi["gaji_maks"]),
        "stabilitas": profesi["stabilitas"],
    }
    bobot = BOBOT_TANGGUNGAN if profil.punya_tanggungan else BOBOT_TANPA
    skor = sum(bobot[k] * komponen[k] for k in bobot)
    return {
        "skor": round(skor, 4),
        "komponen": {k: round(v, 4) for k, v in komponen.items()},
        "bobot": bobot,
    }


def saring(profil: ProfilPengguna, kb: BasisPengetahuan) -> tuple[list[dict], list[dict]]:
    """Memisahkan profesi yang lolos dari yang tersaring."""
    lolos, tersaring = [], []
    for p in kb.profesi:
        alasan = alasan_tersaring(profil, p)
        if alasan:
            tersaring.append({"profesi_id": p["id"], "nama": p["nama"], "alasan": alasan})
        else:
            lolos.append(p)
    return lolos, tersaring
