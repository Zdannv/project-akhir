"""Tahap 2b — Content-Based Filtering pada skill.

Pengguna dan profesi diletakkan di ruang vektor yang sama, satu dimensi per
skill:

  * vektor profesi  : bobot kepentingan skill di profesi itu (skill_weight_pct);
  * vektor pengguna : tingkat penguasaan, 1/3 (dasar), 2/3 (menengah), 1 (mahir).

Dua ukuran dihitung dari kedua vektor itu:

  kosinus   cosine similarity: seberapa SEARAH skill pengguna dengan kebutuhan
            profesi. Tidak peka terhadap banyaknya skill, jadi orang dengan
            tiga skill yang semuanya penting bisa mendapat 60% walaupun baru
            menguasai sebagian kecil kebutuhan profesi.
  cakupan   porsi bobot skill profesi yang sudah dikuasai (memperhitungkan
            tingkat): seberapa LENGKAP. Tidak peka terhadap fokus, jadi orang
            yang memilih semua skill mendapat cakupan tinggi di semua profesi.

Skor CBF bawaan ("gabungan") adalah rata-rata geometrik keduanya,
akar(kosinus x cakupan): tinggi hanya kalau skill-nya searah DAN cukup
lengkap. Di simulasi akurasi peringkatnya setara dengan cosine murni (selisih
di bawah 1,5 poin, lebih baik untuk pemula), tetapi angkanya tidak lagi
bertentangan dengan cakupan yang ditampilkan ke pengguna. Cosine murni
("kosinus") adalah ukuran di buku proposal dan tetap tersedia sebagai pembanding.

Karena cosine tidak peka terhadap panjang vektor, bobot profesi tidak perlu
berjumlah 100.

Ruang vektornya bisa dipilih:

  "global" (bawaan)  cosine pada seluruh kosakata skill, sesuai rumus di
                     proposal. Skill pengguna di luar profesi ikut memperpanjang
                     vektornya, jadi profesi yang hanya memakai sebagian kecil
                     skill pengguna tidak otomatis mendapat skor tinggi.

  "profesi"          cosine hanya pada skill yang diminta profesi itu. Skill
                     lain tidak mengurangi skor, tetapi daya bedanya turun:
                     profesi dengan daftar skill pendek mudah terlihat "cocok".

Di simulasi (docs/hasil-evaluasi.md, bagian A.4) ruang global lebih akurat,
juga untuk persona yang skill-nya banyak, sehingga ia dipertahankan. Harganya:
cosine mengukur KEMIRIPAN ARAH, bukan banyaknya skill, jadi menambah skill
berbobot kecil bisa sedikit menurunkan skornya. Karena itu kemajuan belajar di
roadmap ditampilkan dengan `cakupan` (porsi bobot skill profesi yang sudah
dikuasai), yang selalu naik saat skill bertambah.

Skill profesi yang bobotnya 0 di data sumber tidak menjadi dimensi vektor; ia
tetap tampil di analisis kesenjangan.

Selain skor, modul ini menghasilkan analisis kesenjangan skill (skill gap):
skill profesi yang belum dimiliki, diurutkan dari yang wajib dan paling berat.
"""

from __future__ import annotations

import math

TINGKAT_MAKS = 3
LABEL_TINGKAT = {1: "Dasar", 2: "Menengah", 3: "Mahir"}


def skor_cbf(skill_pengguna: dict[str, int], skill_profesi: list[dict],
             ruang: str = "global", ukuran: str = "gabungan") -> dict:
    if ruang not in ("profesi", "global"):
        raise ValueError(f"ruang_cbf tidak dikenal: {ruang}")
    if ukuran not in ("gabungan", "kosinus"):
        raise ValueError(f"ukuran_cbf tidak dikenal: {ukuran}")
    w = {s["skill_id"]: s["bobot"] for s in skill_profesi if s["bobot"] > 0}
    u = {sid: t / TINGKAT_MAKS for sid, t in skill_pengguna.items()
         if t > 0 and (ruang == "global" or sid in w)}

    norma_u = math.sqrt(sum(v * v for v in u.values()))
    norma_w = math.sqrt(sum(v * v for v in w.values()))
    titik = sum(u[s] * w[s] for s in u.keys() & w.keys())
    kosinus = titik / (norma_u * norma_w) if norma_u and norma_w else 0.0

    cakupan = titik / sum(w.values()) if w else 0.0
    skor = math.sqrt(kosinus * cakupan) if ukuran == "gabungan" else kosinus
    return {"skor": round(skor, 4), "kosinus": round(kosinus, 4), "cakupan": round(cakupan, 4)}


def kesenjangan_skill(skill_pengguna: dict[str, int], skill_profesi: list[dict],
                      nama_skill: dict[str, str]) -> dict:
    dimiliki, belum = [], []
    for s in sorted(skill_profesi, key=lambda s: (not s["wajib"], -s["bobot"])):
        tingkat = skill_pengguna.get(s["skill_id"], 0)
        butir = {
            "skill_id": s["skill_id"],
            "nama": nama_skill[s["skill_id"]],
            "wajib": s["wajib"],
            "bobot": s["bobot"],
            # Di data sumber catatan sering hanya mengulang nama skill.
            "catatan": s["catatan"] if (s["catatan"] or "").strip().lower() != nama_skill[s["skill_id"]].lower() else None,
        }
        if tingkat > 0:
            dimiliki.append({**butir, "tingkat": tingkat, "label_tingkat": LABEL_TINGKAT[tingkat]})
        else:
            belum.append(butir)
    wajib = [s for s in skill_profesi if s["wajib"]]
    return {
        "dimiliki": dimiliki,
        "belum": belum,
        "wajib_terpenuhi": sum(1 for s in wajib if skill_pengguna.get(s["skill_id"], 0) > 0),
        "wajib_total": len(wajib),
    }
