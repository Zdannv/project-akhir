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
from . import statistik as st
from .hibrida import KONFIG_PROPOSAL, Konfigurasi, peringkat
from .kb import BIG5, RIASEC, BasisPengetahuan, campur_riasec, dengan_riasec
from .kbf import ProfilPengguna, saring
from .sus import BUTIR_PENJELASAN

K = (1, 3, 5)

NAMA_BAWAAN = "Hibrida bawaan (korelasi, α = 0,5)"
KONFIG_ABLASI = {
    "KBF saja (korelasi, α = 1,0)": Konfigurasi(alpha=1.0),
    "CBF saja (α = 0,0)": Konfigurasi(alpha=0.0),
    NAMA_BAWAAN: Konfigurasi(),
    "Hibrida tanpa minat bidang dan kesiapan (α = 0,5)": Konfigurasi(skema_bobot="proposal"),
    "Hibrida dengan cosine murni (α = 0,5)": Konfigurasi(ukuran_cbf="kosinus"),
    "Hibrida proposal (Iachan, α = 0,6)": KONFIG_PROPOSAL,
    "Hibrida tanpa RIASEC (α = 0,5)": Konfigurasi(skema_bobot="tanpa_riasec"),
}

# Baseline: cara merekomendasikan yang lebih sederhana, sebagai pembanding.
# "RIASEC saja" setara pendekatan penelitian terdahulu yang hanya memakai minat.
KONFIG_BASELINE = {
    "Baseline: RIASEC saja (indeks Iachan)": Konfigurasi(alpha=1.0, metode_riasec="iachan", skema_bobot="riasec"),
    "Baseline: RIASEC saja (korelasi)": Konfigurasi(alpha=1.0, skema_bobot="riasec"),
}
NAMA_ACAK = "Baseline: acak (nilai harapan)"
NAMA_LOKAL = "Hibrida, profil RIASEC dikalibrasi responden lokal (leave-one-out)"
K_SUSUT = 5.0  # bobot profil O*NET dalam penyusutan, setara 5 responden

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
        # Isian lama belum punya dua pertanyaan ini; None membuat komponennya dilewati.
        bidang={k: (v - 1) / 4 for k, v in m["bidang"].items()} if m.get("bidang") else None,
        pengalaman=m.get("pengalaman_tahun"),
    )


def metrik_lengkap(posisi: list[int | None]) -> dict:
    """Metrik + selang kepercayaan 95% (bootstrap) untuk Hit@5 dan MRR."""
    hasil = metrik(posisi)
    hit5 = [1.0 if r and r <= 5 else 0.0 for r in posisi]
    rr = [1 / r if r else 0.0 for r in posisi]
    hasil["ci_hit@5"] = st.bootstrap_ci(hit5)
    hasil["ci_mrr"] = st.bootstrap_ci(rr)
    return hasil


def metrik_acak(n_lolos: list[int]) -> dict:
    """Nilai harapan kalau urutan profesi diacak: Hit@K = K / m, MRR = H(m) / m."""
    hasil = {f"hit@{k}": statistics.mean(min(k, m) / m for m in n_lolos) for k in K}
    hasil["mrr"] = statistics.mean(sum(1 / i for i in range(1, m + 1)) / m for m in n_lolos)
    return hasil


def _riasec_lokal_loo(kasus: list[tuple[ProfilPengguna, str]], kb: BasisPengetahuan,
                      i: int, k: float = K_SUSUT) -> BasisPengetahuan:
    """Basis pengetahuan dengan profil RIASEC profesi disusutkan ke rata-rata
    responden profesional lain (responden ke-i sendiri tidak ikut)."""
    per_profesi: dict[str, list[dict]] = {}
    for j, (profil, target) in enumerate(kasus):
        if j != i:
            per_profesi.setdefault(target, []).append(profil.riasec)
    profil_baru = {pid: campur_riasec(kb.cari_profesi(pid)["riasec"], daftar, k)
                   for pid, daftar in per_profesi.items() if kb.cari_profesi(pid)}
    return dengan_riasec(kb, profil_baru)


def uji_pakar(kasus: list[tuple[ProfilPengguna, str]], kb: BasisPengetahuan) -> dict:
    """Hit Rate dan MRR terhadap profesi aktual responden profesional,
    untuk konfigurasi sistem dan baseline, beserta uji berpasangan terhadap
    konfigurasi bawaan."""
    konfig = KONFIG_ABLASI | KONFIG_BASELINE
    posisi = {nama: [posisi_profesi(p, t, kb, k) for p, t in kasus] for nama, k in konfig.items()}
    posisi[NAMA_LOKAL] = [posisi_profesi(p, t, _riasec_lokal_loo(kasus, kb, i), Konfigurasi())
                          for i, (p, t) in enumerate(kasus)]
    hasil = {nama: metrik_lengkap(pos) for nama, pos in posisi.items()}
    hasil[NAMA_ACAK] = metrik_acak([len(saring(p, kb)[0]) for p, _ in kasus])

    acuan = posisi[NAMA_BAWAAN]
    hit = lambda pos: [bool(r and r <= 5) for r in pos]  # noqa: E731
    rr = lambda pos: [1 / r if r else 0.0 for r in pos]  # noqa: E731
    uji = {}
    for nama, pos in posisi.items():
        if nama == NAMA_BAWAAN:
            continue
        uji[nama] = {"mcnemar_hit@5": st.mcnemar(hit(acuan), hit(pos)),
                     "wilcoxon_rr": st.wilcoxon(rr(acuan), rr(pos))}
    return {"metrik": hasil, "uji": uji, "n": len(kasus)}


def ringkas_penjelasan(responden: list[dict]) -> dict | None:
    """Rata-rata tiap butir evaluasi penjelasan (skala 1 - 5)."""
    isi = [r["penjelasan"] for r in responden if r.get("penjelasan")]
    if not isi:
        return None
    rata_orang = [statistics.mean(j) for j in isi]
    return {
        "n": len(isi),
        "butir": [(teks, statistics.mean(j[i] for j in isi)) for i, teks in enumerate(BUTIR_PENJELASAN)],
        "rata": statistics.mean(rata_orang),
        "ci": st.bootstrap_ci(rata_orang),
        "setuju": sum(1 for x in rata_orang if x >= 4) / len(isi),
    }


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
    if not db.tersedia():
        return None
    db.siapkan()  # basis data dari versi lama dimutakhirkan dulu
    responden = db.responden_terakhir()
    if not responden:
        return None

    pakar = [r for r in responden if r["profesi_aktual"]]
    hasil: dict = {"n": len(responden), "n_pakar": len(pakar)}

    if pakar:
        kasus = [(profil_dari_masukan(r["masukan"], kb), r["profesi_aktual"]) for r in pakar]
        uji = uji_pakar(kasus, kb)
        # "pakar" dipertahankan bentuknya untuk dasbor; rinciannya di "pakar_uji".
        hasil["pakar"] = {nama: {k: m[k] for k in ("hit@1", "hit@3", "hit@5", "mrr")}
                          for nama, m in uji["metrik"].items()}
        hasil["pakar_uji"] = uji

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
    hasil["sus_ci"] = st.bootstrap_ci(sus) if sus else None
    hasil["penjelasan"] = ringkas_penjelasan(responden)

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
