"""Uji statistik untuk evaluasi, tanpa pustaka tambahan.

Semua fungsi di sini murni (tanpa basis data) supaya bisa diuji langsung:

  * bootstrap_ci   selang kepercayaan persentil untuk metrik per kasus
  * mcnemar        uji eksak McNemar untuk dua konfigurasi pada kasus yang sama
                   (benar/salah per kasus, mis. profesi aktual masuk 5 teratas)
  * wilcoxon       uji peringkat bertanda Wilcoxon untuk nilai berpasangan
                   (mis. reciprocal rank), aproksimasi normal dengan koreksi seri
  * cohen_kappa    kesepakatan dua penilai, label kategoris
  * fleiss_kappa   kesepakatan tiga penilai atau lebih
  * wilson         selang kepercayaan 95% untuk proporsi
  * aiken_v        indeks validitas isi Aiken beserta p-value eksaknya
"""

from __future__ import annotations

import math
import random
from collections import Counter
from collections.abc import Callable, Sequence


def bootstrap_ci(nilai: Sequence[float], fungsi: Callable[[Sequence[float]], float] = None,
                 ulang: int = 2000, seed: int = 42, tingkat: float = 0.95) -> tuple[float, float]:
    """Selang kepercayaan persentil dari `ulang` sampel ulang dengan pengembalian."""
    fungsi = fungsi or (lambda xs: sum(xs) / len(xs))
    n = len(nilai)
    if n == 0:
        raise ValueError("bootstrap butuh minimal satu nilai")
    acak = random.Random(seed)
    sebaran = sorted(fungsi([nilai[acak.randrange(n)] for _ in range(n)]) for _ in range(ulang))
    a = (1 - tingkat) / 2
    return sebaran[int(a * ulang)], sebaran[min(ulang - 1, int((1 - a) * ulang))]


def _binom_dua_sisi(k: int, n: int) -> float:
    """P(X <= min(k, n-k)) * 2 untuk X ~ Binomial(n, 1/2), dibatasi 1."""
    if n == 0:
        return 1.0
    m = min(k, n - k)
    ekor = sum(math.comb(n, i) for i in range(m + 1)) / 2 ** n
    return min(1.0, 2 * ekor)


def mcnemar(a: Sequence[bool], b: Sequence[bool]) -> dict:
    """Uji eksak McNemar. a, b: berhasil/tidak per kasus untuk dua konfigurasi."""
    if len(a) != len(b):
        raise ValueError("panjang a dan b harus sama")
    hanya_a = sum(1 for x, y in zip(a, b) if x and not y)
    hanya_b = sum(1 for x, y in zip(a, b) if y and not x)
    return {"hanya_a": hanya_a, "hanya_b": hanya_b, "p": _binom_dua_sisi(hanya_a, hanya_a + hanya_b)}


def _phi(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def wilcoxon(a: Sequence[float], b: Sequence[float]) -> dict:
    """Uji peringkat bertanda Wilcoxon dua sisi. Selisih nol dibuang (metode Wilcoxon).

    p-value memakai aproksimasi normal dengan koreksi seri dan koreksi
    kontinuitas; untuk n < 10 hasilnya hanya indikatif dan dilaporkan begitu.
    """
    if len(a) != len(b):
        raise ValueError("panjang a dan b harus sama")
    d = [x - y for x, y in zip(a, b) if abs(x - y) > 1e-12]
    n = len(d)
    if n == 0:
        return {"n": 0, "w_plus": 0.0, "p": 1.0}
    urut = sorted(range(n), key=lambda i: abs(d[i]))
    peringkat = [0.0] * n
    i = 0
    seri = []
    while i < n:
        j = i
        while j + 1 < n and abs(abs(d[urut[j + 1]]) - abs(d[urut[i]])) < 1e-12:
            j += 1
        r = (i + j) / 2 + 1
        for t in range(i, j + 1):
            peringkat[urut[t]] = r
        seri.append(j - i + 1)
        i = j + 1
    w_plus = sum(r for r, x in zip(peringkat, d) if x > 0)
    rata = n * (n + 1) / 4
    var = n * (n + 1) * (2 * n + 1) / 24 - sum(t ** 3 - t for t in seri) / 48
    if var <= 0:
        return {"n": n, "w_plus": w_plus, "p": 1.0}
    z = (abs(w_plus - rata) - 0.5) / math.sqrt(var)
    return {"n": n, "w_plus": w_plus, "p": min(1.0, 2 * (1 - _phi(max(z, 0.0))))}


def cohen_kappa(a: Sequence, b: Sequence) -> float | None:
    if len(a) != len(b) or not a:
        raise ValueError("dua penilai harus menilai butir yang sama")
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return None if pe == 1 else (po - pe) / (1 - pe)


def fleiss_kappa(penilaian: Sequence[Sequence]) -> float | None:
    """penilaian[i] = label dari seluruh penilai untuk butir i (jumlah penilai sama)."""
    if not penilaian:
        raise ValueError("tidak ada butir")
    m = len(penilaian[0])
    if m < 2 or any(len(p) != m for p in penilaian):
        raise ValueError("setiap butir harus dinilai oleh jumlah penilai yang sama (>= 2)")
    kategori = sorted({x for p in penilaian for x in p}, key=str)
    N = len(penilaian)
    hitung = [Counter(p) for p in penilaian]
    P_i = [(sum(c[k] ** 2 for k in kategori) - m) / (m * (m - 1)) for c in hitung]
    p_j = [sum(c[k] for c in hitung) / (N * m) for k in kategori]
    Pbar, Pe = sum(P_i) / N, sum(x * x for x in p_j)
    return None if Pe == 1 else (Pbar - Pe) / (1 - Pe)


def wilson(berhasil: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = berhasil / n
    pusat = (p + z * z / (2 * n)) / (1 + z * z / n)
    lebar = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, pusat - lebar), min(1.0, pusat + lebar)


def aiken_v(nilai: Sequence[int], terendah: int = 1, kategori: int = 5) -> dict:
    """V = jumlah(r - terendah) / (n * (c - 1)).

    p-value eksak: peluang V setinggi ini atau lebih kalau tiap penilai memilih
    kategori secara acak seragam. Dihitung dengan konvolusi, jadi tidak perlu
    tabel kritis.
    """
    n = len(nilai)
    if n == 0:
        raise ValueError("butuh minimal satu penilai")
    if any(not terendah <= x < terendah + kategori for x in nilai):
        raise ValueError("nilai di luar skala")
    s = sum(x - terendah for x in nilai)
    v = s / (n * (kategori - 1))
    sebaran = [1.0]  # sebaran jumlah (r - terendah) di bawah hipotesis nol
    for _ in range(n):
        baru = [0.0] * (len(sebaran) + kategori - 1)
        for total, peluang in enumerate(sebaran):
            for x in range(kategori):
                baru[total + x] += peluang / kategori
        sebaran = baru
    return {"v": v, "p": sum(sebaran[s:])}
