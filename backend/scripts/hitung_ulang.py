"""Menghitung ulang rekomendasi tersimpan dengan konfigurasi dan basis pengetahuan terkini.

Jawaban mentah tiap responden disimpan, jadi rekomendasinya bisa dihitung ulang
kapan saja. Jalankan setelah mengubah rumus, bobot, atau daftar skill:

    python scripts/hitung_ulang.py

PERHATIAN: penilaian relevansi (Precision@K) diberikan responden terhadap
rekomendasi yang mereka LIHAT. Setelah dihitung ulang, lima teratasnya bisa
berubah dan penilaian lama tidak lagi lengkap untuk daftar baru. Karena itu
skrip ini dimaksudkan untuk masa pengembangan; setelah pengumpulan data
dimulai, jangan dijalankan tanpa mencadangkan data/pa.db lebih dulu.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import penyimpanan as db  # noqa: E402
from app.evaluasi import profil_dari_masukan  # noqa: E402
from app.hibrida import Konfigurasi, rekomendasi  # noqa: E402
from app.kb import muat_kb  # noqa: E402


def main() -> None:
    kb = muat_kb()
    db.siapkan()
    id_skill = {s["id"] for s in kb.skill}
    n = 0
    for r in db.semua_responden():
        m = r["masukan"]
        m["skill"] = {s: t for s, t in m["skill"].items() if s in id_skill}
        profil = profil_dari_masukan(m, kb)
        hasil = rekomendasi(profil, kb, Konfigurasi())
        hasil["profil"] = {"riasec": profil.riasec}
        db.perbarui_hasil(r["id"], hasil)
        teratas = hasil["rekomendasi"][0] if hasil["rekomendasi"] else None
        print(f"{r['nama'][:30]:30} -> {teratas['nama'] if teratas else '-'}"
              f" ({round(teratas['skor'] * 100) if teratas else 0}%)")
        n += 1
    print(f"{n} isian dihitung ulang")


if __name__ == "__main__":
    main()
