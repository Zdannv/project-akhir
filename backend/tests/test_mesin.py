"""Pengujian mesin rekomendasi (white-box)."""

import math

import pytest

from app import kuesioner as q
from app.cbf import kesenjangan_skill, skor_cbf
from app.hibrida import Konfigurasi, peringkat, rekomendasi
from app.kb import muat_kb
from app.kbf import (BOBOT_TANGGUNGAN, BOBOT_TANPA, ProfilPengguna, alasan_tersaring,
                     kecocokan_big5, kecocokan_finansial, kongruensi_iachan,
                     kongruensi_korelasi, skor_kbf)

KB = muat_kb()


def profil(**ubah) -> ProfilPengguna:
    dasar = dict(
        riasec=dict(R=0.4, I=0.9, A=0.3, S=0.2, E=0.2, C=0.8),
        big5=dict(O=0.8, C=0.8, E=0.3, A=0.4, N=0.4),
        rank_pendidikan=4, domisili="Surabaya", bersedia_relokasi=True,
        ekspektasi_gaji=7_000_000, punya_tanggungan=False,
        skill={"SK001": 3, "SK015": 3, "SK068": 2},
    )
    return ProfilPengguna(**(dasar | ubah))


# ── Basis pengetahuan ───────────────────────────────────────────────────────
def test_kb_lengkap():
    assert len(KB.profesi) == 35
    for p in KB.profesi:
        assert KB.skill_profesi(p["id"]), p["id"]
        assert len(p["kode_holland"]) == 3
        assert set(p["big5_ideal"]) == set("OCEAN")
        assert all(0 <= v <= 1 for v in p["big5_ideal"].values())
        assert 0 <= p["stabilitas"] <= 1
        assert p["gaji_min"] <= p["gaji_maks"]


# ── Kuesioner ───────────────────────────────────────────────────────────────
def test_skor_riasec_rata_dan_normal():
    jawab = {k: 3 for k, _, _ in q.BUTIR_RIASEC} | {"I1": 5, "I2": 5, "I3": 5, "S1": 1, "S2": 1, "S3": 1}
    s = q.skor_riasec(jawab)
    assert s["I"] == 1.0 and s["S"] == 0.0 and s["R"] == 0.5


def test_skor_big5_butir_terbalik():
    # B1 (terbalik) = 1 dan B6 = 5 -> ekstraversi maksimum
    jawab = {k: 3 for k, _, _, _ in q.BUTIR_BIG5} | {"B1": 1, "B6": 5}
    assert q.skor_big5(jawab)["E"] == 1.0


def test_jawaban_tidak_lengkap_ditolak():
    with pytest.raises(ValueError):
        q.skor_riasec({"R1": 3})
    with pytest.raises(ValueError):
        q.skor_big5({k: 9 for k, _, _, _ in q.BUTIR_BIG5})


def test_kode_holland_seri_deterministik():
    assert q.kode_holland(dict(R=0.5, I=0.5, A=0.5, S=0.5, E=0.5, C=0.5)) == "RIA"
    assert q.kode_holland(dict(R=0.1, I=0.9, A=0.2, S=0.3, E=0.8, C=0.7)) == "IEC"


# ── KBF ─────────────────────────────────────────────────────────────────────
def test_iachan():
    assert kongruensi_iachan("ICR", "ICR") == 1.0
    assert kongruensi_iachan("SAE", "ICR") == 0.0
    # huruf pertama sama, sisanya tidak: 22/28
    assert kongruensi_iachan("ISA", "ICR") == pytest.approx(22 / 28)
    # kode sama tetapi urutan terbalik: 4 + 5 + 4 = 13
    assert kongruensi_iachan("RCI", "ICR") == pytest.approx(13 / 28)


def test_korelasi_riasec():
    a = dict(R=0.1, I=0.9, A=0.2, S=0.3, E=0.4, C=0.8)
    assert kongruensi_korelasi(a, a) == pytest.approx(1.0)
    balik = {k: 1 - v for k, v in a.items()}
    assert kongruensi_korelasi(a, balik) == pytest.approx(0.0)
    rata = dict.fromkeys("RIASEC", 0.5)
    assert kongruensi_korelasi(rata, a) == 0.5


def test_big5_dan_finansial():
    x = dict(O=0.5, C=0.5, E=0.5, A=0.5, N=0.5)
    assert kecocokan_big5(x, x) == 1.0
    assert kecocokan_big5(dict.fromkeys("OCEAN", 0.0), dict.fromkeys("OCEAN", 1.0)) == pytest.approx(0.0)
    assert kecocokan_finansial(0, 5, 10) == 1.0
    assert kecocokan_finansial(5, 5, 10) == 1.0
    assert kecocokan_finansial(7, 5, 10) == pytest.approx(0.6)
    assert kecocokan_finansial(12, 5, 10) == 0.0


