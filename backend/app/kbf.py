"""Tahap 2a — Knowledge-Based Filtering.

Dua lapis, mengikuti buku proposal:

  1. Penyaring mutlak (hard filter). Profesi yang syaratnya tidak mungkin
     dipenuhi dikeluarkan sebelum diberi skor, lengkap dengan alasannya:
       * pendidikan  — jenjang pengguna di bawah syarat minimum profesi;
       * relokasi    — pengguna tidak bersedia pindah, sedangkan profesinya
                       tidak ada di kota domisili dan tidak bisa dikerjakan
                       jarak jauh.
                       Bawaannya MATI dan diganti catatan untuk pengguna;
                       hanya aktif di konfigurasi proposal.

  2. Skor kecocokan berbobot dari enam komponen, masing-masing 0 - 1:

       komponen               punya tanggungan   tanpa tanggungan   proposal
       kongruensi RIASEC            0,25              0,30          0,50 / 0,60
       minat bidang TI              0,25              0,30              -
       kecocokan Big Five           0,10              0,15          0,20 / 0,25
       kesiapan pengalaman          0,15              0,15              -
       kecocokan finansial          0,10              0,10          0,15 / 0,15
       stabilitas kerja             0,15              0,00          0,15 / 0,00

     Dua komponen tidak ada di buku proposal dan ditambahkan setelah uji coba:

       * minat bidang TI   RIASEC membedakan bidang besar (teknik, seni,
         sosial), tetapi hampir semua profesi TI berkode mirip. Yang
         membedakan Backend dari Data Engineer dari UI/UX adalah bidang kerja
         yang disukai, jadi itu ditanyakan langsung.
       * kesiapan pengalaman   tanpa ini profesi senior (minimal 3 tahun) bisa
         menjadi peringkat satu bagi mahasiswa: cocok, tetapi belum bisa
         dimasuki.

     Bobot stabilitas hanya aktif untuk pengguna yang menanggung keluarga.
     Komponen yang datanya tidak ada (isian lama tanpa minat bidang) dilewati
     dan bobot sisanya dinormalkan ulang. Skema "proposal" memakai empat
     komponen dan bobot asli buku proposal, sebagai pembanding.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .kb import BIG5, RIASEC, BasisPengetahuan
from .kuesioner import kode_holland

# (punya tanggungan, tanpa tanggungan) per skema.
SKEMA_BOBOT = {
    "lengkap": (
        {"riasec": 0.25, "bidang": 0.25, "big5": 0.10, "kesiapan": 0.15, "finansial": 0.10, "stabilitas": 0.15},
        {"riasec": 0.30, "bidang": 0.30, "big5": 0.15, "kesiapan": 0.15, "finansial": 0.10, "stabilitas": 0.00},
    ),
    "proposal": (
        {"riasec": 0.50, "big5": 0.20, "finansial": 0.15, "stabilitas": 0.15},
        {"riasec": 0.60, "big5": 0.25, "finansial": 0.15, "stabilitas": 0.00},
    ),
    # Dua skema di bawah hanya untuk evaluasi, bukan untuk pengguna:
    #   riasec        baseline "minat saja", setara pendekatan penelitian
    #                 terdahulu yang merekomendasikan dari RIASEC
    #   tanpa_riasec  menguji seberapa bergantung hasil pada profil minat O*NET
    #                 (pertanyaan "datanya dari AS, relevan untuk Indonesia?")
    "riasec": ({"riasec": 1.0}, {"riasec": 1.0}),
}
# Bobot "lengkap" tanpa RIASEC, sisanya dinormalkan ulang supaya berjumlah 1.
SKEMA_BOBOT["tanpa_riasec"] = tuple(
    {k: v / (1 - b["riasec"]) for k, v in b.items() if k != "riasec"} for b in SKEMA_BOBOT["lengkap"]
)
BOBOT_TANGGUNGAN, BOBOT_TANPA = SKEMA_BOBOT["proposal"]   # nama lama, dipakai pengujian

# Selisih pengalaman (tahun) yang membuat kesiapan menjadi nol.
JARAK_PENGALAMAN_MAKS = 3.0

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
    bidang: dict[str, float] | None = None   # minat per bidang TI, 0 - 1; None = tidak ditanyakan
    pengalaman: float | None = None    # tahun pengalaman kerja/magang di TI; None = tidak ditanyakan


# ── Penyaring mutlak ────────────────────────────────────────────────────────
def alasan_tersaring(profil: ProfilPengguna, profesi: dict, relokasi: bool = False) -> list[dict]:
    """Daftar kosong berarti profesi lolos.

    Penyaring relokasi (dari buku proposal) bawaannya MATI. Data lokasi berasal
    dari tempat lowongan terbanyak, bukan dari tempat lowongan itu mustahil
    ada: menyaring Mobile Developer bagi orang di luar lima kota besar berarti
    menyatakan sesuatu yang tidak didukung datanya. Sebagai gantinya pengguna
    diberi catatan (lihat catatan_lokasi) dan profesinya tetap dinilai.
    """
    alasan = []
    if profil.rank_pendidikan < profesi["pendidikan_min_rank"]:
        alasan.append({
            "kode": "pendidikan",
            "pesan": f"Syarat pendidikan minimum {profesi['pendidikan_min_label']}.",
        })
    if relokasi and not profil.bersedia_relokasi and not _terjangkau(profil.domisili, profesi):
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


def catatan_lokasi(profil: ProfilPengguna, profesi: dict) -> str | None:
    """Catatan untuk pengguna yang kotanya bukan pusat lowongan profesi ini.
    Hanya keterangan; tidak mengubah skor maupun peringkat."""
    if _terjangkau(profil.domisili, profesi):
        return None
    kota = ", ".join(profesi["lokasi"])
    if profil.bersedia_relokasi:
        return f"Lowongannya paling banyak di {kota}. Kamu bersedia pindah, jadi ini bukan halangan."
    return (f"Lowongannya paling banyak di {kota} dan umumnya tidak jarak jauh. "
            "Di kotamu peluangnya mungkin lebih sedikit; cek lowongan setempat.")


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


def minat_bidang(minat: dict[str, float] | None, bidang_profesi: dict[str, float]) -> float | None:
    """Rata-rata berbobot minat pengguna pada bidang-bidang profesi ini."""
    if not minat:
        return None
    return sum(b * minat.get(k, 0.0) for k, b in bidang_profesi.items()) / sum(bidang_profesi.values())


def kesiapan_pengalaman(pengalaman: float | None, minimum: int) -> float | None:
    """1 kalau pengalaman memenuhi syarat minimum profesi, turun linear sampai
    0 saat kurang tiga tahun atau lebih."""
    if pengalaman is None:
        return None
    return max(0.0, 1.0 - max(0.0, minimum - pengalaman) / JARAK_PENGALAMAN_MAKS)


# ── Skor KBF ────────────────────────────────────────────────────────────────
def skor_kbf(profil: ProfilPengguna, profesi: dict, metode_riasec: str = "korelasi",
             skema: str = "lengkap") -> dict:
    if metode_riasec == "iachan":
        riasec = kongruensi_iachan(kode_holland(profil.riasec), profesi["kode_holland"])
    elif metode_riasec == "korelasi":
        riasec = kongruensi_korelasi(profil.riasec, profesi["riasec"])
    else:
        raise ValueError(f"metode_riasec tidak dikenal: {metode_riasec}")

    if skema not in SKEMA_BOBOT:
        raise ValueError(f"skema bobot tidak dikenal: {skema}")
    nilai = {
        "riasec": riasec,
        "bidang": minat_bidang(profil.bidang, profesi["bidang"]),
        "big5": kecocokan_big5(profil.big5, profesi["big5_ideal"]),
        "kesiapan": kesiapan_pengalaman(profil.pengalaman, profesi["pengalaman_min_tahun"]),
        "finansial": kecocokan_finansial(profil.ekspektasi_gaji, profesi["gaji_min"], profesi["gaji_maks"]),
        "stabilitas": profesi["stabilitas"],
    }
    dasar = SKEMA_BOBOT[skema][0 if profil.punya_tanggungan else 1]
    # Komponen tanpa data dilewati; bobot sisanya dinormalkan supaya tetap berjumlah 1.
    aktif = {k: b for k, b in dasar.items() if nilai[k] is not None}
    total = sum(aktif.values())
    bobot = {k: round(b / total, 4) for k, b in aktif.items()}
    skor = sum(bobot[k] * nilai[k] for k in bobot)
    return {
        "skor": round(skor, 4),
        "komponen": {k: round(nilai[k], 4) for k in bobot},
        "bobot": bobot,
    }


def saring(profil: ProfilPengguna, kb: BasisPengetahuan,
           relokasi: bool = False) -> tuple[list[dict], list[dict]]:
    """Memisahkan profesi yang lolos dari yang tersaring."""
    lolos, tersaring = [], []
    for p in kb.profesi:
        alasan = alasan_tersaring(profil, p, relokasi)
        if alasan:
            tersaring.append({"profesi_id": p["id"], "nama": p["nama"], "alasan": alasan})
        else:
            lolos.append(p)
    return lolos, tersaring
