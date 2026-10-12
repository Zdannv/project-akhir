"""Metrik evaluasi dari data responden.

Dipakai dua pihak: scripts/evaluasi.py (laporan untuk naskah) dan dasbor
peneliti di aplikasi. Keduanya memanggil fungsi yang sama, jadi angkanya tidak
mungkin berbeda.
"""

from __future__ import annotations

import statistics
from collections import Counter

from . import kuesioner as q
from . import penyimpanan as db
from .hibrida import Konfigurasi, peringkat
from .kb import BIG5, RIASEC, BasisPengetahuan
from .kbf import ProfilPengguna

K = (1, 3, 5)

KONFIG_ABLASI = {
    "KBF saja (α = 1,0)": Konfigurasi(alpha=1.0),
    "CBF saja (α = 0,0)": Konfigurasi(alpha=0.0),
    "Hibrida (α = 0,6)": Konfigurasi(alpha=0.6),
}


def metrik(posisi: list[int | None]) -> dict:
    """posisi: peringkat jawaban benar tiap kasus (None = tidak masuk daftar)."""
    n = len(posisi)
    hasil = {f"hit@{k}": sum(1 for r in posisi if r and r <= k) / n for k in K}
    hasil["mrr"] = sum(1 / r for r in posisi if r) / n
    return hasil


def posisi_profesi(profil: ProfilPengguna, target: str, kb: BasisPengetahuan,
                   konfig: Konfigurasi) -> int | None:
    semua, _ = peringkat(profil, kb, konfig)
    return next((b["peringkat"] for b in semua if b["profesi_id"] == target), None)


def profil_dari_masukan(m: dict, kb: BasisPengetahuan) -> ProfilPengguna:
    return ProfilPengguna(
        riasec=q.skor_riasec(m["riasec"]), big5=q.skor_big5(m["big5"]),
        rank_pendidikan=kb.rank_jenjang(m["jenjang"]), domisili=m["domisili"],
        bersedia_relokasi=m["bersedia_relokasi"], ekspektasi_gaji=m["ekspektasi_gaji"],
        punya_tanggungan=m["punya_tanggungan"], skill=m["skill"],
    )


def cronbach_alpha(butir: list[list[int]]) -> float | None:
    """butir[i][j]: jawaban responden j pada butir i."""
    k, n = len(butir), len(butir[0]) if butir else 0
    if k < 2 or n < 2:
        return None
    total = [sum(b[j] for b in butir) for j in range(n)]
    var_total = statistics.variance(total)
    if var_total == 0:
        return None
    return k / (k - 1) * (1 - sum(statistics.variance(b) for b in butir) / var_total)


def data_responden(kb: BasisPengetahuan) -> dict | None:
    """Semua metrik pengujian. Hanya isian TERAKHIR tiap orang yang dihitung:
    isian yang sudah diperbarui lewat "ubah jawaban" tidak dihitung dua kali."""
    if not db.berkas_db().exists():
        return None
    db.siapkan()  # basis data dari versi lama dimutakhirkan dulu
    responden = db.responden_terakhir()
    if not responden:
        return None

    pakar = [r for r in responden if r["profesi_aktual"]]
    hasil: dict = {"n": len(responden), "n_pakar": len(pakar)}

    if pakar:
        hasil["pakar"] = {
            nama: metrik([posisi_profesi(profil_dari_masukan(r["masukan"], kb), r["profesi_aktual"], kb, k)
                          for r in pakar])
            for nama, k in KONFIG_ABLASI.items()
        }

    # Precision@K dari penilaian relevansi: hanya responden yang menilai semua
    # K rekomendasi teratasnya, supaya penyebutnya benar-benar K.
    presisi = {}
    for k in K:
        nilai = []
        for r in responden:
            teratas = [b["profesi_id"] for b in r["hasil"]["rekomendasi"][:k]]
            if len(teratas) == k and all(p in r["umpan_balik"] for p in teratas):
                nilai.append(sum(r["umpan_balik"][p] for p in teratas) / k)
        presisi[k] = (statistics.mean(nilai), len(nilai)) if nilai else None
    hasil["presisi"] = presisi

    sus = [r["skor_sus"] for r in responden if r["skor_sus"] is not None]
    hasil["sus"] = (statistics.mean(sus), len(sus)) if sus else None

    reliabilitas = {}
    for tipe in RIASEC:
        kode = [k for k, t, _ in q.BUTIR_RIASEC if t == tipe]
        reliabilitas[f"RIASEC {tipe}"] = cronbach_alpha(
            [[r["masukan"]["riasec"][k] for r in responden] for k in kode])
    for dim in BIG5:
        butir = [(k, tb) for k, d, tb, _ in q.BUTIR_BIG5 if d == dim]
        reliabilitas[f"Big Five {dim}"] = cronbach_alpha(
            [[(6 - r["masukan"]["big5"][k]) if tb else r["masukan"]["big5"][k] for r in responden]
             for k, tb in butir])
    hasil["reliabilitas"] = reliabilitas

    # Skill yang diketik sendiri karena tidak ada di pilihan: daftar belanja
    # untuk memperluas basis pengetahuan.
    luar = Counter(s.strip().lower() for r in responden for s in r["masukan"].get("skill_lain", []))
    hasil["skill_lain"] = luar.most_common(30)
    hasil["n_skill"] = statistics.mean(len(r["masukan"]["skill"]) for r in responden)
    return hasil
