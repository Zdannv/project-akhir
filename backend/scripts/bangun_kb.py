"""Membangun basis pengetahuan (knowledge base) dari berkas sumber.

Tiga sumber digabung menjadi satu berkas JSON yang dibaca mesin rekomendasi:

  data/sumber/knowledge_base_profesi_IT.xlsx
      35 profesi TI, 114 skill, 308 relasi profesi-skill berbobot, patokan gaji.
      Hasil pengolahan lowongan kerja lokal (LinkedIn Indonesia, 2025).

  data/sumber/pelengkap_skill.csv, pelengkap_profesi_skill.csv
      Workbook di atas berhenti di C027: sembilan profesi (C023, C028 - C035)
      belum punya relasi skill, dan skill khasnya belum ada di daftar. Dua
      berkas ini melengkapinya. Isinya KURASI PENULIS, bukan hasil pengolahan
      lowongan; setiap baris dari sini diberi sumber "kurasi" di keluaran
      supaya bisa dibedakan dan divalidasi belakangan.

  data/sumber/onet_riasec_profesi_ti.csv
      Profil minat Holland (RIASEC) tiap profesi, dari O*NET 30.3 lewat padanan
      kode SOC. Skala OI asli O*NET, 1,00 - 7,00.

  data/sumber/onet_workstyle_profesi_ti.csv
      Skor Work Styles O*NET per kode SOC (0 - 100), bahan profil ideal Big Five.

Inilah "dataset hibrida" di buku proposal: realitas pasar kerja lokal (syarat,
skill, gaji) digabung dengan taksonomi psikologi O*NET (RIASEC).

Jalankan:  python scripts/bangun_kb.py
Keluaran:  data/kb/basis_pengetahuan.json
"""

from __future__ import annotations

import csv
import json
import statistics
from datetime import date
from pathlib import Path

import openpyxl

AKAR = Path(__file__).resolve().parents[2]
SUMBER = AKAR / "data" / "sumber"
KELUARAN = AKAR / "data" / "kb" / "basis_pengetahuan.json"

# ─────────────────────────────────────────────────────────────────────────────
# Jenjang pendidikan
#
# Enam tingkat ordinal. D4 dan S1 setingkat, SMA dan SMK setingkat. Urutan
# inilah yang dipakai penyaring mutlak (hard filter) pendidikan di KBF.
# ─────────────────────────────────────────────────────────────────────────────
JENJANG = [
    {"kode": "SMA", "nama": "SMA / SMK sederajat", "rank": 1},
    {"kode": "D1", "nama": "Diploma 1 / 2", "rank": 2},
    {"kode": "D3", "nama": "Diploma 3", "rank": 3},
    {"kode": "S1", "nama": "Sarjana / Sarjana Terapan (S1 / D4)", "rank": 4},
    {"kode": "S2", "nama": "Magister (S2)", "rank": 5},
    {"kode": "S3", "nama": "Doktor (S3)", "rank": 6},
]

# Token yang muncul di kolom min_education -> rank. Syarat profesi ditulis
# sebagai rentang ("D3/D4/S1"); yang dipakai rank TERENDAH di dalamnya, karena
# itu batas bawah yang masih diterima.
RANK_TOKEN = {"SMA": 1, "SMK": 1, "D1": 2, "D2": 2, "D3": 3, "D4": 4, "S1": 4, "S2": 5, "S3": 6}


def rank_pendidikan_min(teks: str) -> int:
    token = [t.strip().upper() for t in teks.replace("-", "/").split("/")]
    rank = [RANK_TOKEN[t] for t in token if t in RANK_TOKEN]
    if not rank:
        raise ValueError(f"min_education tidak dikenali: {teks!r}")
    return min(rank)


def label_jenjang(rank: int) -> str:
    return next(j["nama"] for j in JENJANG if j["rank"] == rank)


# ─────────────────────────────────────────────────────────────────────────────
# Indeks stabilitas kerja (0 - 1)
#
# Buku proposal memakai "penalti stabilitas sosial" untuk pengguna yang punya
# tanggungan keluarga, tetapi sumber data tidak punya kolom stabilitas kontrak.
# Yang ada: pola kerja dan sektor. Indeks di bawah adalah PROKSI yang diturunkan
# terang-terangan dari dua kolom itu -- bukan hasil pengukuran. Ia perlu diganti
# dengan proporsi lowongan berstatus tetap vs kontrak begitu data itu tersedia.
# Asumsinya ditulis di docs/keputusan-desain.md supaya bisa dipertanggungjawabkan.
# ─────────────────────────────────────────────────────────────────────────────
STABILITAS_POLA = {"onsite": 1.00, "hybrid": 0.80, "remote": 0.55}
SEKTOR_BARU = {"Emerging Technology": 0.15, "Game Development": 0.10}


def pola_kerja(teks: str) -> list[str]:
    """ "Hybrid/Remote" -> ["hybrid", "remote"]; urutan dipertahankan."""
    return [t.strip().lower() for t in teks.split("/") if t.strip()]