def test_bobot_berjumlah_satu():
    assert math.isclose(sum(BOBOT_TANGGUNGAN.values()), 1.0)
    assert math.isclose(sum(BOBOT_TANPA.values()), 1.0)


def test_stabilitas_hanya_untuk_yang_punya_tanggungan():
    p = KB.cari_profesi("C033")  # Blockchain Developer, stabilitas rendah
    tanpa = skor_kbf(profil(), p, skema="proposal")
    dengan = skor_kbf(profil(punya_tanggungan=True), p, skema="proposal")
    assert tanpa["bobot"]["stabilitas"] == 0 and dengan["bobot"]["stabilitas"] == 0.15
    assert dengan["skor"] < tanpa["skor"]


def test_minat_bidang_dan_kesiapan():
    from app.kbf import SKEMA_BOBOT, kesiapan_pengalaman, minat_bidang
    for skema in SKEMA_BOBOT.values():
        assert all(math.isclose(sum(b.values()), 1.0) for b in skema)

    assert minat_bidang(None, {"WEB": 1}) is None
    assert minat_bidang({"WEB": 1.0, "DATA": 0.0}, {"WEB": 1}) == 1.0
    assert minat_bidang({"WEB": 1.0, "DATA": 0.0}, {"DATA": 1, "WEB": 0.5}) == pytest.approx(0.5 / 1.5)

    assert kesiapan_pengalaman(None, 3) is None
    assert kesiapan_pengalaman(0, 0) == 1.0 and kesiapan_pengalaman(5, 3) == 1.0
    assert kesiapan_pengalaman(0, 3) == 0.0 and kesiapan_pengalaman(1.5, 3) == pytest.approx(0.5)

    # Komponen tanpa data dilewati dan bobotnya dinormalkan ulang.
    pm = KB.cari_profesi("C023")  # IT Project Manager, minimal 3 tahun
    tanpa_data = skor_kbf(profil(), pm)
    assert "bidang" not in tanpa_data["bobot"] and math.isclose(sum(tanpa_data["bobot"].values()), 1.0, abs_tol=1e-3)
    minat = dict.fromkeys((b["kode"] for b in KB.bidang), 0.5) | {"MANAJEMEN": 1.0}
    baru = skor_kbf(profil(bidang=minat, pengalaman=0), pm)
    senior = skor_kbf(profil(bidang=minat, pengalaman=5), pm)
    assert baru["komponen"]["kesiapan"] == 0.0 and senior["komponen"]["kesiapan"] == 1.0
    assert senior["skor"] > baru["skor"]


def test_saring_pendidikan():
    sma = profil(rank_pendidikan=1)
    assert alasan_tersaring(sma, KB.cari_profesi("C002"))[0]["kode"] == "pendidikan"
    assert alasan_tersaring(sma, KB.cari_profesi("C024")) == []  # IT Support menerima SMA/SMK


def test_saring_relokasi():
    network = KB.cari_profesi("C026")  # onsite, Jakarta/Surabaya/Bandung
    assert alasan_tersaring(profil(domisili="Bali", bersedia_relokasi=False), network)[0]["kode"] == "relokasi"
    assert alasan_tersaring(profil(domisili="Bali", bersedia_relokasi=True), network) == []
    assert alasan_tersaring(profil(domisili="Surabaya", bersedia_relokasi=False), network) == []
    # bisa remote -> domisili tidak jadi soal
    assert alasan_tersaring(profil(domisili="Lainnya", bersedia_relokasi=False), KB.cari_profesi("C002")) == []
    # IT Support: semua kota besar
    assert alasan_tersaring(profil(domisili="Lainnya", bersedia_relokasi=False), KB.cari_profesi("C024")) == []


# ── CBF ─────────────────────────────────────────────────────────────────────
def test_cbf():
    sp = [{"skill_id": "A", "bobot": 30, "wajib": True, "catatan": None},
          {"skill_id": "B", "bobot": 40, "wajib": False, "catatan": None}]
    assert skor_cbf({}, sp) == {"skor": 0.0, "cakupan": 0.0}
    assert skor_cbf({"Z": 3}, sp)["skor"] == 0.0
    # vektor pengguna searah dengan vektor profesi -> 1
    assert skor_cbf({"A": 3}, [sp[0]])["skor"] == 1.0
    penuh = skor_cbf({"A": 3, "B": 3}, sp)
    assert penuh["cakupan"] == 1.0
    # Skill di luar profesi: tidak berpengaruh di ruang profesi, mengencerkan di ruang global.
    assert skor_cbf({"A": 3, "B": 3, "Z": 3}, sp)["skor"] < penuh["skor"]
    assert skor_cbf({"A": 3, "B": 3, "Z": 3}, sp, "profesi")["skor"] == penuh["skor"]
    assert skor_cbf({"A": 3, "B": 3}, sp, "profesi")["skor"] == penuh["skor"]
    # Skill berbobot 0 bukan dimensi vektor profesi.
    nol = sp + [{"skill_id": "N", "bobot": 0, "wajib": True, "catatan": None}]
    assert skor_cbf({"A": 3, "B": 3}, nol)["skor"] == penuh["skor"]
    assert skor_cbf({"A": 3, "B": 3, "N": 3}, nol, "profesi")["skor"] == penuh["skor"]
    with pytest.raises(ValueError):
        skor_cbf({}, sp, "lain")
    assert skor_cbf({"A": 1}, sp)["skor"] == skor_cbf({"A": 3}, sp)["skor"]  # cosine: arah, bukan besar


