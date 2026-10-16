"""Uji statistik untuk evaluasi, dibandingkan dengan nilai yang bisa dihitung tangan."""

import math

import pytest

from app import statistik as st
from app.kb import RIASEC, campur_riasec, dengan_riasec, muat_kb


def test_mcnemar_eksak():
    # 6 kasus hanya benar di a, 1 kasus hanya benar di b: p = 2 * P(X <= 1 | n=7, p=1/2) = 2 * 8/128
    a = [True] * 6 + [False] + [True] * 3
    b = [False] * 6 + [True] + [True] * 3
    hasil = st.mcnemar(a, b)
    assert (hasil["hanya_a"], hasil["hanya_b"]) == (6, 1)
    assert hasil["p"] == pytest.approx(16 / 128)
    assert st.mcnemar([True, False], [True, False])["p"] == 1.0


def test_wilcoxon():
    sama = st.wilcoxon([0.5, 0.3, 1.0], [0.5, 0.3, 1.0])
    assert sama["n"] == 0 and sama["p"] == 1.0
    beda = st.wilcoxon([1.0] * 12, [0.5] * 12)
    assert beda["w_plus"] == pytest.approx(78) and beda["p"] < 0.01


def test_kappa():
    # Kesepakatan 65%, harapan kebetulan 0,55 x 0,5 + 0,45 x 0,5 = 50% -> kappa 0,3
    a = ["Ya"] * 35 + ["Tidak"] * 15 + ["Ya"] * 20 + ["Tidak"] * 30
    b = ["Ya"] * 35 + ["Ya"] * 15 + ["Tidak"] * 20 + ["Tidak"] * 30
    assert st.cohen_kappa(a, b) == pytest.approx((0.65 - 0.5) / 0.5)
    assert st.fleiss_kappa([["Ya", "Ya", "Ya"], ["Tidak", "Tidak", "Tidak"]]) == pytest.approx(1.0)


def test_aiken_v_dan_wilson():
    hasil = st.aiken_v([5, 5])
    assert hasil["v"] == 1.0 and hasil["p"] == pytest.approx(1 / 25)
    assert st.aiken_v([4, 5])["p"] == pytest.approx(3 / 25)
    lo, hi = st.wilson(8, 10)
    assert 0.49 < lo < 0.5 and 0.94 < hi < 0.95


def test_bootstrap_ci_mengapit_rata_rata():
    lo, hi = st.bootstrap_ci([0, 1] * 20)
    assert lo < 0.5 < hi


def test_campur_riasec():
    onet = dict.fromkeys(RIASEC, 4.0)
    lokal = [dict.fromkeys(RIASEC, 1.0)] * 5  # skala 0-1 -> 7 pada skala O*NET
    hasil = campur_riasec(onet, lokal, k=5)
    assert all(math.isclose(hasil[t], 5.5) for t in RIASEC)  # bobot lokal 5 / (5 + 5)
    assert campur_riasec(onet, [], k=5) == onet


def test_dengan_riasec_mengganti_profil_dan_kode():
    kb = muat_kb()
    pid = kb.profesi[0]["id"]
    baru = dengan_riasec(kb, {pid: {"R": 1, "I": 2, "A": 3, "S": 7, "E": 6, "C": 5}})
    assert baru.cari_profesi(pid)["kode_holland"] == "SEC"
    assert baru.cari_profesi(pid)["riasec_sumber"] == "kalibrasi lokal"
    assert "riasec_sumber" not in kb.cari_profesi(pid)  # aslinya tidak berubah