def stabilitas(pola: list[str], sektor: str) -> float:
    # Pola yang disebut pertama adalah yang dominan, jadi diberi bobot lebih.
    bobot = [0.65, 0.35] if len(pola) > 1 else [1.0]
    dasar = sum(b * STABILITAS_POLA[p] for b, p in zip(bobot, pola))
    return round(max(0.0, min(1.0, dasar - SEKTOR_BARU.get(sektor, 0.0))), 3)


# ─────────────────────────────────────────────────────────────────────────────
# Profil ideal Big Five per profesi
#
# O*NET tidak mengukur Big Five. Yang ada adalah Work Styles, dan pemetaannya
# ke Big Five mengikuti pengelompokan yang lazim di literatur (Work Styles
# O*NET disusun di atas taksonomi kepribadian lima faktor):
#
#   Openness            Innovation, Tolerance for Ambiguity      -> WSY_DINAMIS
#   Conscientiousness   Dependability, Attention to Detail,
#                       Achievement, Perseverance                -> WSY_TERSTRUKTUR,
#                                                                   WSY_DETAIL, WSY_TARGET
#   Extraversion        Social Orientation, ditambah minat
#                       Enterprising dan Social (RIASEC)         -> WSY_KOLABORATIF + E/S
#   Agreeableness       Cooperation, Empathy, Sincerity          -> WSY_KOLABORATIF,
#                                                                   WSY_PELAYANAN
#   Neuroticism         kebalikan Stress Tolerance, Adaptability -> 1 - WSY_BERUBAH
#
# Extraversion paling lemah dasarnya: Work Styles yang tersedia tidak memuat
# Leadership, jadi ia ditopang minat Enterprising/Social. Ini keterbatasan yang
# dicatat, bukan disembunyikan.
# ─────────────────────────────────────────────────────────────────────────────
def big5_ideal(ws: dict[str, float], riasec: dict[str, float]) -> dict[str, float]:
    def s(kode: str) -> float:
        return ws[kode] / 100.0

    sosial = ((riasec["E"] + riasec["S"]) / 2 - 1) / 6  # skala 1-7 -> 0-1
    hasil = {
        "O": s("WSY_DINAMIS"),
        "C": (s("WSY_TERSTRUKTUR") + s("WSY_DETAIL") + s("WSY_TARGET")) / 3,
        "E": 0.5 * s("WSY_KOLABORATIF") + 0.5 * sosial,
        "A": (s("WSY_KOLABORATIF") + s("WSY_PELAYANAN")) / 2,
        "N": 1 - s("WSY_BERUBAH"),
    }
    return {k: round(max(0.0, min(1.0, v)), 4) for k, v in hasil.items()}


# ─────────────────────────────────────────────────────────────────────────────
def baca_sheet(wb, nama: str) -> list[dict]:
    baris = list(wb[nama].iter_rows(values_only=True))
    kepala = [str(k) for k in baris[0]]
    return [dict(zip(kepala, b)) for b in baris[1:] if any(c is not None for c in b)]