def test_kesenjangan_urut_wajib_dulu():
    sp = [{"skill_id": "A", "bobot": 5, "wajib": True, "catatan": None},
          {"skill_id": "B", "bobot": 40, "wajib": False, "catatan": None},
          {"skill_id": "C", "bobot": 20, "wajib": True, "catatan": None}]
    g = kesenjangan_skill({"B": 2}, sp, {"A": "a", "B": "b", "C": "c"})
    assert [s["skill_id"] for s in g["belum"]] == ["C", "A"]
    assert g["dimiliki"][0]["label_tingkat"] == "Menengah"
    assert (g["wajib_terpenuhi"], g["wajib_total"]) == (0, 2)


# ── Hibrida ─────────────────────────────────────────────────────────────────
def test_rumus_hibrida():
    for alpha in (0.0, 0.6, 1.0):
        semua, _ = peringkat(profil(), KB, Konfigurasi(alpha=alpha))
        for b in semua:
            assert b["skor"] == pytest.approx(
                alpha * b["kbf"]["skor"] + (1 - alpha) * b["cbf"]["skor"], abs=1e-4)
        assert [b["skor"] for b in semua] == sorted((b["skor"] for b in semua), reverse=True)


def test_rekomendasi_top_n_dan_tersaring():
    h = rekomendasi(profil(rank_pendidikan=1), KB, Konfigurasi(top_n=3))
    assert h["n_lolos"] + h["n_tersaring"] == 35
    assert len(h["rekomendasi"]) == min(3, h["n_lolos"])
    lolos = {b["profesi_id"] for b in h["peringkat_lengkap"]}
    assert not lolos & {t["profesi_id"] for t in h["tersaring"]}
    assert all(b["alasan"] for b in h["rekomendasi"])


def test_skill_menggeser_peringkat():
    """Dua profil dengan minat sama tetapi skill berbeda harus mendapat urutan berbeda."""
    data = rekomendasi(profil(skill={"SK001": 3, "SK068": 3, "SK070": 3, "SK072": 3}), KB)
    web = rekomendasi(profil(skill={"SK002": 3, "SK016": 3, "SK021": 3, "SK003": 2}), KB)
    assert data["rekomendasi"][0]["profesi_id"] != web["rekomendasi"][0]["profesi_id"]


def test_cakupan_selalu_naik_saat_skill_bertambah():
    """Cakupan dipakai sebagai ukuran kemajuan di roadmap, jadi harus monoton."""
    dasar = {"SK001": 3, "SK015": 2}
    for p in KB.profesi:
        relasi = KB.skill_profesi(p["id"])
        sebelum = skor_cbf(dasar, relasi)["cakupan"]
        skill = dict(dasar)
        for s in relasi:
            if s["skill_id"] in skill:
                continue
            skill[s["skill_id"]] = 2
            sesudah = skor_cbf(skill, relasi)["cakupan"]
            assert sesudah >= sebelum and (sesudah > sebelum or s["bobot"] == 0), p["id"]
            sebelum = sesudah


def test_konfigurasi_bawaan_dan_proposal():
    from app.hibrida import KONFIG_PROPOSAL
    assert (Konfigurasi().alpha, Konfigurasi().metode_riasec) == (0.5, "korelasi")
    assert (KONFIG_PROPOSAL.alpha, KONFIG_PROPOSAL.metode_riasec) == (0.6, "iachan")
    # Minat merata dengan huruf pertama berbeda tipis: Iachan menjatuhkan, korelasi tidak.
    rata = profil(riasec=dict(R=0.58, I=0.83, A=0.67, S=1.0, E=1.0, C=0.92))
    dev = KB.cari_profesi("C003")
    assert skor_kbf(rata, dev, "iachan")["komponen"]["riasec"] < 0.2
    assert skor_kbf(rata, dev, "korelasi")["komponen"]["riasec"] > 0.4


def test_konfigurasi_tidak_sah():
    with pytest.raises(ValueError):
        Konfigurasi(alpha=1.2)
