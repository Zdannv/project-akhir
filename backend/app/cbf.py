"""Tahap 2b — Content-Based Filtering pada skill.

Pengguna dan profesi diletakkan di ruang vektor yang sama, satu dimensi per
skill:

  * vektor profesi  : bobot kepentingan skill di profesi itu (skill_weight_pct);
  * vektor pengguna : tingkat penguasaan, 1/3 (dasar), 2/3 (menengah), 1 (mahir).

Skor CBF adalah cosine similarity keduanya. Karena cosine tidak peka terhadap
panjang vektor, bobot profesi tidak perlu berjumlah 100.

Selain skor, modul ini menghasilkan analisis kesenjangan skill (skill gap):
skill profesi yang belum dimiliki, diurutkan dari yang wajib dan paling berat.
"""

from __future__ import annotations

import math

TINGKAT_MAKS = 3
LABEL_TINGKAT = {1: "Dasar", 2: "Menengah", 3: "Mahir"}


def skor_cbf(skill_pengguna: dict[str, int], skill_profesi: list[dict]) -> dict:
    u = {sid: t / TINGKAT_MAKS for sid, t in skill_pengguna.items() if t > 0}
    w = {s["skill_id"]: s["bobot"] for s in skill_profesi}

    norma_u = math.sqrt(sum(v * v for v in u.values()))
    norma_w = math.sqrt(sum(v * v for v in w.values()))
    titik = sum(u[s] * w[s] for s in u.keys() & w.keys())
    kosinus = titik / (norma_u * norma_w) if norma_u and norma_w else 0.0

    # Cakupan: porsi bobot skill profesi yang sudah dikuasai. Bukan bagian dari
    # skor; dipakai untuk menjelaskan hasil ke pengguna.
    cakupan = titik / sum(w.values()) if w else 0.0
    return {"skor": round(kosinus, 4), "cakupan": round(cakupan, 4)}


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
