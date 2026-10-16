"""Menguji, dan bila terbukti lebih baik, menerapkan profil RIASEC profesi versi lokal.

Profil minat tiap profesi berasal dari O*NET (Amerika Serikat). Skrip ini
memakai jawaban responden profesional TI Indonesia untuk menjawab apakah
profil itu masih mewakili kondisi lokal:

  1. Untuk tiap profesi, profil O*NET disusutkan ke rata-rata minat responden
     profesional di profesi itu:  w = n / (n + k),  profil = (1 - w) O*NET + w lokal.
  2. Diuji dengan leave-one-out: responden yang sedang diuji tidak ikut
     membentuk profil lokalnya, jadi tidak ada kebocoran jawaban.
  3. Dibandingkan dengan profil O*NET murni (Hit@5, MRR, McNemar, Wilcoxon).

Jalankan:
  python scripts/kalibrasi_riasec.py              # laporan saja
  python scripts/kalibrasi_riasec.py --tulis      # + simpan data/kb/riasec_lokal.json
                                                  #   kalau kalibrasi tidak lebih buruk
Keluaran: docs/hasil-kalibrasi-riasec.md
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import penyimpanan as db  # noqa: E402
from app import statistik as st  # noqa: E402
from app.evaluasi import _riasec_lokal_loo, metrik, posisi_profesi, profil_dari_masukan  # noqa: E402
from app.hibrida import Konfigurasi  # noqa: E402
from app.kb import AKAR, BERKAS_KB, BERKAS_RIASEC_LOKAL, RIASEC, BasisPengetahuan, campur_riasec  # noqa: E402
from app.kuesioner import kode_holland  # noqa: E402

KELUARAN = AKAR / "docs" / "hasil-kalibrasi-riasec.md"


def korelasi(a: dict, b: dict) -> float | None:
    x, y = [a[t] for t in RIASEC], [b[t] for t in RIASEC]
    mx, my = sum(x) / 6, sum(y) / 6
    sx = math.sqrt(sum((v - mx) ** 2 for v in x))
    sy = math.sqrt(sum((v - my) ** 2 for v in y))
    if sx == 0 or sy == 0:
        return None
    return sum((p - mx) * (q - my) for p, q in zip(x, y)) / (sx * sy)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--k", type=float, default=5.0, help="kekuatan profil O*NET, setara k responden")
    ap.add_argument("--tulis", action="store_true", help="simpan profil lokal kalau tidak lebih buruk")
    ap.add_argument("--paksa", action="store_true", help="simpan walaupun lebih buruk (tidak disarankan)")
    a = ap.parse_args()

    # Selalu mulai dari profil O*NET murni, bukan dari profil lokal yang mungkin sudah tersimpan.
    kb = BasisPengetahuan(json.loads(BERKAS_KB.read_text(encoding="utf-8")))
    pakar = [r for r in (db.responden_terakhir() if db.tersedia() else []) if r["profesi_aktual"]]
    L = ["# Kalibrasi Profil RIASEC Lokal", "",
         f"Dibuat otomatis oleh `backend/scripts/kalibrasi_riasec.py` pada {date.today():%d-%m-%Y}.", ""]
    if len(pakar) < 2:
        L += [f"Responden profesional baru {len(pakar)} orang; leave-one-out butuh minimal 2. "
              "Jalankan ulang setelah data terkumpul.", ""]
        KELUARAN.write_text("\n".join(L), encoding="utf-8")
        print("\n".join(L))
        return

    kasus = [(profil_dari_masukan(r["masukan"], kb), r["profesi_aktual"]) for r in pakar]
    onet = [posisi_profesi(p, t, kb, Konfigurasi()) for p, t in kasus]
    hasil_k = {}
    for k in sorted({2.0, 5.0, 10.0, a.k}):
        lokal = [posisi_profesi(p, t, _riasec_lokal_loo(kasus, kb, i, k), Konfigurasi()) for i, (p, t) in enumerate(kasus)]
        hasil_k[k] = lokal
    hit = lambda pos: [bool(r and r <= 5) for r in pos]  # noqa: E731
    rr = lambda pos: [1 / r if r else 0.0 for r in pos]  # noqa: E731
    m0 = metrik(onet)
    L += [f"{len(kasus)} responden profesional, {len({t for _, t in kasus})} profesi berbeda.", "",
          "## Leave-one-out", "",
          "| Profil RIASEC profesi | Hit@1 | Hit@5 | MRR | p McNemar (Hit@5) | p Wilcoxon (RR) |",
          "|---|---:|---:|---:|---:|---:|",
          f"| O*NET murni | {m0['hit@1']:.1%} | {m0['hit@5']:.1%} | {m0['mrr']:.3f} | – | – |"]
    for k, pos in hasil_k.items():
        m = metrik(pos)
        L.append(f"| Disusutkan ke data lokal, k = {k:g} | {m['hit@1']:.1%} | {m['hit@5']:.1%} | {m['mrr']:.3f} | "
                 f"{st.mcnemar(hit(onet), hit(pos))['p']:.3f} | {st.wilcoxon(rr(onet), rr(pos))['p']:.3f} |")
    L += ["", "k = kekuatan profil O*NET, setara k responden. Makin kecil k, makin besar pengaruh data lokal.", ""]

    per_profesi: dict[str, list[dict]] = {}
    for p, t in kasus:
        per_profesi.setdefault(t, []).append(p.riasec)
    L += ["## Profil O*NET vs rata-rata responden lokal", "",
          "| Profesi | n | Kode O*NET | Kode lokal | Korelasi profil |", "|---|---:|---|---|---:|"]
    for pid, daftar in sorted(per_profesi.items(), key=lambda x: -len(x[1])):
        p = kb.cari_profesi(pid)
        rata = {t: sum(x[t] for x in daftar) / len(daftar) for t in RIASEC}
        r = korelasi(p["riasec"], rata)
        L.append(f"| {p['nama']} | {len(daftar)} | {p['kode_holland']} | {kode_holland(rata)} | "
                 f"{'–' if r is None else f'{r:.2f}'} |")
    L += ["", "Korelasi profil mendekati 1 berarti pola minat profesional Indonesia di profesi itu "
          "sejalan dengan profil O*NET; mendekati 0 atau negatif berarti berbeda.", ""]

    ml = metrik(hasil_k[a.k])
    tidak_lebih_buruk = ml["hit@5"] >= m0["hit@5"] and ml["mrr"] >= m0["mrr"]
    if a.tulis and (tidak_lebih_buruk or a.paksa):
        profil = {pid: campur_riasec(kb.cari_profesi(pid)["riasec"], daftar, a.k) for pid, daftar in per_profesi.items()}
        BERKAS_RIASEC_LOKAL.write_text(json.dumps({
            "dibuat": date.today().isoformat(), "k": a.k, "n_responden": len(kasus),
            "n_per_profesi": {pid: len(d) for pid, d in per_profesi.items()}, "profil": profil,
        }, indent=2, ensure_ascii=False), encoding="utf-8")
        L += [f"**Disimpan** ke `{BERKAS_RIASEC_LOKAL.relative_to(AKAR)}`; mesin memakainya setelah server dijalankan ulang. "
              "Jalankan juga `scripts/hitung_ulang.py` supaya hasil responden lama ikut diperbarui.", ""]
    elif a.tulis:
        L += ["**Tidak disimpan**: profil lokal tidak lebih baik daripada O*NET pada leave-one-out.", ""]
    KELUARAN.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
