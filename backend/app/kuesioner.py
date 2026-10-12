"""Tahap 1 — Profiling: butir kuesioner dan penskorannya.

Dua instrumen, keduanya skala Likert 1 - 5:

  * Minat RIASEC, 18 butir (3 per tipe). Butirnya disusun sendiri mengikuti
    enam tipe Holland, jadi BELUM tervalidasi; scripts/evaluasi.py menghitung
    Cronbach's alpha per tipe dari jawaban yang terkumpul sebagai bukti awal.
  * Kepribadian Big Five, BFI-10 (Rammstedt & John, 2007): 2 butir per dimensi,
    satu di antaranya berarah terbalik. Kalimat Indonesianya terjemahan
    penulis; untuk naskah, rujuk adaptasi Indonesia yang sudah terbit.

Semua skor dinormalkan ke 0 - 1 supaya sebanding dengan profil profesi.
"""

from __future__ import annotations

from .kb import BIG5, RIASEC

SKALA_MIN, SKALA_MAKS = 1, 5

LABEL_SKALA_MINAT = ["Sangat tidak suka", "Tidak suka", "Netral", "Suka", "Sangat suka"]
LABEL_SKALA_SETUJU = ["Sangat tidak setuju", "Tidak setuju", "Netral", "Setuju", "Sangat setuju"]

NAMA_RIASEC = {
    "R": "Realistic", "I": "Investigative", "A": "Artistic",
    "S": "Social", "E": "Enterprising", "C": "Conventional",
}
NAMA_BIG5 = {
    "O": "Openness", "C": "Conscientiousness", "E": "Extraversion",
    "A": "Agreeableness", "N": "Neuroticism",
}

# (kode, tipe, kalimat). Urutan tampil diselang antar tipe supaya butir setipe
# tidak berjejer dan memancing jawaban seragam.
BUTIR_RIASEC: list[tuple[str, str, str]] = [
    ("R1", "R", "Merakit atau memperbaiki perangkat elektronik — komputer, robot, atau alat listrik."),
    ("I1", "I", "Menelusuri penyebab sebuah masalah sampai ketemu akarnya."),
    ("A1", "A", "Merancang tampilan visual — poster, ilustrasi, atau antarmuka aplikasi."),
    ("S1", "S", "Menjelaskan sesuatu ke teman sampai dia benar-benar paham."),
    ("E1", "E", "Memimpin sebuah tim atau kegiatan."),
    ("C1", "C", "Menulis atau merapikan kode program supaya jalan sesuai aturan."),
    ("R2", "R", "Menguji apakah sebuah alat atau mesin benar-benar bekerja seperti yang dirancang."),
    ("I2", "I", "Mengolah data atau angka untuk menemukan pola yang tersembunyi."),
    ("A2", "A", "Membuat konten kreatif seperti video, tulisan, atau musik."),
    ("S2", "S", "Menemani atau membantu orang yang sedang kesulitan."),
    ("E2", "E", "Meyakinkan orang lain supaya setuju dengan ideku."),
    ("C2", "C", "Menyusun data atau catatan supaya rapi dan mudah dicari."),
    ("R3", "R", "Mengerjakan sesuatu dengan tangan sampai jadi barang yang bisa dipegang."),
    ("I3", "I", "Mencari tahu cara kerja sesuatu, walaupun tidak ada yang menyuruh."),
    ("A3", "A", "Mengerjakan tugas dengan caraku sendiri daripada mengikuti contoh yang sudah ada."),
    ("S3", "S", "Bekerja dalam kelompok dan memastikan semua anggotanya nyaman."),
    ("E3", "E", "Memikirkan ide usaha atau produk yang bisa dijual."),
    ("C3", "C", "Mengecek pekerjaan berulang kali supaya tidak ada yang terlewat."),
]

# (kode, dimensi, terbalik, kalimat). Awalan: "Saya melihat diri saya sebagai
# seseorang yang ..."
BUTIR_BIG5: list[tuple[str, str, bool, str]] = [
    ("B1", "E", True, "pendiam dan cenderung menahan diri."),
    ("B2", "A", False, "mudah percaya kepada orang lain."),
    ("B3", "C", True, "cenderung malas."),
    ("B4", "N", True, "santai dan bisa menghadapi tekanan dengan baik."),
    ("B5", "O", True, "kurang tertarik pada hal-hal yang berbau seni."),
    ("B6", "E", False, "mudah bergaul dan suka bersosialisasi."),
    ("B7", "A", True, "cenderung mencari-cari kesalahan orang lain."),
    ("B8", "C", False, "mengerjakan tugas sampai tuntas dan teliti."),
    ("B9", "N", False, "mudah merasa gugup atau cemas."),
    ("B10", "O", False, "punya imajinasi yang aktif."),
]
AWALAN_BIG5 = "Saya melihat diri saya sebagai seseorang yang …"


def _periksa(jawaban: dict[str, int], kode_wajib: list[str], nama: str) -> None:
    kurang = [k for k in kode_wajib if k not in jawaban]
    if kurang:
        raise ValueError(f"jawaban {nama} belum lengkap: {', '.join(kurang)}")
    for k in kode_wajib:
        if not SKALA_MIN <= jawaban[k] <= SKALA_MAKS:
            raise ValueError(f"jawaban {k} di luar skala {SKALA_MIN}-{SKALA_MAKS}")


def _normal(rata: float) -> float:
    return (rata - SKALA_MIN) / (SKALA_MAKS - SKALA_MIN)


def skor_riasec(jawaban: dict[str, int]) -> dict[str, float]:
    """Rata-rata butir per tipe, dinormalkan ke 0 - 1."""
    _periksa(jawaban, [k for k, _, _ in BUTIR_RIASEC], "minat")
    hasil = {}
    for tipe in RIASEC:
        nilai = [jawaban[k] for k, t, _ in BUTIR_RIASEC if t == tipe]
        hasil[tipe] = round(_normal(sum(nilai) / len(nilai)), 4)
    return hasil


def skor_big5(jawaban: dict[str, int]) -> dict[str, float]:
    """Rata-rata dua butir per dimensi (butir terbalik dibalik dulu), 0 - 1."""
    _periksa(jawaban, [k for k, _, _, _ in BUTIR_BIG5], "kepribadian")
    hasil = {}
    for dim in BIG5:
        nilai = [
            (SKALA_MIN + SKALA_MAKS - jawaban[k]) if terbalik else jawaban[k]
            for k, d, terbalik, _ in BUTIR_BIG5 if d == dim
        ]
        hasil[dim] = round(_normal(sum(nilai) / len(nilai)), 4)
    return hasil


def kode_holland(skor: dict[str, float], n: int = 3) -> str:
    """Tiga tipe tertinggi. Seri diputus menurut urutan baku R-I-A-S-E-C,
    supaya profil yang sama selalu menghasilkan kode yang sama."""
    urut = sorted(RIASEC, key=lambda t: (-skor[t], RIASEC.index(t)))
    return "".join(urut[:n])
