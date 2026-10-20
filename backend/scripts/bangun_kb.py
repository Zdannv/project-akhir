"""Membangun basis pengetahuan (knowledge base) dari berkas sumber.

Tiga sumber digabung menjadi satu berkas JSON yang dibaca mesin rekomendasi:

  data/sumber/knowledge_base_profesi_IT.xlsx
      35 profesi TI, 114 skill, 308 relasi profesi-skill berbobot, patokan gaji.
      Hasil pengolahan lowongan kerja lokal (LinkedIn Indonesia, April–Juli 2026).

  data/sumber/pelengkap_skill.csv, pelengkap_profesi_skill.csv
      Workbook di atas punya dua lubang: sembilan profesi (C023, C028 - C035)
      belum punya relasi skill, dan banyak skill umum (machine learning,
      pengujian, jaringan, riset pengguna, ...) tidak ada di daftarnya. Dua
      berkas ini melengkapinya. Isinya KURASI PENULIS, bukan hasil pengolahan
      lowongan; setiap baris dari sini diberi sumber "kurasi" di keluaran
      supaya bisa dibedakan dan divalidasi belakangan.

  data/sumber/alias_skill.csv
      Nama lain tiap skill, hanya untuk pencarian di formulir.

  data/sumber/video_tutorial.csv
      Video tutorial YouTube per skill, dibuat scripts/ambil_video.py.

  data/sumber/bidang_ti.csv, bidang_profesi.csv
      Enam belas bidang kerja TI dan bobotnya di tiap profesi, bahan komponen
      "minat bidang" di KBF.

  data/sumber/sumber_belajar.csv, panduan_karier.csv, proyek_portofolio.csv
      Bahan belajar: tautan dokumentasi resmi dan kursus gratis per skill, peta
      belajar per profesi, dan ide proyek portofolio. Semuanya kurasi, hanya
      untuk ditampilkan, dan tidak memengaruhi skor.

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


def baca_csv(nama: str, pemisah: str = ",") -> list[dict]:
    with open(SUMBER / nama, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=pemisah))


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

    # Alias hanya untuk pencarian di formulir ("ReactJS" menemukan React.js);
    # tidak ikut dalam perhitungan.
    alias: dict[str, list[str]] = {}
    for b in baca_csv("alias_skill.csv"):
        if b["skill_id"] not in id_skill:
            raise ValueError(f"alias menunjuk skill yang tidak ada: {b['skill_id']}")
        alias.setdefault(b["skill_id"], []).append(b["alias"])
    for s in skill:
        s["alias"] = alias.get(s["id"], [])

    profesi_skill: dict[str, list[dict]] = {}
    for sumber, daftar in (("lowongan", baca_sheet(wb, "career_skills")),
                           ("kurasi", baca_csv("pelengkap_profesi_skill.csv"))):
        for b in daftar:
            if b["skill_id"] not in id_skill:
                raise ValueError(f"relasi menunjuk skill yang tidak ada: {b['skill_id']}")
            # Pelengkap boleh MENAMBAH skill ke profesi mana pun, tetapi tidak
            # boleh menimpa relasi yang sudah ada di data lowongan.
            if any(x["skill_id"] == b["skill_id"] for x in profesi_skill.get(b["career_id"], [])):
                raise ValueError(f"relasi ganda: {b['career_id']} - {b['skill_id']}")
            profesi_skill.setdefault(b["career_id"], []).append({
                "skill_id": b["skill_id"],
                "wajib": bool(int(b["is_required"])),
                "bobot": float(b["skill_weight_pct"]),
                "catatan": b["notes"] or None,
                "sumber": sumber,
            })

    # Sumber belajar per skill: tautan kurasi ke dokumentasi resmi, kursus, dan
    # latihan gratis. Hanya untuk ditampilkan; tidak ikut dalam perhitungan.
    belajar: dict[str, list[dict]] = {}
    for b in baca_csv("sumber_belajar.csv", "|"):
        if b["skill_id"] not in id_skill:
            raise ValueError(f"sumber belajar menunjuk skill yang tidak ada: {b['skill_id']}")
        if not b["url"].startswith("https://"):
            raise ValueError(f"tautan sumber belajar harus https: {b['url']}")
        belajar.setdefault(b["skill_id"], []).append(
            {"judul": b["judul"], "penyedia": b["penyedia"], "jenis": b["jenis"], "url": b["url"]})
    # Video tutorial hasil scripts/ambil_video.py: dipilih otomatis dari
    # pencarian YouTube dan dipastikan masih ada, tetapi isinya tidak ditinjau.
    if (SUMBER / "video_tutorial.csv").exists():
        with open(SUMBER / "video_tutorial.csv", newline="", encoding="utf-8") as f:
            for b in csv.DictReader(f, delimiter="|", quoting=csv.QUOTE_NONE):
                if b["skill_id"] not in id_skill:
                    continue  # skill-nya sudah dihapus dari katalog
                if not b["url"].startswith("https://www.youtube.com/watch?v="):
                    raise ValueError(f"tautan video tidak sah: {b['url']}")
                belajar.setdefault(b["skill_id"], []).append({
                    "judul": b["judul"], "penyedia": b["kanal"], "jenis": "video",
                    "url": b["url"], "durasi": b["durasi"]})
    for s in skill:
        s["belajar"] = belajar.get(s["id"], [])

    # Panduan per profesi: peta belajar dari roadmap.sh dan ide proyek portofolio.
    id_profesi = {p["id"] for p in profesi}
    peta = {b["career_id"]: {"judul": b["judul"], "url": b["url"]} for b in baca_csv("panduan_karier.csv", "|")}
    proyek: dict[str, list[dict]] = {}
    for b in baca_csv("proyek_portofolio.csv", "|"):
        proyek.setdefault(b["career_id"], []).append(
            {"tingkat": b["tingkat"], "judul": b["judul"], "deskripsi": b["deskripsi"]})
    if (set(peta) | set(proyek)) - id_profesi:
        raise ValueError("panduan karier menunjuk profesi yang tidak ada")
    # Bidang kerja TI tiap profesi. Bidang utama mengikuti kolom sektor di data
    # lowongan; bidang sekunder (bobot < 1) ditambahkan untuk profesi lintas
    # bidang, mis. Data Engineer = data + infrastruktur.
    bidang = [{"kode": b["kode"], "nama": b["nama"], "pertanyaan": b["pertanyaan"]}
              for b in baca_csv("bidang_ti.csv", "|")]
    kode_bidang = {b["kode"] for b in bidang}
    bidang_profesi: dict[str, dict[str, float]] = {}
    for b in baca_csv("bidang_profesi.csv", "|"):
        if b["bidang"] not in kode_bidang or b["career_id"] not in id_profesi:
            raise ValueError(f"bidang profesi tidak sah: {b}")
        bidang_profesi.setdefault(b["career_id"], {})[b["bidang"]] = float(b["bobot"])
    tanpa_bidang = id_profesi - set(bidang_profesi)
    if tanpa_bidang:
        raise ValueError(f"profesi tanpa bidang: {sorted(tanpa_bidang)}")
    for p in profesi:
        p["bidang"] = bidang_profesi[p["id"]]

    for p in profesi:
        p["peta_belajar"] = peta.get(p["id"])
        p["proyek"] = proyek.get(p["id"], [])

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

    # lowongan = seluruh skill dari data lowongan; kurasi = seluruhnya kurasi;
    # campuran = data lowongan yang ditambah skill kurasi.
    for p in profesi:
        asal = {r["sumber"] for r in profesi_skill[p["id"]]}
        p["skill_sumber"] = "campuran" if len(asal) > 1 else asal.pop()

    kota = sorted({k for p in profesi for k in p["lokasi"]})

    kb = {
        "meta": {
            "dibuat": date.today().isoformat(),
            "n_profesi": len(profesi),
            "n_skill": len(skill),
            "n_relasi": sum(len(v) for v in profesi_skill.values()),
            "n_relasi_kurasi": sum(1 for v in profesi_skill.values() for r in v if r["sumber"] == "kurasi"),
            "sumber": {
                "pasar_kerja": "knowledge_base_profesi_IT.xlsx — pengolahan lowongan kerja LinkedIn Indonesia 2025",
                "skill_kurasi": "pelengkap_*.csv — kurasi penulis: skill untuk 9 profesi yang belum tercakup "
                                "dan skill umum yang belum ada di data lowongan; perlu divalidasi",
                "riasec": "O*NET 30.3 Career Interest Types (USDOL/ETA, CC BY 4.0), lewat padanan kode SOC",
                "big5_ideal": "diturunkan dari O*NET Work Styles; lihat bangun_kb.py",
                "stabilitas": "proksi dari pola kerja dan sektor; lihat bangun_kb.py",
            },
        },
        "jenjang": JENJANG,
        "bidang": bidang,
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
