"""Mengalibrasi alpha dan bobot KBF dari data responden profesional.

Bobot bawaan dipilih dengan pertimbangan, bukan dari data. Begitu ada responden
profesional (mereka mengisi profesi aktualnya), bobot bisa dicari yang paling
sering menaruh profesi aktual itu di peringkat atas.

Caranya: pencarian acak. Tiap kandidat adalah satu nilai alpha dan satu set
bobot komponen KBF (diambil acak, dinormalkan berjumlah 1). Kandidat dinilai
dengan MRR. Supaya tidak sekadar menghafal data, angka yang dilaporkan adalah
hasil leave-one-out: untuk tiap responden, bobot dipilih dari responden LAIN
lalu diuji pada responden itu.

    python scripts/kalibrasi.py [--kandidat 400] [--seed 7]

Dengan kurang dari 15 profesional, hasilnya terlalu goyah untuk dipakai;
skrip tetap berjalan tetapi memberi peringatan.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import kbf  # noqa: E402
from app import penyimpanan as db  # noqa: E402
from app.cbf import skor_cbf  # noqa: E402
from app.evaluasi import profil_dari_masukan  # noqa: E402
from app.kb import muat_kb  # noqa: E402

KOMPONEN = ("riasec", "bidang", "kesiapan", "finansial")


def siapkan(kb, responden):
    """Nilai tiap komponen untuk tiap (responden, profesi yang lolos); dihitung sekali."""
    data = []
    for r in responden:
        p = profil_dari_masukan(r["masukan"], kb)
        lolos, _ = kbf.saring(p, kb)
        baris = []
        for pr in lolos:
            k = kbf.skor_kbf(p, pr)["komponen"]
            baris.append((pr["id"], {x: k.get(x) for x in KOMPONEN}, skor_cbf(p.skill, kb.skill_profesi(pr["id"]))["skor"]))
        data.append((r["profesi_aktual"], baris))
    return data


def rr(kasus, alpha, bobot):
    """Reciprocal rank profesi aktual untuk satu responden."""
    target, baris = kasus
    skor = []
    for pid, k, cbf in baris:
        aktif = {x: b for x, b in bobot.items() if k[x] is not None}
        total = sum(aktif.values()) or 1.0
        kb_ = sum(b / total * k[x] for x, b in aktif.items())
        skor.append((alpha * kb_ + (1 - alpha) * cbf, pid))
    skor.sort(reverse=True)
    return next((1 / (i + 1) for i, (_, pid) in enumerate(skor) if pid == target), 0.0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kandidat", type=int, default=400)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    kb = muat_kb()
    db.siapkan()
    pakar = [r for r in db.responden_terakhir() if r["profesi_aktual"]]
    if len(pakar) < 3:
        print(f"Baru ada {len(pakar)} responden profesional. Kalibrasi butuh minimal 3, idealnya 15 atau lebih.")
        return
    if len(pakar) < 15:
        print(f"PERINGATAN: hanya {len(pakar)} responden profesional; hasil di bawah belum layak dipakai.\n")

    data = siapkan(kb, pakar)
    acak = random.Random(a.seed)
    bawaan = (0.5, dict(kbf.SKEMA_BOBOT["lengkap"][1]))
    kandidat = [bawaan]
    for _ in range(a.kandidat):
        mentah = [acak.random() for _ in KOMPONEN]
        kandidat.append((round(acak.random(), 2), {k: v / sum(mentah) for k, v in zip(KOMPONEN, mentah)}))

    # Nilai tiap kandidat pada tiap responden, dihitung sekali.
    nilai = [[rr(k, alpha, bobot) for k in data] for alpha, bobot in kandidat]
    n = len(data)

    def terbaik(kecuali: int | None) -> int:
        return max(range(len(kandidat)),
                   key=lambda i: sum(v for j, v in enumerate(nilai[i]) if j != kecuali))

    loo = sum(nilai[terbaik(j)][j] for j in range(n)) / n
    i = terbaik(None)
    alpha, bobot = kandidat[i]

    print(f"{n} responden profesional, {len(kandidat)} kandidat\n")
    print(f"MRR bobot bawaan            : {sum(nilai[0]) / n:.3f}")
    print(f"MRR bobot terbaik (di data) : {sum(nilai[i]) / n:.3f}   <- optimistis, bobotnya dipilih dari data yang sama")
    print(f"MRR leave-one-out           : {loo:.3f}   <- perkiraan jujur untuk responden baru\n")
    print(f"alpha = {alpha}")
    for k in KOMPONEN:
        print(f"  {k:10} {bobot[k]:.2f}")
    if loo <= sum(nilai[0]) / n:
        print("\nLeave-one-out tidak mengungguli bobot bawaan: belum ada alasan mengganti bobot.")


if __name__ == "__main__":
    main()
