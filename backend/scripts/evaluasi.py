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

Jalankan:  python scripts/evaluasi.py [--persona 40] [--seed 42]
Keluaran:  docs/hasil-evaluasi.md
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluasi import KONFIG_ABLASI, data_responden, metrik, posisi_profesi  # noqa: E402
from app.hibrida import Konfigurasi  # noqa: E402
from app.kb import AKAR, BIG5, RIASEC, BasisPengetahuan, muat_kb  # noqa: E402
from app.kbf import ProfilPengguna  # noqa: E402

KELUARAN = AKAR / "docs" / "hasil-evaluasi.md"


def jepit(x: float) -> float:
    return max(0.0, min(1.0, x))


# ── A. Simulasi ─────────────────────────────────────────────────────────────
def persona(p: dict, kb: BasisPengetahuan, acak: random.Random,
            sigma: float, semua_skill: list[str], n_derau: int = 2) -> ProfilPengguna:
    """Satu orang rekaan yang 'cocok' dengan profesi p, dengan derau.

    Minat dan kepribadian: profil profesi + derau Gauss. Skill: sebagian skill
    wajib (peluang 0,75) dan pilihan (0,35) profesi itu, ditambah dua skill
    acak yang tidak berhubungan — orang sungguhan tidak pernah punya persis
    daftar skill sebuah lowongan.
    """
    riasec = {t: jepit((p["riasec"][t] - 1) / 6 + acak.gauss(0, sigma)) for t in RIASEC}
    big5 = {d: jepit(p["big5_ideal"][d] + acak.gauss(0, sigma)) for d in BIG5}
    skill = {}
    for s in kb.skill_profesi(p["id"]):
        if acak.random() < (0.75 if s["wajib"] else 0.35):
            skill[s["skill_id"]] = acak.choice((1, 2, 2, 3))
    for sid in acak.sample(semua_skill, n_derau):
        skill.setdefault(sid, acak.choice((1, 2)))
    return ProfilPengguna(
        riasec=riasec, big5=big5,
        rank_pendidikan=max(p["pendidikan_min_rank"], 4),
        domisili="Jakarta", bersedia_relokasi=True,
        ekspektasi_gaji=p["gaji_min"], punya_tanggungan=acak.random() < 0.3,
        skill=skill,
    )


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

    return {
        "ruang": ruang,
        "n": len(kasus),
        "ablasi": {nama: jalankan(k) for nama, k in KONFIG_ABLASI.items()},
        "alpha": {a / 10: jalankan(Konfigurasi(alpha=a / 10)) for a in range(11)},
        "alpha_iachan": {a / 10: jalankan(Konfigurasi(alpha=a / 10, metode_riasec="iachan")) for a in range(11)},
        "riasec": {m: jalankan(Konfigurasi(metode_riasec=m)) for m in ("iachan", "korelasi")},
        "riasec_kbf": {m: jalankan(Konfigurasi(alpha=1.0, metode_riasec=m)) for m in ("iachan", "korelasi")},
    }


# ── Laporan ─────────────────────────────────────────────────────────────────
def pct(x: float) -> str:
    return f"{x * 100:.1f}%".replace(".", ",")


def tabel_metrik(baris: dict) -> list[str]:
    out = ["| Konfigurasi | Hit@1 | Hit@3 | Hit@5 | MRR |", "|---|---:|---:|---:|---:|"]
    for nama, m in baris.items():
        out.append(f"| {nama} | {pct(m['hit@1'])} | {pct(m['hit@3'])} | {pct(m['hit@5'])} | "
                   f"{m['mrr']:.3f} |".replace(".", ","))
    return out


def laporan(sim: dict, resp: dict | None, argumen: argparse.Namespace, kb: BasisPengetahuan) -> str:
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
        *tabel_metrik(sim["ablasi"]),
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
        "## B. Data responden",
        "",
    ]
    if resp is None:
        L += ["Belum ada responden di basis data. Bagian ini terisi setelah pengujian dengan "
              "mahasiswa dan profesional TI dijalankan lewat aplikasinya.", ""]
        return "\n".join(L)

    L += [f"{resp['n']} responden, {resp['n_pakar']} di antaranya profesional yang mengisi profesi aktual.", ""]
    L += ["### B.1 Hit Rate terhadap profesi aktual (uji pakar)", ""]
    if resp.get("pakar"):
        L += [*tabel_metrik(resp["pakar"]), "",
              "Target proposal: Hit Rate@5 ≥ 60% dengan 15–20 profesional.", ""]
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
        L += [f"Rata-rata **{rata:.1f}** dari {n} responden (ambang proposal: ≥ 68).".replace(".", ",", 1), ""]
    else:
        L += ["Belum ada jawaban SUS.", ""]

    L += ["### B.4 Reliabilitas kuesioner (Cronbach's α)", "", "| Skala | α |", "|---|---:|"]
    for nama, a in resp["reliabilitas"].items():
        L.append(f"| {nama} | {'–' if a is None else f'{a:.2f}'.replace('.', ',')} |")
    L += ["", "Skala Big Five hanya dua butir per dimensi (BFI-10), sehingga α yang rendah di sana "
              "lazim dan bukan tanda instrumen rusak.", ""]

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
    a = ap.parse_args()

    kb = muat_kb()
    teks = laporan(simulasi(kb, a.persona, a.seed, a.sigma), data_responden(kb), a, kb)
    KELUARAN.write_text(teks + "\n", encoding="utf-8")
    print(teks)
    print(f"\n-> {KELUARAN.relative_to(AKAR)}")


if __name__ == "__main__":
    main()
