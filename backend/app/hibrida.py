"""Tahap 2c — penggabungan (weighted hybrid) dan penyusunan Top-N.

    Skor_Final = alpha * Skor_KBF + (1 - alpha) * Skor_CBF        alpha = 0,5

Konfigurasi bawaan (alpha 0,5 dan kongruensi minat berbasis korelasi) berbeda
dari buku proposal (alpha 0,6 dan indeks Iachan). Alasannya ada di
docs/keputusan-desain.md; konfigurasi proposal tetap tersedia sebagai
`KONFIG_PROPOSAL` dan selalu dilaporkan berdampingan di evaluasi.

Fungsi `rekomendasi` adalah satu-satunya pintu masuk mesin: API dan skrip
evaluasi memanggil fungsi yang sama, sehingga angka di laporan pengujian
berasal dari kode yang juga dijalankan pengguna.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .cbf import kesenjangan_skill, skor_cbf
from .kb import BasisPengetahuan
from .kbf import ProfilPengguna, catatan_lokasi, saring, skor_kbf
from .kuesioner import kode_holland


@dataclass(frozen=True)
class Konfigurasi:
    alpha: float = 0.5              # porsi KBF; 1 = KBF saja, 0 = CBF saja
    metode_riasec: str = "korelasi"  # "korelasi" | "iachan"
    ruang_cbf: str = "global"       # "global" | "profesi"; lihat cbf.py
    skema_bobot: str = "lengkap"    # "lengkap" | "proposal"; lihat kbf.py
    ukuran_cbf: str = "gabungan"    # "gabungan" | "kosinus"; lihat cbf.py
    saring_relokasi: bool = False   # penyaring mutlak relokasi; lihat kbf.alasan_tersaring
    top_n: int = 5

    def __post_init__(self) -> None:
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError("alpha harus di antara 0 dan 1")
        if self.top_n < 1:
            raise ValueError("top_n minimal 1")


# Persis seperti di buku proposal; dipakai sebagai pembanding.
KONFIG_PROPOSAL = Konfigurasi(alpha=0.6, metode_riasec="iachan", skema_bobot="proposal",
                              ukuran_cbf="kosinus", saring_relokasi=True)


def peringkat(profil: ProfilPengguna, kb: BasisPengetahuan,
              konfig: Konfigurasi = Konfigurasi()) -> tuple[list[dict], list[dict]]:
    """Semua profesi yang lolos, terurut; ditambah daftar yang tersaring."""
    lolos, tersaring = saring(profil, kb, konfig.saring_relokasi)
    baris = []
    for p in lolos:
        kbf = skor_kbf(profil, p, konfig.metode_riasec, konfig.skema_bobot)
        cbf = skor_cbf(profil.skill, kb.skill_profesi(p["id"]), konfig.ruang_cbf, konfig.ukuran_cbf)
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
            "pengalaman_min_tahun": p["pengalaman_min_tahun"],
            "kesenjangan": kesenjangan_skill(profil.skill, kb.skill_profesi(p["id"]), nama),
            "alasan": susun_alasan(profil, p, b, {x["kode"]: x["nama"] for x in kb.bidang}),
        })
    return {
        "konfigurasi": asdict(konfig),
        "kode_holland": kode_holland(profil.riasec),
        "n_lolos": len(semua),
        "n_tersaring": len(tersaring),
        "rekomendasi": teratas,
        "peringkat_lengkap": [
            {k: b[k] for k in ("peringkat", "profesi_id", "nama", "sektor", "skor")} | {
                "skor_kbf": b["kbf"]["skor"], "skor_cbf": b["cbf"]["skor"],
                **_ringkas(kb.cari_profesi(b["profesi_id"]))}
            for b in semua
        ],
        "tersaring": tersaring,
    }


def _ringkas(p: dict) -> dict:
    """Data kartu profesi di daftar."""
    return {k: p[k] for k in ("gaji_min", "gaji_maks", "pola_kerja", "kode_holland", "deskripsi",
                              "senioritas", "pengalaman_min_tahun")}


def susun_alasan(profil: ProfilPengguna, profesi: dict, baris: dict,
                 nama_bidang: dict[str, str] | None = None) -> list[dict]:
    """Penjelasan singkat mengapa profesi ini muncul, dari komponen skornya.

    Tiap alasan bernada "cocok" atau "perhatian", supaya antarmuka bisa
    membedakan kekuatan dari hal yang perlu diperhatikan.
    """
    k = baris["kbf"]["komponen"]
    kode = kode_holland(profil.riasec)
    nama_bidang = nama_bidang or {}
    alasan: list[dict] = []

    def tambah(nada: str, teks: str) -> None:
        alasan.append({"nada": nada, "teks": teks})

    sama = [h for h in kode if h in profesi["kode_holland"]]
    # Ambang 0,7: korelasi +0,4 ke atas, atau indeks Iachan dengan huruf pertama sama.
    if k["riasec"] >= 0.7:
        tambah("cocok", f"Minatmu ({kode}) sejalan dengan tipe minat profesi ini ({profesi['kode_holland']}).")
    elif sama:
        tambah("cocok", f"Sebagian minatmu ({', '.join(sama)}) cocok dengan tipe minat profesi ini ({profesi['kode_holland']}).")
    else:
        tambah("perhatian", f"Tipe minat profesi ini ({profesi['kode_holland']}) berbeda dari minatmu ({kode}).")

    if "bidang" in k:
        utama = max(profesi["bidang"], key=profesi["bidang"].get)
        if k["bidang"] >= 0.75:
            tambah("cocok", f"Kamu tertarik pada bidang kerja profesi ini ({nama_bidang.get(utama, utama)}).")
        elif k["bidang"] <= 0.4:
            tambah("perhatian", f"Minatmu pada bidang kerja profesi ini ({nama_bidang.get(utama, utama)}) rendah.")

    if k["big5"] >= 0.75:
        tambah("cocok", "Kepribadianmu dekat dengan profil ideal profesi ini.")

    if k.get("kesiapan", 1) < 1:
        tambah("perhatian", f"Profesi ini umumnya meminta pengalaman minimal {profesi['pengalaman_min_tahun']} tahun. "
                            "Anggap sebagai tujuan jangka menengah.")

    cakupan = baris["cbf"]["cakupan"]
    if cakupan >= 0.5:
        tambah("cocok", f"Kamu sudah menguasai sekitar {round(cakupan * 100)}% bobot skill yang diminta.")
    elif cakupan > 0:
        tambah("perhatian", f"Skill-mu baru menutup sekitar {round(cakupan * 100)}% bobot yang diminta.")
    else:
        tambah("perhatian", "Belum ada skill-mu yang beririsan dengan profesi ini.")

    if profil.ekspektasi_gaji > 0:
        if k["finansial"] >= 1:
            tambah("cocok", "Ekspektasi gajimu terpenuhi oleh rentang gaji profesi ini.")
        elif k["finansial"] <= 0:
            tambah("perhatian", "Ekspektasi gajimu melebihi rentang gaji profesi ini.")
    lokasi = catatan_lokasi(profil, profesi)
    if lokasi:
        tambah("cocok" if profil.bersedia_relokasi else "perhatian", lokasi)
    if profil.punya_tanggungan and profesi["stabilitas"] >= 0.85:
        tambah("cocok", "Pola kerjanya relatif stabil, sesuai dengan tanggungan keluargamu.")
    return alasan
