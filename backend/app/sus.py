"""System Usability Scale (Brooke, 1996)."""

from __future__ import annotations

BUTIR_SUS = [
    "Saya rasa saya akan sering menggunakan sistem ini.",
    "Saya merasa sistem ini rumit, padahal tidak perlu serumit itu.",
    "Saya merasa sistem ini mudah digunakan.",
    "Saya rasa saya butuh bantuan orang teknis untuk bisa menggunakan sistem ini.",
    "Saya merasa fitur-fitur di sistem ini terintegrasi dengan baik.",
    "Saya merasa ada terlalu banyak hal yang tidak konsisten di sistem ini.",
    "Saya rasa kebanyakan orang akan cepat belajar menggunakan sistem ini.",
    "Saya merasa sistem ini merepotkan untuk digunakan.",
    "Saya merasa percaya diri saat menggunakan sistem ini.",
    "Saya perlu mempelajari banyak hal dulu sebelum bisa menggunakan sistem ini.",
]


# Evaluasi penjelasan rekomendasi: apakah rincian poin dan kalimat alasan
# membuat pengguna paham dan percaya. Butir disusun mengikuti dimensi
# transparansi dan kepercayaan pada sistem rekomendasi yang dapat dijelaskan;
# skala 1 - 5, semuanya berarah positif.
BUTIR_PENJELASAN = [
    "Saya paham mengapa profesi-profesi tersebut direkomendasikan kepada saya.",
    "Rincian poin dan alasan membantu saya menilai apakah rekomendasinya tepat.",
    "Saya percaya rekomendasi profesi dari sistem ini.",
    "Penjelasan skill yang belum saya kuasai membuat saya tahu apa yang harus dipelajari.",
]


def periksa_penjelasan(jawaban: list[int]) -> None:
    if len(jawaban) != len(BUTIR_PENJELASAN) or any(not 1 <= j <= 5 for j in jawaban):
        raise ValueError(f"evaluasi penjelasan butuh {len(BUTIR_PENJELASAN)} jawaban bernilai 1-5")


def skor_sus(jawaban: list[int]) -> float:
    """Butir ganjil: nilai - 1; butir genap: 5 - nilai; jumlahnya dikali 2,5."""
    if len(jawaban) != 10 or any(not 1 <= j <= 5 for j in jawaban):
        raise ValueError("SUS butuh 10 jawaban bernilai 1-5")
    total = sum((j - 1) if i % 2 == 0 else (5 - j) for i, j in enumerate(jawaban))
    return total * 2.5
