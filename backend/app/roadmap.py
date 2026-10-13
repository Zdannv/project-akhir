"""Roadmap skill menuju profesi tujuan, dengan simulasi skor.

Setelah pengguna memilih satu profesi sebagai tujuan, skill profesi itu yang
belum dikuasai disusun menjadi tiga tahap berdasarkan data yang sama dengan
yang dipakai CBF:

    Pondasi     skill wajib
    Penguatan   skill pilihan dengan bobot di atas atau sama dengan median
    Pelengkap   skill pilihan sisanya

Pengguna bisa mencentang skill yang sudah (atau akan) dipelajari. Centang itu
TIDAK mengubah profil maupun rekomendasi yang tersimpan — data pengujian harus
tetap mencerminkan jawaban asli. Ia hanya dipakai untuk menghitung proyeksi:
"kalau skill ini sudah kukuasai, cakupan, skor, dan peringkatku jadi berapa?"

Ukuran kemajuannya adalah CAKUPAN (porsi bobot skill profesi yang dikuasai),
karena ia selalu naik saat skill bertambah. Skor cosine tidak dijamin begitu:
ia mengukur kemiripan arah, jadi skill berbobot kecil bisa sedikit
menurunkannya. Skor dan peringkat proyeksi tetap ditampilkan apa adanya.
"""

from __future__ import annotations

import statistics
from dataclasses import replace

from .hibrida import Konfigurasi, peringkat
from .kb import BasisPengetahuan
from .kbf import ProfilPengguna

# Skill yang dicentang di roadmap dianggap dikuasai pada tingkat menengah.
TINGKAT_PROYEKSI = 2

TAHAP = [
    ("pondasi", "Pondasi", "Skill wajib. Tanpa ini sulit melamar ke profesi ini."),
    ("penguatan", "Penguatan", "Skill pilihan yang paling sering diminta."),
    ("pelengkap", "Pelengkap", "Nilai tambah yang membedakanmu dari pelamar lain."),
]


def susun(profil: ProfilPengguna, profesi_id: str, dicentang: set[str],
          kb: BasisPengetahuan, konfig: Konfigurasi = Konfigurasi()) -> dict:
    nama = kb.nama_skill()
    belajar = kb.belajar_skill()
    relasi = kb.skill_profesi(profesi_id)
    belum = [r for r in relasi if profil.skill.get(r["skill_id"], 0) == 0]
    pilihan = [r["bobot"] for r in belum if not r["wajib"]]
    ambang = statistics.median(pilihan) if pilihan else 0.0

    kelompok: dict[str, list[dict]] = {kode: [] for kode, _, _ in TAHAP}
    for r in sorted(belum, key=lambda r: -r["bobot"]):
        kode = "pondasi" if r["wajib"] else "penguatan" if r["bobot"] >= ambang else "pelengkap"
        kelompok[kode].append({
            "skill_id": r["skill_id"], "nama": nama[r["skill_id"]], "wajib": r["wajib"],
            "bobot": r["bobot"], "dicentang": r["skill_id"] in dicentang,
            "belajar": belajar[r["skill_id"]],
        })

    # Hanya centang yang memang bagian dari roadmap profesi ini yang dihitung.
    sah = {r["skill_id"] for r in belum} & dicentang
    # Skill berbobot 0 tidak membawa informasi kecocokan, jadi tidak ikut ke
    # vektor proyeksi (tetap dihitung sebagai kemajuan).
    berbobot = {r["skill_id"] for r in belum if r["bobot"] > 0} & sah
    awal = _posisi(profil, profesi_id, kb, konfig)
    proyeksi = _posisi(
        replace(profil, skill=profil.skill | dict.fromkeys(berbobot, TINGKAT_PROYEKSI)),
        profesi_id, kb, konfig,
    ) if berbobot else awal

    return {
        "tahap": [{"kode": kode, "nama": n, "keterangan": ket, "skill": kelompok[kode]}
                  for kode, n, ket in TAHAP if kelompok[kode]],
        "dikuasai": [{"skill_id": r["skill_id"], "nama": nama[r["skill_id"]], "wajib": r["wajib"]}
                     for r in relasi if profil.skill.get(r["skill_id"], 0) > 0],
        "progres": {"selesai": len(sah), "total": len(belum)},
        "awal": awal,
        "proyeksi": proyeksi,
    }


def _posisi(profil: ProfilPengguna, profesi_id: str, kb: BasisPengetahuan, konfig: Konfigurasi) -> dict | None:
    semua, _ = peringkat(profil, kb, konfig)
    b = next((b for b in semua if b["profesi_id"] == profesi_id), None)
    if b is None:
        return None
    return {"skor": b["skor"], "skor_cbf": b["cbf"]["skor"], "cakupan": b["cbf"]["cakupan"],
            "peringkat": b["peringkat"]}
