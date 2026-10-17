"""Evaluasi mesin rekomendasi.

Dua bagian yang sengaja dipisah karena kekuatan buktinya berbeda:

  A. SIMULASI — persona sintetis yang dibangkitkan dari basis pengetahuan.
     Menjawab: apakah mesin konsisten, dan apa sumbangan tiap komponen?
     (KBF saja vs CBF saja vs hibrida, kepekaan terhadap alpha, Iachan vs
     korelasi.) Karena personanya berasal dari data yang sama dengan yang
     dipakai mesin, angka di sini adalah BATAS ATAS dan BUKAN bukti akurasi
     pada manusia.

  B. DATA RESPONDEN — jawaban sungguhan yang tersimpan di SQLite.
     Menjawab pertanyaan pengujian di buku proposal: Hit Rate@5 terhadap
     profesi aktual responden profesional, Precision@K dari penilaian
     relevansi, skor SUS, dan reliabilitas kuesioner (Cronbach's alpha).
     Karena jawaban mentahnya disimpan, perbandingan konfigurasi di bagian A
     diulang juga di sini.

Jalankan:  python scripts/evaluasi.py [--persona 40] [--seed 42] [--lowongan jobs.xlsx]
Keluaran:  docs/hasil-evaluasi.md dan docs/hasil-evaluasi.json

  C. LOWONGAN NYATA — lowongan LinkedIn mentah sebagai kasus uji di luar
     simulasi (app/lowongan.py). Menguji sisi keahlian pada teks lowongan
     apa adanya.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import statistik as st  # noqa: E402
from app.evaluasi import (KONFIG_ABLASI, KONFIG_BASELINE, MIN_RELIABILITAS, NAMA_ACAK, NAMA_BAWAAN,  # noqa: E402
                          NAMA_LOKAL,
                          data_responden, metrik, metrik_acak, metrik_ci, posisi_jaccard, posisi_profesi,
                          uji_berpasangan)
from app.hibrida import peringkat  # noqa: E402
from app.lowongan import baca_lowongan  # noqa: E402
from app.kbf import saring  # noqa: E402
from app.hibrida import Konfigurasi  # noqa: E402
from app.kb import AKAR, BIG5, RIASEC, BasisPengetahuan, muat_kb  # noqa: E402
from app.kbf import ProfilPengguna  # noqa: E402

KELUARAN = AKAR / "docs" / "hasil-evaluasi.md"
KELUARAN_JSON = AKAR / "docs" / "hasil-evaluasi.json"
# Data mentah scraping disimpan di luar repositori (lihat docs/bukti-data/README.md).
BERKAS_LOWONGAN = Path.home() / "Downloads" / "jobs.xlsx"


def jepit(x: float) -> float:
    return max(0.0, min(1.0, x))


# ── A. Simulasi ─────────────────────────────────────────────────────────────
def persona(p: dict, kb: BasisPengetahuan, acak: random.Random,
            sigma: float, semua_skill: list[str], n_derau: int = 2,
            peluang: tuple[float, float] = (0.75, 0.35), n_skill: int | None = None,
            pengalaman: float | None = None, tanggungan: bool | None = None) -> ProfilPengguna:
    """Satu orang rekaan yang 'cocok' dengan profesi p, dengan derau.

    Minat dan kepribadian: profil profesi + derau Gauss. Skill: sebagian skill
    wajib (peluang 0,75) dan pilihan (0,35) profesi itu, ditambah dua skill
    acak yang tidak berhubungan — orang sungguhan tidak pernah punya persis
    daftar skill sebuah lowongan.

    Varian untuk uji yang lebih sulit:
      n_skill     pemula: hanya sekian skill profesi (wajib didahulukan)
      pengalaman  tahun pengalaman tetap, misalnya 0 untuk mahasiswa
      tanggungan  memaksa ada/tidaknya tanggungan keluarga
    """
    riasec = {t: jepit((p["riasec"][t] - 1) / 6 + acak.gauss(0, sigma)) for t in RIASEC}
    big5 = {d: jepit(p["big5_ideal"][d] + acak.gauss(0, sigma)) for d in BIG5}
    skill = {}
    milik = kb.skill_profesi(p["id"])
    if n_skill is None:
        for s in milik:
            if acak.random() < (peluang[0] if s["wajib"] else peluang[1]):
                skill[s["skill_id"]] = acak.choice((1, 2, 2, 3))
    else:
        wajib = [s["skill_id"] for s in milik if s["wajib"]]
        pilihan = [s["skill_id"] for s in milik if not s["wajib"]]
        acak.shuffle(wajib); acak.shuffle(pilihan)
        for sid in (wajib + pilihan)[:n_skill]:
            skill[sid] = acak.choice((1, 1, 2))
    for sid in acak.sample(semua_skill, n_derau):
        skill.setdefault(sid, acak.choice((1, 2)))
    # Minat bidang: bobot bidang profesi + derau. Pengalaman bawaan: memenuhi
    # syarat profesi asalnya, karena persona ini memang "orang yang cocok" di sana.
    bidang = {b["kode"]: jepit(p["bidang"].get(b["kode"], 0.2) + acak.gauss(0, 2 * sigma)) for b in kb.bidang}
    if pengalaman is None:
        pengalaman = p["pengalaman_min_tahun"] + acak.choice((0, 0.5, 1.5))
    return ProfilPengguna(
        bidang=bidang, pengalaman=pengalaman,
        riasec=riasec, big5=big5,
        rank_pendidikan=max(p["pendidikan_min_rank"], 4),
        domisili="Jakarta", bersedia_relokasi=True,
        ekspektasi_gaji=p["gaji_min"],
        punya_tanggungan=acak.random() < 0.3 if tanggungan is None else tanggungan,
        skill=skill,
    )


def posisi_semua(kasus: list, kb: BasisPengetahuan, konfig: dict) -> dict[str, list]:
    """Peringkat jawaban benar per kasus untuk tiap konfigurasi. Nilai konfig
    berupa Konfigurasi, atau "jaccard" untuk baseline Jaccard."""
    hasil = {}
    for nama, k in konfig.items():
        if k == "jaccard":
            hasil[nama] = [posisi_jaccard(pr, pid, kb) for pid, pr in kasus]
        else:
            hasil[nama] = [posisi_profesi(pr, pid, kb, k) for pid, pr in kasus]
    return hasil


def ringkas(posisi: dict[str, list], acuan: str | None = None, k_uji: int = 1) -> dict:
    """Metrik dengan CI tiap konfigurasi, dan uji berpasangan terhadap `acuan`."""
    out = {nama: metrik_ci(pos) for nama, pos in posisi.items()}
    if acuan:
        for nama, pos in posisi.items():
            if nama != acuan:
                out[nama]["uji"] = uji_berpasangan(posisi[acuan], pos, k_uji)
    return out


NAMA_JACCARD = "Baseline: kecocokan keahlian Jaccard"
NAMA_TANPA_BIDANG = "Hibrida tanpa minat bidang"
NAMA_TANPA_KESIAPAN = "Hibrida tanpa kesiapan pengalaman"
NAMA_TANPA_STABILITAS = "Hibrida tanpa stabilitas kerja"


def simulasi(kb: BasisPengetahuan, n_persona: int, seed: int, sigma: float) -> dict:
    acak = random.Random(seed)
    semua_skill = [s["id"] for s in kb.skill]
    kasus = [(p["id"], persona(p, kb, acak, sigma, semua_skill))
             for p in kb.profesi for _ in range(n_persona)]

    def jalankan(konfig: Konfigurasi) -> dict:
        return metrik([posisi_profesi(pr, pid, kb, konfig) for pid, pr in kasus])

    # Persona "generalis": profil yang sama kuatnya, tetapi punya 15 skill lain
    # di luar profesinya. Menguji seberapa tahan tiap ruang CBF terhadap orang
    # yang skill-nya banyak.
    acak_g = random.Random(seed)
    generalis = [(p["id"], persona(p, kb, acak_g, sigma, semua_skill, n_derau=15))
                 for p in kb.profesi for _ in range(n_persona)]

    def jalankan_di(daftar: list, konfig: Konfigurasi) -> dict:
        return metrik([posisi_profesi(pr, pid, kb, konfig) for pid, pr in daftar])

    ruang = {}
    for nama_set, daftar in (("spesialis (2 skill lain)", kasus), ("generalis (15 skill lain)", generalis)):
        for r in ("profesi", "global"):
            ruang[f"CBF saja, ruang {r} — {nama_set}"] = jalankan_di(daftar, Konfigurasi(alpha=0.0, ruang_cbf=r))
            ruang[f"Hibrida, ruang {r} — {nama_set}"] = jalankan_di(daftar, Konfigurasi(ruang_cbf=r))

    ablasi_konfig = KONFIG_ABLASI | KONFIG_BASELINE | {NAMA_JACCARD: "jaccard"}
    ablasi = ringkas(posisi_semua(kasus, kb, ablasi_konfig), acuan=NAMA_BAWAAN)
    ablasi[NAMA_ACAK] = metrik_acak([len(saring(pr, kb)[0]) for _, pr in kasus])

    return {
        "ruang": ruang,
        "n": len(kasus),
        "ablasi": ablasi,
        "alpha": {a / 10: jalankan(Konfigurasi(alpha=a / 10)) for a in range(11)},
        "alpha_iachan": {a / 10: jalankan(Konfigurasi(alpha=a / 10, metode_riasec="iachan")) for a in range(11)},
        "riasec": {m: jalankan(Konfigurasi(metode_riasec=m)) for m in ("iachan", "korelasi")},
        "riasec_kbf": {m: jalankan(Konfigurasi(alpha=1.0, metode_riasec=m)) for m in ("iachan", "korelasi")},
        "derau": kurva_derau(kb, n_persona, seed),
        "pemula": uji_pemula(kb, n_persona, seed, sigma),
        "mahasiswa": uji_mahasiswa(kb, n_persona, seed, sigma),
        "tanggungan": uji_tanggungan(kb, n_persona, seed, sigma),
    }


KONFIG_KURVA = {
    NAMA_BAWAAN: Konfigurasi(),
    "KBF saja": Konfigurasi(alpha=1.0),
    "CBF saja": Konfigurasi(alpha=0.0),
    NAMA_JACCARD: "jaccard",
}


def kurva_derau(kb: BasisPengetahuan, n_persona: int, seed: int) -> dict:
    """Seberapa cepat ketepatan turun ketika persona makin jauh dari profil
    profesinya: (1) derau minat dan kepribadian dibesarkan, (2) keahlian yang
    dimiliki makin sedikit."""
    semua_skill = [s["id"] for s in kb.skill]
    n = max(10, n_persona // 2)
    hasil = {"sigma": {}, "kelengkapan": {}}
    for sigma in (0.06, 0.12, 0.20, 0.30, 0.40):
        acak = random.Random(seed)
        kasus = [(p["id"], persona(p, kb, acak, sigma, semua_skill)) for p in kb.profesi for _ in range(n)]
        hasil["sigma"][sigma] = {nama: metrik(pos) for nama, pos in posisi_semua(kasus, kb, KONFIG_KURVA).items()}
    for skala in (1.0, 0.6, 0.35, 0.15):
        acak = random.Random(seed)
        kasus = [(p["id"], persona(p, kb, acak, 0.20, semua_skill, peluang=(0.75 * skala, 0.35 * skala)))
                 for p in kb.profesi for _ in range(n)]
        hasil["kelengkapan"][skala] = {nama: metrik(pos) for nama, pos in posisi_semua(kasus, kb, KONFIG_KURVA).items()}
    return hasil


def uji_pemula(kb: BasisPengetahuan, n_persona: int, seed: int, sigma: float) -> dict:
    """Hipotesis H1: pada pengguna dengan sedikit keahlian (2–4), komponen minat
    bidang kerja TI menaikkan ketepatan. Pengalaman dibuat memenuhi syarat
    supaya yang diuji hanya minat bidang. Uji McNemar pada Hit@3."""
    acak = random.Random(seed + 1)
    semua_skill = [s["id"] for s in kb.skill]
    kasus = [(p["id"], persona(p, kb, acak, sigma, semua_skill, n_skill=acak.choice((2, 3, 4))))
             for p in kb.profesi for _ in range(n_persona)]
    konfig = {NAMA_BAWAAN: Konfigurasi(), NAMA_TANPA_BIDANG: Konfigurasi(skema_bobot="tanpa_bidang"),
              "KBF saja": Konfigurasi(alpha=1.0), "CBF saja": Konfigurasi(alpha=0.0),
              NAMA_JACCARD: "jaccard"}
    return {"n": len(kasus), "hasil": ringkas(posisi_semua(kasus, kb, konfig), acuan=NAMA_BAWAAN, k_uji=3)}


def uji_mahasiswa(kb: BasisPengetahuan, n_persona: int, seed: int, sigma: float) -> dict:
    """Hipotesis H2: bagi mahasiswa tanpa pengalaman, komponen kesiapan
    pengalaman menurunkan porsi profesi senior (syarat >= 2 tahun) di lima
    rekomendasi teratas tanpa menurunkan ketepatan untuk profesi tingkat awal."""
    acak = random.Random(seed + 2)
    semua_skill = [s["id"] for s in kb.skill]
    awal = [p for p in kb.profesi if p["pengalaman_min_tahun"] == 0]
    kasus = [(p["id"], persona(p, kb, acak, sigma, semua_skill, n_skill=acak.choice((3, 4, 5, 6)), pengalaman=0.0))
             for p in awal for _ in range(n_persona)]
    senior = {p["id"] for p in kb.profesi if p["pengalaman_min_tahun"] >= 2}
    konfig = {NAMA_BAWAAN: Konfigurasi(), NAMA_TANPA_KESIAPAN: Konfigurasi(skema_bobot="tanpa_kesiapan")}
    posisi = posisi_semua(kasus, kb, konfig)
    hasil = ringkas(posisi, acuan=NAMA_BAWAAN, k_uji=3)
    for nama, k in konfig.items():
        porsi = []
        for _, pr in kasus:
            semua, _ = peringkat(pr, kb, k)
            porsi.append(sum(1 for b in semua[:5] if b["profesi_id"] in senior) / 5)
        hasil[nama]["porsi_senior"] = statistics.mean(porsi)
        hasil[nama]["_porsi"] = porsi
    a, b = hasil[NAMA_BAWAAN].pop("_porsi"), hasil[NAMA_TANPA_KESIAPAN].pop("_porsi")
    hasil[NAMA_TANPA_KESIAPAN]["uji_porsi"] = st.wilcoxon(a, b)
    return {"n": len(kasus), "n_profesi": len(awal), "n_senior": len(senior), "hasil": hasil}


def uji_tanggungan(kb: BasisPengetahuan, n_persona: int, seed: int, sigma: float) -> dict:
    """Besar pengaruh indeks stabilitas (proksi) bagi pengguna bertanggungan:
    berapa persen daftar lima teratas berubah kalau komponen itu dibuang."""
    acak = random.Random(seed + 3)
    semua_skill = [s["id"] for s in kb.skill]
    kasus = [(p["id"], persona(p, kb, acak, sigma, semua_skill, tanggungan=True))
             for p in kb.profesi for _ in range(n_persona)]
    konfig = {NAMA_BAWAAN: Konfigurasi(), NAMA_TANPA_STABILITAS: Konfigurasi(skema_bobot="tanpa_stabilitas")}
    hasil = ringkas(posisi_semua(kasus, kb, konfig), acuan=NAMA_BAWAAN)
    berubah = 0
    for _, pr in kasus:
        a = [b["profesi_id"] for b in peringkat(pr, kb, konfig[NAMA_BAWAAN])[0][:5]]
        b = [b["profesi_id"] for b in peringkat(pr, kb, konfig[NAMA_TANPA_STABILITAS])[0][:5]]
        berubah += set(a) != set(b)
    return {"n": len(kasus), "hasil": hasil, "top5_berubah": berubah / len(kasus)}


# ── C. Lowongan nyata ───────────────────────────────────────────────────────
def uji_lowongan(kb: BasisPengetahuan, berkas: Path) -> dict | None:
    """Kasus uji dari lowongan LinkedIn mentah (lihat app/lowongan.py). Lowongan
    tidak memuat minat atau kepribadian, sehingga yang diuji adalah sisi keahlian
    (CBF) dan baselinenya."""
    if not berkas.exists():
        return None
    data = baca_lowongan(berkas, kb)
    kasus = [(d["profesi_id"], ProfilPengguna(
        riasec={t: 0.5 for t in RIASEC}, big5={d_: 0.5 for d_ in BIG5}, rank_pendidikan=6,
        domisili="Jakarta", bersedia_relokasi=True, ekspektasi_gaji=0, punya_tanggungan=False,
        skill={s: 2 for s in d["skill"]})) for d in data]

    # Variasi basis pengetahuan: hanya relasi keahlian yang berasal dari data
    # lowongan, tanpa 591 relasi hasil kurasi penulis.
    tanpa_kurasi = BasisPengetahuan({**kb.mentah, "profesi_skill": {
        pid: [r for r in rel if r["sumber"] == "lowongan"] for pid, rel in kb.mentah["profesi_skill"].items()}})

    posisi = posisi_semua(kasus, kb, {
        "CBF gabungan (bawaan)": Konfigurasi(alpha=0.0),
        "CBF cosine murni": Konfigurasi(alpha=0.0, ukuran_cbf="kosinus"),
        NAMA_JACCARD: "jaccard",
    })
    posisi["CBF gabungan, tanpa relasi kurasi"] = [
        posisi_profesi(pr, pid, tanpa_kurasi, Konfigurasi(alpha=0.0)) for pid, pr in kasus]
    # Baseline popularitas: selalu merekomendasikan profesi dengan lowongan
    # terbanyak di data (leave-one-out, jadi lowongan yang diuji tidak ikut dihitung).
    frek = Counter(pid for pid, _ in kasus)
    semua_id = [p["id"] for p in kb.profesi]
    pop = []
    for pid, _ in kasus:
        f = frek.copy(); f[pid] -= 1
        urut = sorted(semua_id, key=lambda x: (-f[x], x))
        pop.append(urut.index(pid) + 1)
    posisi["Baseline: profesi terpopuler"] = pop

    hasil = ringkas(posisi, acuan="CBF gabungan (bawaan)", k_uji=3)
    hasil[NAMA_ACAK] = metrik_acak([len(kb.profesi)] * len(kasus))
    per_profesi = {}
    for pid in sorted(frek):
        pos = [r for (t, _), r in zip(kasus, posisi["CBF gabungan (bawaan)"]) if t == pid]
        per_profesi[pid] = {"nama": kb.cari_profesi(pid)["nama"], **metrik_ci(pos), "n": len(pos)}
    # Matriks kebingungan peringkat pertama, untuk melihat profesi yang saling tertukar.
    tertukar = Counter()
    for pid, pr in kasus:
        atas = peringkat(pr, kb, Konfigurasi(alpha=0.0))[0][0]["profesi_id"]
        if atas != pid:
            tertukar[(pid, atas)] += 1
    return {"n": len(kasus), "n_skill_median": statistics.median(len(d["skill"]) for d in data),
            "hasil": hasil, "per_profesi": per_profesi,
            "tertukar": [(kb.cari_profesi(a)["nama"], kb.cari_profesi(b)["nama"], n) for (a, b), n in tertukar.most_common(6)]}


# ── Laporan ─────────────────────────────────────────────────────────────────
def pct(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def d(x: float, digit: int = 2) -> str:
    return f"{x:.{digit}f}".replace(".", ",")


def ci(pasangan) -> str:
    return f"{pct(pasangan[0])}–{pct(pasangan[1])}"


def p_teks(p: float) -> str:
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def tabel_pakar(uji: dict) -> list[str]:
    out = ["| Konfigurasi | Hit@1 | Hit@3 | Hit@5 (95% CI) | MRR (95% CI) |", "|---|---:|---:|---:|---:|"]
    for nama, m in uji["metrik"].items():
        hit5 = pct(m["hit@5"]) + (f" ({ci(m['ci_hit@5'])})" if "ci_hit@5" in m else "")
        mrr = f"{m['mrr']:.3f}".replace(".", ",") + (
            f" ({m['ci_mrr'][0]:.3f}–{m['ci_mrr'][1]:.3f})".replace(".", ",") if "ci_mrr" in m else "")
        out.append(f"| {nama} | {pct(m['hit@1'])} | {pct(m['hit@3'])} | {hit5} | {mrr} |")
    return out


def tabel_uji(uji: dict) -> list[str]:
    out = ["| Dibandingkan dengan hibrida bawaan | Hanya bawaan benar | Hanya pembanding benar | p McNemar (Hit@5) | p Wilcoxon (RR) |",
           "|---|---:|---:|---:|---:|"]
    for nama, u in uji["uji"].items():
        m, w = u["mcnemar_hit@5"], u["wilcoxon_rr"]
        out.append(f"| {nama} | {m['hanya_a']} | {m['hanya_b']} | {p_teks(m['p'])} | {p_teks(w['p'])} |")
    return out


def tabel_metrik(baris: dict) -> list[str]:
    out = ["| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |", "|---|---:|---:|---:|---:|"]
    for nama, m in baris.items():
        out.append(f"| {nama} | {pct(m['hit@1'])} | {pct(m['hit@3'])} | {pct(m['hit@5'])} | "
                   f"{m['mrr']:.3f} |".replace(".", ","))
    return out


def tabel_ci(baris: dict, k_uji: int = 1) -> list[str]:
    """Metrik dengan CI 95% dan p-value uji berpasangan terhadap acuan (kalau ada)."""
    out = [f"| Konfigurasi | Hit@1 (95% CI) | Hit@3 | Hit@5 | MRR (95% CI) | p McNemar Hit@{k_uji} | p Wilcoxon RR |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for nama, m in baris.items():
        h1 = pct(m["hit@1"]) + (f" ({ci(m['ci_hit@1'])})" if "ci_hit@1" in m else "")
        mrr = d(m["mrr"], 3) + (f" ({d(m['ci_mrr'][0], 3)}–{d(m['ci_mrr'][1], 3)})" if "ci_mrr" in m else "")
        u = m.get("uji")
        pm = p_teks(u["mcnemar"]["p"]) if u else "acuan" if "ci_mrr" in m else "–"
        pw = p_teks(u["wilcoxon"]["p"]) if u else "acuan" if "ci_mrr" in m else "–"
        out.append(f"| {nama} | {h1} | {pct(m['hit@3'])} | {pct(m['hit@5'])} | {mrr} | {pm} | {pw} |")
    return out


def tabel_kurva(kurva: dict, label: str) -> list[str]:
    nama = list(next(iter(kurva.values())))
    out = [f"| {label} | " + " | ".join(f"{n} Hit@1" for n in nama) + " |", "|---:|" + "---:|" * len(nama)]
    for x, baris in kurva.items():
        out.append(f"| {d(x)} | " + " | ".join(pct(baris[n]["hit@1"]) for n in nama) + " |")
    return out


def bagian_lanjut(sim: dict, low: dict | None) -> list[str]:
    pm, mh, tg, kv = sim["pemula"], sim["mahasiswa"], sim["tanggungan"], sim["derau"]
    L = ["### A.5 Kurva ketahanan terhadap derau", "",
         "Derau minat dan kepribadian (σ) dibesarkan; keahlian tetap seperti persona bawaan:", "",
         *tabel_kurva(kv["sigma"], "σ"), "",
         "Keahlian makin sedikit (peluang memiliki keahlian profesi dikalikan faktor), σ = 0,20:", "",
         *tabel_kurva(kv["kelengkapan"], "faktor keahlian"), "",
         "### A.6 H1: minat bidang pada pengguna berkeahlian sedikit", "",
         f"{pm['n']} persona dengan 2–4 keahlian profesi; pengalaman memenuhi syarat. Uji McNemar pada Hit@3.", "",
         *tabel_ci(pm["hasil"], 3), "",
         "### A.7 H2: kesiapan pengalaman bagi mahasiswa", "",
         f"{mh['n']} persona mahasiswa (pengalaman 0 tahun, 3–6 keahlian) dari {mh['n_profesi']} profesi tingkat awal. "
         f"Profesi senior = {mh['n_senior']} profesi bersyarat pengalaman ≥ 2 tahun.", "",
         *tabel_ci(mh["hasil"], 3), "",
         "| Konfigurasi | Porsi profesi senior di 5 teratas |", "|---|---:|",
         *[f"| {n} | {pct(m['porsi_senior'])} |" for n, m in mh["hasil"].items()], "",
         f"Wilcoxon porsi senior per persona: p = {p_teks(mh['hasil'][NAMA_TANPA_KESIAPAN]['uji_porsi']['p'])}.", "",
         "### A.8 Pengaruh indeks stabilitas (proksi) bagi pengguna bertanggungan", "",
         f"{tg['n']} persona bertanggungan.", "", *tabel_ci(tg["hasil"]), "",
         f"Daftar lima teratas berubah pada {pct(tg['top5_berubah'])} persona bila komponen stabilitas dibuang.", ""]
    L += ["## C. Uji pada lowongan nyata", ""]
    if low is None:
        L += ["Berkas lowongan mentah tidak ditemukan; bagian ini dilewati.", ""]
        return L
    L += [f"{low['n']} lowongan LinkedIn unik (April–Juli 2026) yang judulnya terpetakan ke profesi data/AI dan "
          f"menyebut ≥ 3 keahlian (median {d(low['n_skill_median'], 0)}). Keahlian yang disebut lowongan menjadi profil, "
          "judul lowongan menjadi jawaban benar, dan peringkat dihitung di antara 35 profesi. Uji McNemar pada Hit@3.", "",
          "> Sebagian relasi keahlian profesi data di basis pengetahuan diringkas dari lowongan yang sama, sehingga uji ini",
          "> belum sepenuhnya lepas; tetapi kasusnya teks lowongan apa adanya, bukan persona yang dibangkitkan mesin.", "",
          *tabel_ci(low["hasil"], 3), "",
          "| Profesi | n | Hit@1 | Hit@3 (95% CI) | MRR |", "|---|---:|---:|---:|---:|",
          *[f"| {m['nama']} | {m['n']} | {pct(m['hit@1'])} | {pct(m['hit@3'])} ({ci(m['ci_hit@3'])}) | {d(m['mrr'], 3)} |"
            for m in low["per_profesi"].values()], "",
          "Pasangan yang paling sering tertukar di peringkat pertama (jawaban benar → tebakan):", "",
          *[f"- {a} → {b}: {n} lowongan" for a, b, n in low["tertukar"]], ""]
    return L


def laporan(sim: dict, resp: dict | None, argumen: argparse.Namespace, kb: BasisPengetahuan,
            low: dict | None = None) -> str:
    L = [
        "# Hasil Evaluasi",
        "",
        "Dibuat otomatis oleh `backend/scripts/evaluasi.py`. Jangan disunting tangan; jalankan ulang skripnya.",
        "",
        "## A. Simulasi persona sintetis",
        "",
        f"{sim['n']} persona ({argumen.persona} per profesi × {len(kb.profesi)} profesi), "
        f"derau σ = {argumen.sigma}, seed {argumen.seed}. Tiap persona dibangkitkan dari satu profesi; "
        "mesin dinilai berhasil kalau profesi asal itu muncul di K teratas.",
        "",
        "> Persona berasal dari basis pengetahuan yang sama dengan yang dipakai mesin. Angka di bagian ini",
        "> menunjukkan konsistensi mesin dan sumbangan tiap komponen — **bukan** akurasi pada pengguna sungguhan.",
        "",
        "### A.1 Ablasi: sumbangan tiap komponen",
        "",
        "Selang kepercayaan 95%: Wilson untuk Hit@K, bootstrap 2000 sampel ulang untuk MRR. p-value dari uji",
        "berpasangan terhadap hibrida bawaan pada persona yang sama.",
        "",
        *tabel_ci(sim["ablasi"]),
        "",
        "### A.2 Kepekaan terhadap α",
        "",
        "Kongruensi minat berbasis korelasi (bawaan):",
        "",
        *tabel_metrik({f"α = {a:.1f}".replace(".", ","): m for a, m in sim["alpha"].items()}),
        "",
        "Kongruensi minat dengan indeks Iachan (proposal):",
        "",
        *tabel_metrik({f"α = {a:.1f}".replace(".", ","): m for a, m in sim["alpha_iachan"].items()}),
        "",
        "### A.3 Ukuran kongruensi RIASEC",
        "",
        *tabel_metrik({f"Hibrida, {m}": v for m, v in sim["riasec"].items()}
                      | {f"KBF saja, {m}": v for m, v in sim["riasec_kbf"].items()}),
        "",
        "### A.4 Ruang vektor CBF",
        "",
        "Cosine pada seluruh kosakata skill (`global`, bawaan) dibandingkan dengan cosine pada skill profesi",
        "saja (`profesi`), untuk persona spesialis dan generalis.",
        "",
        *tabel_metrik(sim["ruang"]),
        "",
        *bagian_lanjut(sim, low),
        "## B. Data responden",
        "",
    ]
    if resp is None:
        L += ["Belum ada responden di basis data. Bagian ini terisi setelah pengujian dengan "
              "mahasiswa dan profesional TI dijalankan lewat aplikasinya.", ""]
        return "\n".join(L)

    L += [f"{resp['n']} responden, {resp['n_pakar']} di antaranya profesional yang mengisi profesi aktual.", ""]
    L += ["### B.1 Hit Rate terhadap profesi aktual (uji pakar)", ""]
    if resp.get("pakar_uji"):
        uji = resp["pakar_uji"]
        L += [*tabel_pakar(uji), "",
              "Selang kepercayaan 95% dari 2000 sampel ulang bootstrap. Target proposal: Hit Rate@5 ≥ 60% "
              "dengan 15–20 profesional.", "",
              f"`{NAMA_LOKAL}`: profil RIASEC tiap profesi disusutkan ke rata-rata minat responden "
              "profesional Indonesia di profesi itu, tanpa menyertakan responden yang sedang diuji. "
              "Kalau baris ini lebih baik daripada hibrida bawaan, profil O*NET kurang mewakili kondisi lokal; "
              "jalankan `scripts/kalibrasi_riasec.py`. Lihat `docs/relevansi-riasec.md`.", "",
              "#### Uji berpasangan terhadap hibrida bawaan", "", *tabel_uji(uji), "",
              "McNemar (eksak) membandingkan apakah profesi aktual masuk 5 teratas pada kasus yang sama; "
              "Wilcoxon membandingkan reciprocal rank per kasus. p < 0,05 berarti perbedaannya kecil "
              "kemungkinan terjadi karena kebetulan." +
              (" **Responden profesional kurang dari 10, jadi p-value di atas hanya indikatif.**"
               if uji["n"] < 10 else ""), ""]
        if resp.get("pakar_cocok"):
            L += ["#### Khusus profesional yang menilai profesinya cocok (≥ 4 dari 5)", "",
                  f"{resp['pakar_cocok']['n']} responden.", "", *tabel_pakar(resp["pakar_cocok"]), ""]
    else:
        L += ["Belum ada responden profesional.", ""]

    L += ["### B.2 Precision@K dari penilaian relevansi", "",
          "| K | Precision@K | n responden |", "|---:|---:|---:|"]
    for k, v in resp["presisi"].items():
        L.append(f"| {k} | {pct(v[0])} | {v[1]} |" if v else f"| {k} | – | 0 |")
    L += [""]

    L += ["### B.3 Usability (SUS)", ""]
    if resp["sus"]:
        rata, n = resp["sus"]
        lo, hi = resp["sus_ci"]
        L += [f"Rata-rata **{d(rata, 1)}** dari {n} responden (95% CI {d(lo, 1)}–{d(hi, 1)}; "
              "ambang proposal: ≥ 68).", ""]
    else:
        L += ["Belum ada jawaban SUS.", ""]

    L += ["### B.3b Evaluasi penjelasan rekomendasi", ""]
    pj = resp.get("penjelasan")
    if pj:
        L += [f"{pj['n']} responden. Rata-rata keseluruhan **{d(pj['rata'])}** dari 5 "
              f"(95% CI {d(pj['ci'][0])}–{d(pj['ci'][1])}); {pct(pj['setuju'])} responden rata-ratanya ≥ 4.",
              "", "| Butir | Rata-rata |", "|---|---:|",
              *[f"| {t} | {d(v)} |" for t, v in pj["butir"]], ""]
    else:
        L += ["Belum ada jawaban.", ""]

    L += ["### B.4 Reliabilitas kuesioner", "", "| Skala | Koefisien |", "|---|---:|"]
    for nama, a in resp["reliabilitas"].items():
        L.append(f"| {nama} | {'–' if a is None else f'{a:.2f}'.replace('.', ',')} |")
    L += ["", "RIASEC memakai Cronbach's α (tiga butir per tipe). Big Five memakai koefisien Spearman-Brown "
              "karena BFI-10 hanya dua butir per dimensi. Koefisien baru dihitung setelah ada minimal "
              f"{MIN_RELIABILITAS} responden.", ""]
    L += ["### B.4b Relevansi menurut label skor", "",
          "Porsi rekomendasi yang dinilai relevan oleh responden pada tiap label. Label yang baik menunjukkan "
          "porsi relevan yang menurun dari Sangat Cocok ke Kurang Cocok.", "",
          "| Label | Porsi relevan | n penilaian |", "|---|---:|---:|"]
    for nama, v in resp["relevansi_label"].items():
        L.append(f"| {nama} | {pct(v[0])} | {v[1]} |" if v else f"| {nama} | – | 0 |")
    L += [""]

    L += ["### B.5 Skill di luar pilihan", "",
          f"Rata-rata {resp['n_skill']:.1f} skill dipilih per responden. Skill yang diketik sendiri "
          "karena tidak ada di pilihan (bahan perluasan basis pengetahuan):", ""]
    if resp["skill_lain"]:
        L += ["| Skill | Disebut |", "|---|---:|", *[f"| {s} | {n} |" for s, n in resp["skill_lain"]], ""]
    else:
        L += ["Belum ada.", ""]
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--persona", type=int, default=40, help="persona per profesi")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--sigma", type=float, default=0.12, help="simpangan baku derau profil")
    ap.add_argument("--lowongan", default=str(BERKAS_LOWONGAN),
                    help="berkas lowongan LinkedIn mentah (di luar repositori)")
    a = ap.parse_args()

    kb = muat_kb()
    sim = simulasi(kb, a.persona, a.seed, a.sigma)
    low = uji_lowongan(kb, Path(a.lowongan).expanduser())
    teks = laporan(sim, data_responden(kb), a, kb, low)
    KELUARAN.write_text(teks + "\n", encoding="utf-8")
    # Angka yang sama dalam bentuk mesin, dibaca penyusun buku supaya naskah
    # tidak pernah berbeda dengan laporan ini.
    KELUARAN_JSON.write_text(json.dumps({"simulasi": sim, "lowongan": low,
                                         "argumen": {**vars(a), "lowongan": Path(a.lowongan).name}},
                                        ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(teks)
    print(f"\n-> {KELUARAN.relative_to(AKAR)}")


if __name__ == "__main__":
    main()