def baca_csv(nama: str) -> list[dict]:
    with open(SUMBER / nama, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    wb = openpyxl.load_workbook(SUMBER / "knowledge_base_profesi_IT.xlsx", read_only=True)

    with open(SUMBER / "onet_riasec_profesi_ti.csv", newline="", encoding="utf-8") as f:
        onet = {b["profesi"]: b for b in csv.DictReader(f)}

    workstyle: dict[str, dict[str, float]] = {}
    with open(SUMBER / "onet_workstyle_profesi_ti.csv", newline="", encoding="utf-8") as f:
        for b in csv.DictReader(f):
            workstyle.setdefault(b["soc_code"], {})[b["atribut"]] = float(b["skor"])

    # Patokan gaji: median dari median per jenjang senioritas, kalau ada.
    median_gaji: dict[str, list[int]] = {}
    for b in baca_sheet(wb, "salary_benchmarks"):
        median_gaji.setdefault(b["career_id"], []).append(int(b["salary_median_idr"]))

    profesi = []
    for b in baca_sheet(wb, "careers"):
        nama = b["career_title"]
        if nama not in onet:
            raise ValueError(f"profesi tanpa padanan O*NET: {nama}")
        o = onet[nama]
        riasec = {h: float(o[f"{h.lower()}_raw"]) for h in "RIASEC"}
        pola = pola_kerja(b["work_type"])
        lokasi_teks = str(b["location_bias"])
        semua_kota = lokasi_teks.lower().startswith("semua")
        lokasi = [] if semua_kota else [
            k.strip() for k in lokasi_teks.split(",") if k.strip().lower() != "remote"
        ]
        gaji_min, gaji_maks = int(b["min_salary_idr"]), int(b["max_salary_idr"])
        rank = rank_pendidikan_min(str(b["min_education"]))

        profesi.append({
            "id": b["career_id"],
            "nama": nama,
            "nama_en": b["career_title_en"],
            "sektor": b["sector"],
            "senioritas": b["seniority_level"],
            "pendidikan_min_rank": rank,
            "pendidikan_min_label": label_jenjang(rank),
            "pendidikan_sumber": b["min_education"],
            "pengalaman_min_tahun": int(b["min_experience_year"]),
            "gaji_min": gaji_min,
            "gaji_maks": gaji_maks,
            "gaji_median": int(statistics.median(median_gaji[b["career_id"]]))
            if b["career_id"] in median_gaji else (gaji_min + gaji_maks) // 2,
            "gaji_median_dari_patokan": b["career_id"] in median_gaji,
            "pola_kerja": pola,
            "lokasi": lokasi,
            "semua_kota": semua_kota,
            "deskripsi": b["career_description"],
            "tanggung_jawab": [t.strip() for t in str(b["key_responsibilities"]).split(";") if t.strip()],
            "jenjang_karier": b["career_path_next"],
            "soc_code": o["soc_code"],
            "soc_judul": o["judul_onet"],
            "soc_keyakinan": o["keyakinan"],
            "soc_catatan": o["catatan"],
            "riasec": riasec,
            "kode_holland": o["holland_code"],
            "big5_ideal": big5_ideal(workstyle[o["soc_code"]], riasec),
            "stabilitas": stabilitas(pola, b["sector"]),
        })

    skill = [
        {"id": b["skill_id"], "nama": b["skill_name"], "kategori": b["skill_category"],
         "tipe": b["skill_type"], "deskripsi": b["description"], "sumber": sumber}
        for sumber, daftar in (("lowongan", baca_sheet(wb, "skills")),
                               ("kurasi", baca_csv("pelengkap_skill.csv")))
        for b in daftar
    ]
    id_skill = {s["id"] for s in skill}

    profesi_skill: dict[str, list[dict]] = {}
    dari_lowongan: set[str] = set()
    for sumber, daftar in (("lowongan", baca_sheet(wb, "career_skills")),
                           ("kurasi", baca_csv("pelengkap_profesi_skill.csv"))):
        for b in daftar:
            if b["skill_id"] not in id_skill:
                raise ValueError(f"relasi menunjuk skill yang tidak ada: {b['skill_id']}")
            if sumber == "kurasi" and b["career_id"] in dari_lowongan:
                raise ValueError(f"pelengkap menimpa profesi yang sudah punya data: {b['career_id']}")
            profesi_skill.setdefault(b["career_id"], []).append({
                "skill_id": b["skill_id"],
                "wajib": bool(int(b["is_required"])),
                "bobot": float(b["skill_weight_pct"]),
                "catatan": b["notes"] or None,
                "sumber": sumber,
            })
        if sumber == "lowongan":
            dari_lowongan = set(profesi_skill)

    prodi = [
        {"id": b["prodi_id"], "nama": b["nama_prodi"], "jenjang": b["jenjang"], "rumpun": b["rumpun"],
         "relevansi": int(b["relevance_score"]),
         "profesi": [p.strip() for p in str(b["career_ids_recommended"]).split(",") if p.strip()]}
        for b in baca_sheet(wb, "program_studi")
    ]

    # Penjaga: basis pengetahuan yang bolong lebih baik gagal di sini daripada
    # diam-diam menghasilkan skor yang salah.
    tanpa_skill = [p["id"] for p in profesi if p["id"] not in profesi_skill]
    if tanpa_skill:
        raise ValueError(f"profesi tanpa skill: {tanpa_skill}")
    for p in profesi:
        if p["gaji_min"] > p["gaji_maks"]:
            raise ValueError(f"rentang gaji terbalik: {p['id']}")

    for p in profesi:
        p["skill_sumber"] = "lowongan" if p["id"] in dari_lowongan else "kurasi"

    kota = sorted({k for p in profesi for k in p["lokasi"]})

    kb = {
        "meta": {
            "dibuat": date.today().isoformat(),
            "n_profesi": len(profesi),
            "n_skill": len(skill),
            "n_relasi": sum(len(v) for v in profesi_skill.values()),
            "sumber": {
                "pasar_kerja": "knowledge_base_profesi_IT.xlsx — pengolahan lowongan kerja LinkedIn Indonesia 2025",
                "skill_kurasi": "pelengkap_*.csv — kurasi penulis untuk 9 profesi yang belum tercakup, perlu divalidasi",
                "riasec": "O*NET 30.3 Career Interest Types (USDOL/ETA, CC BY 4.0), lewat padanan kode SOC",
                "big5_ideal": "diturunkan dari O*NET Work Styles; lihat bangun_kb.py",
                "stabilitas": "proksi dari pola kerja dan sektor; lihat bangun_kb.py",
            },
        },
        "jenjang": JENJANG,
        "kota": kota,
        "profesi": profesi,
        "skill": skill,
        "profesi_skill": profesi_skill,
        "prodi": prodi,
    }

    KELUARAN.parent.mkdir(parents=True, exist_ok=True)
    KELUARAN.write_text(json.dumps(kb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{KELUARAN.relative_to(AKAR)}: {len(profesi)} profesi, {len(skill)} skill, "
          f"{kb['meta']['n_relasi']} relasi, {len(kota)} kota")


if __name__ == "__main__":
    main()
