"""Tahap 2c — penggabungan (weighted hybrid) dan penyusunan Top-N.

    Skor_Final = alpha * Skor_KBF + (1 - alpha) * Skor_CBF        alpha = 0,6

Fungsi `rekomendasi` adalah satu-satunya pintu masuk mesin: API dan skrip
evaluasi memanggil fungsi yang sama, sehingga angka di laporan pengujian
berasal dari kode yang juga dijalankan pengguna.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .cbf import kesenjangan_skill, skor_cbf
from .kb import BasisPengetahuan
from .kbf import ProfilPengguna, saring, skor_kbf
from .kuesioner import kode_holland


@dataclass(frozen=True)
class Konfigurasi:
    alpha: float = 0.6              # porsi KBF; 1 = KBF saja, 0 = CBF saja
    metode_riasec: str = "iachan"   # "iachan" | "korelasi"
    top_n: int = 5

    def __post_init__(self) -> None:
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError("alpha harus di antara 0 dan 1")
        if self.top_n < 1:
            raise ValueError("top_n minimal 1")


def peringkat(profil: ProfilPengguna, kb: BasisPengetahuan,
              konfig: Konfigurasi = Konfigurasi()) -> tuple[list[dict], list[dict]]:
    """Semua profesi yang lolos, terurut; ditambah daftar yang tersaring."""
    lolos, tersaring = saring(profil, kb)
    baris = []
    for p in lolos:
        kbf = skor_kbf(profil, p, konfig.metode_riasec)
        cbf = skor_cbf(profil.skill, kb.skill_profesi(p["id"]))
        final = konfig.alpha * kbf["skor"] + (1 - konfig.alpha) * cbf["skor"]
        baris.append({
            "profesi_id": p["id"],
            "nama": p["nama"],
            "sektor": p["sektor"],
            "skor": round(final, 4),
            "kbf": kbf,
            "cbf": cbf,
        })
    # Seri diputus dengan skor KBF, lalu id, supaya urutannya deterministik.
    baris.sort(key=lambda b: (-b["skor"], -b["kbf"]["skor"], b["profesi_id"]))
    for i, b in enumerate(baris, start=1):
        b["peringkat"] = i
    return baris, tersaring


def rekomendasi(profil: ProfilPengguna, kb: BasisPengetahuan,
                konfig: Konfigurasi = Konfigurasi()) -> dict:
    semua, tersaring = peringkat(profil, kb, konfig)
    nama = kb.nama_skill()
    teratas = []
    for b in semua[: konfig.top_n]:
        p = kb.cari_profesi(b["profesi_id"])
        teratas.append({
            **b,
            "kode_holland": p["kode_holland"],
            "gaji_min": p["gaji_min"],
            "gaji_maks": p["gaji_maks"],
            "pola_kerja": p["pola_kerja"],
            "kesenjangan": kesenjangan_skill(profil.skill, kb.skill_profesi(p["id"]), nama),
            "alasan": susun_alasan(profil, p, b),
        })
    return {
        "konfigurasi": asdict(konfig),
        "kode_holland": kode_holland(profil.riasec),
        "n_lolos": len(semua),
        "n_tersaring": len(tersaring),
        "rekomendasi": teratas,
        "peringkat_lengkap": [
            {k: b[k] for k in ("peringkat", "profesi_id", "nama", "skor")} | {
                "skor_kbf": b["kbf"]["skor"], "skor_cbf": b["cbf"]["skor"]}
            for b in semua
        ],
        "tersaring": tersaring,
    }


def susun_alasan(profil: ProfilPengguna, profesi: dict, baris: dict) -> list[str]:
    """Penjelasan singkat mengapa profesi ini muncul, dari komponen skornya."""
    k = baris["kbf"]["komponen"]
    kode = kode_holland(profil.riasec)
    alasan = []

    sama = [h for h in kode if h in profesi["kode_holland"]]
    if k["riasec"] >= 0.6:
        alasan.append(f"Minatmu ({kode}) sejalan dengan tipe profesi ini ({profesi['kode_holland']}).")
    elif sama:
        alasan.append(f"Sebagian minatmu ({', '.join(sama)}) cocok dengan tipe profesi ini ({profesi['kode_holland']}).")
    else:
        alasan.append(f"Tipe minat profesi ini ({profesi['kode_holland']}) berbeda dari minatmu ({kode}).")

    if k["big5"] >= 0.75:
        alasan.append("Gaya kerjamu dekat dengan tuntutan kepribadian profesi ini.")

    cakupan = baris["cbf"]["cakupan"]
    if cakupan >= 0.5:
        alasan.append(f"Kamu sudah menguasai sekitar {round(cakupan * 100)}% bobot skill yang diminta.")
    elif cakupan > 0:
        alasan.append(f"Skill-mu baru menutup sekitar {round(cakupan * 100)}% bobot yang diminta — lihat kesenjangan skill.")
    else:
        alasan.append("Belum ada skill-mu yang beririsan dengan profesi ini.")

    if profil.ekspektasi_gaji > 0:
        if k["finansial"] >= 1:
            alasan.append("Ekspektasi gajimu masih di dalam rentang gaji awal profesi ini.")
        elif k["finansial"] <= 0:
            alasan.append("Ekspektasi gajimu melebihi rentang gaji profesi ini.")
    if profil.punya_tanggungan and profesi["stabilitas"] >= 0.85:
        alasan.append("Pola kerjanya relatif stabil, sesuai dengan tanggungan keluargamu.")
    return alasan
