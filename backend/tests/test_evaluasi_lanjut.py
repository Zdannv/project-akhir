"""Uji untuk evaluasi tambahan: lowongan nyata, baseline Jaccard, ablasi per komponen, reliabilitas."""

import pytest

from app.evaluasi import posisi_jaccard, relevansi_per_label, spearman_brown, uji_berpasangan
from app.kb import muat_kb
from app.kbf import SKEMA_BOBOT, ProfilPengguna
from app.lowongan import pola_skill, profesi_dari_judul, skill_dari_teks


@pytest.fixture(scope="module")
def kb():
    return muat_kb()


def test_profesi_dari_judul():
    assert profesi_dari_judul("Senior Data Scientist - Risk") == "C010"
    assert profesi_dari_judul("Business Intelligence Analyst") == "C008"
    assert profesi_dari_judul("AI/ML Engineer") == "C011"      # pola ML diperiksa sebelum AI
    assert profesi_dari_judul("Applied AI Engineer") == "C012"
    assert profesi_dari_judul("Data Engineer (Remote)") == "C009"
    assert profesi_dari_judul("Data Architect") is None         # tidak dipetakan, tidak dipakai


def test_skill_dari_teks_menghindari_alias_umum(kb):
    pola = pola_skill(kb)
    nama = kb.nama_skill()
    temu = {nama[s] for s in skill_dari_teks("We make dashboards with SQL and Python on Apache Spark.", pola)}
    assert {"SQL", "Python"} <= temu
    assert not any("Workflow Automation" in t or "Nginx" in t for t in temu)
    # Nama satu huruf peka huruf besar: "r" di tengah kata atau huruf kecil tidak terhitung.
    assert "R" in {nama[s] for s in skill_dari_teks("Proficient in R and SQL", pola)}
    assert "R" not in {nama[s] for s in skill_dari_teks("for r&d teams", pola)}


def test_skema_ablasi_berjumlah_satu():
    for nama in ("tanpa_riasec", "tanpa_bidang", "tanpa_kesiapan", "tanpa_stabilitas"):
        komp = nama.removeprefix("tanpa_")
        for bobot in SKEMA_BOBOT[nama]:
            assert komp not in bobot
            assert sum(bobot.values()) == pytest.approx(1.0)


def test_posisi_jaccard_mengutamakan_himpunan_paling_mirip(kb):
    skill = {r["skill_id"]: 2 for r in kb.skill_profesi("C007")}
    profil = ProfilPengguna(riasec={t: 0.5 for t in "RIASEC"}, big5={d: 0.5 for d in "OCEAN"},
                            rank_pendidikan=6, domisili="Jakarta", bersedia_relokasi=True,
                            ekspektasi_gaji=0, punya_tanggungan=False, skill=skill)
    assert posisi_jaccard(profil, "C007", kb) == 1


def test_spearman_brown():
    a = [1, 2, 3, 4, 5, 3]
    assert spearman_brown(a, a) == pytest.approx(1.0)
    assert spearman_brown([1, 1, 1], [1, 2, 3]) is None   # tanpa variasi
    # r = 0,5 -> 2(0,5) / 1,5
    x, y = [1, 2, 3, 4], [2, 1, 4, 3]
    assert spearman_brown(x, y) == pytest.approx(2 * 0.6 / 1.6)


def test_relevansi_per_label():
    responden = [{"hasil": {"rekomendasi": [{"profesi_id": "A", "skor": 0.8}, {"profesi_id": "B", "skor": 0.5},
                                            {"profesi_id": "C", "skor": 0.3}]},
                  "umpan_balik": {"A": 1, "B": 0}}]
    hasil = relevansi_per_label(responden)
    assert hasil["Sangat Cocok"] == (1.0, 1)
    assert hasil["Cukup Cocok"] == (0.0, 1)
    assert hasil["Kurang Cocok"] is None   # C belum dinilai


def test_uji_berpasangan():
    acuan, lain = [1, 1, 2, None], [2, 1, 1, None]
    u = uji_berpasangan(acuan, lain, k=1)
    assert (u["mcnemar"]["hanya_a"], u["mcnemar"]["hanya_b"]) == (1, 1)
