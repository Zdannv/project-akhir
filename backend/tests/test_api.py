"""Pengujian API (black-box) dengan basis data sementara."""

import pytest
from fastapi.testclient import TestClient

from app import kuesioner as q
from app.sus import skor_sus


@pytest.fixture()
def klien(tmp_path, monkeypatch):
    monkeypatch.setenv("PA_DB", str(tmp_path / "uji.db"))
    from app.main import app
    with TestClient(app) as k:
        yield k


def masukan(**ubah) -> dict:
    dasar = {
        "nama": "Uji", "jenjang": "S1", "domisili": "Surabaya", "bersedia_relokasi": True,
        "ekspektasi_gaji": 6_000_000, "punya_tanggungan": False,
        "riasec": {k: 3 for k, _, _ in q.BUTIR_RIASEC} | {"I1": 5, "I2": 5, "I3": 5},
        "big5": {k: 3 for k, _, _, _ in q.BUTIR_BIG5},
        "skill": {"SK001": 3, "SK015": 2},
    }
    return dasar | ubah


def test_kuesioner(klien):
    d = klien.get("/api/kuesioner").json()
    assert len(d["riasec"]["butir"]) == 18 and len(d["big5"]["butir"]) == 10
    assert len(d["sus"]) == 10 and len(d["profesi"]) == 35
    assert "Lainnya" in d["kota"]


def test_alur_lengkap(klien):
    r = klien.post("/api/rekomendasi", json=masukan(profesi_aktual="C010", jenis_responden="profesional"))
    assert r.status_code == 201
    rid = r.json()["id"]

    h = klien.get(f"/api/rekomendasi/{rid}").json()
    rek = h["hasil"]["rekomendasi"]
    assert len(rek) == 5 and h["hasil"]["kode_holland"][0] == "I"

    pid = rek[0]["profesi_id"]
    d = klien.get(f"/api/rekomendasi/{rid}/profesi/{pid}").json()
    assert d["profesi"]["id"] == pid and d["penilaian"]["peringkat"] == 1

    assert klien.post(f"/api/rekomendasi/{rid}/umpan-balik",
                      json={"penilaian": {pid: True}}).status_code == 204
    assert klien.post(f"/api/rekomendasi/{rid}/umpan-balik",
                      json={"penilaian": {"C999": True}}).status_code == 422

    s = klien.post(f"/api/rekomendasi/{rid}/sus", json={"jawaban": [5, 1] * 5})
    assert s.json()["skor"] == 100.0
    h = klien.get(f"/api/rekomendasi/{rid}").json()
    assert h["umpan_balik"] == {pid: True} and h["skor_sus"] == 100.0


def test_validasi(klien):
    assert klien.post("/api/rekomendasi", json=masukan(jenjang="S9")).status_code == 422
    assert klien.post("/api/rekomendasi", json=masukan(domisili="Mars")).status_code == 422
    assert klien.post("/api/rekomendasi", json=masukan(skill={"SK001": 7})).status_code == 422
    assert klien.post("/api/rekomendasi", json=masukan(riasec={"R1": 3})).status_code == 422
    assert klien.post("/api/rekomendasi", json=masukan(nama="   ")).status_code == 422
    assert klien.get("/api/rekomendasi/tidakada").status_code == 404


def test_sus():
    assert skor_sus([3] * 10) == 50.0
    assert skor_sus([1, 5] * 5) == 0.0
    with pytest.raises(ValueError):
        skor_sus([3] * 9)


# ── Fitur lanjutan ──────────────────────────────────────────────────────────
def test_skill_lain_dirapikan_dan_tidak_memengaruhi_skor(klien):
    a = klien.post("/api/rekomendasi", json=masukan()).json()["id"]
    b = klien.post("/api/rekomendasi", json=masukan(
        skill_lain=["  Svelte ", "svelte", "COBOL", ""])).json()["id"]
    ha, hb = (klien.get(f"/api/rekomendasi/{x}").json() for x in (a, b))
    assert hb["data_diri"]["skill_lain"] == ["Svelte", "COBOL"]
    assert [r["skor"] for r in ha["hasil"]["rekomendasi"]] == [r["skor"] for r in hb["hasil"]["rekomendasi"]]


def test_target_dan_roadmap(klien):
    rid = klien.post("/api/rekomendasi", json=masukan()).json()["id"]
    assert klien.get(f"/api/rekomendasi/{rid}/roadmap").json() == {"target": None}
    assert klien.post(f"/api/rekomendasi/{rid}/roadmap/centang",
                      json={"skill_id": "SK068", "selesai": True}).status_code == 422

    assert klien.put(f"/api/rekomendasi/{rid}/target", json={"profesi_id": "C999"}).status_code == 422
    assert klien.put(f"/api/rekomendasi/{rid}/target", json={"profesi_id": "C007"}).status_code == 204

    r = klien.get(f"/api/rekomendasi/{rid}/roadmap").json()
    assert r["target"]["profesi_id"] == "C007" and r["tahap"][0]["kode"] == "pondasi"
    semua = [s for t in r["tahap"] for s in t["skill"]]
    assert r["progres"] == {"selesai": 0, "total": len(semua)}
    assert not {s["skill_id"] for s in semua} & {"SK001", "SK015"}  # yang sudah dikuasai tidak diulang
    assert r["proyeksi"] == r["awal"]

    # Mencentang skill menaikkan skor proyeksi, tetapi rekomendasi tersimpan tetap.
    sebelum = klien.get(f"/api/rekomendasi/{rid}").json()["hasil"]
    for s in r["tahap"][0]["skill"]:
        assert klien.post(f"/api/rekomendasi/{rid}/roadmap/centang",
                          json={"skill_id": s["skill_id"], "selesai": True}).status_code == 204
    r2 = klien.get(f"/api/rekomendasi/{rid}/roadmap").json()
    assert r2["progres"]["selesai"] == len(r["tahap"][0]["skill"])
    assert r2["proyeksi"]["cakupan"] > r2["awal"]["cakupan"] and r2["awal"] == r["awal"]
    assert r2["proyeksi"]["skor"] != r2["awal"]["skor"]
    h = klien.get(f"/api/rekomendasi/{rid}").json()
    assert h["hasil"] == sebelum and h["target"]["profesi_id"] == "C007"

    assert klien.post(f"/api/rekomendasi/{rid}/roadmap/centang",
                      json={"skill_id": "SK128", "selesai": True}).status_code == 422  # bukan skill profesi ini
    assert klien.put(f"/api/rekomendasi/{rid}/target", json={"profesi_id": None}).status_code == 204
    assert klien.get(f"/api/rekomendasi/{rid}").json()["target"] is None


def test_profesi_tersaring_tidak_bisa_jadi_target(klien):
    rid = klien.post("/api/rekomendasi", json=masukan(jenjang="SMA")).json()["id"]
    assert klien.put(f"/api/rekomendasi/{rid}/target", json={"profesi_id": "C003"}).status_code == 422
    assert klien.put(f"/api/rekomendasi/{rid}/target", json={"profesi_id": "C024"}).status_code == 204


def test_ubah_jawaban_tidak_dihitung_dua_kali(klien):
    lama = klien.post("/api/rekomendasi", json=masukan(nama="Satu")).json()["id"]
    isi = klien.get(f"/api/rekomendasi/{lama}/masukan").json()
    assert isi["riasec"]["I1"] == 5 and "induk" not in isi
    baru = klien.post("/api/rekomendasi", json=isi | {"skill": {"SK002": 3}, "induk": lama}).json()["id"]
    assert klien.post("/api/rekomendasi", json=masukan(induk="tidakada")).status_code == 422
    klien.post("/api/rekomendasi", json=masukan(nama="Dua"))

    d = klien.get("/api/peneliti/ringkasan").json()
    assert d["n"] == 2
    assert baru in {r["id"] for r in d["responden"]} and lama not in {r["id"] for r in d["responden"]}


def test_dasbor_peneliti(klien, monkeypatch):
    assert klien.get("/api/peneliti/ringkasan").json() == {"n": 0}
    rid = klien.post("/api/rekomendasi", json=masukan(
        profesi_aktual="C010", jenis_responden="profesional", skill_lain=["Svelte"])).json()["id"]
    klien.post(f"/api/rekomendasi/{rid}/sus", json={"jawaban": [4, 2] * 5})
    d = klien.get("/api/peneliti/ringkasan").json()
    assert d["n"] == 1 and d["n_pakar"] == 1 and d["sus"][0] == 75.0
    assert d["skill_lain"] == [["svelte", 1]] and d["responden"][0]["profesi_aktual"] == "Data Scientist"
    assert "Hibrida bawaan (korelasi, α = 0,5)" in d["pakar"] and len(d["pakar"]) == 5

    csv_ = klien.get("/api/peneliti/ekspor.csv")
    assert csv_.headers["content-type"].startswith("text/csv")
    baris = csv_.text.strip().splitlines()
    assert len(baris) == 2 and baris[0].startswith("id,dibuat,jenis") and "Svelte" in baris[1]

    monkeypatch.setenv("PA_KUNCI_PENELITI", "rahasia-uji")
    assert klien.get("/api/peneliti/ringkasan").status_code == 401
    assert klien.get("/api/peneliti/ringkasan", headers={"X-Kunci": "salah"}).status_code == 401
    assert klien.get("/api/peneliti/ringkasan", headers={"X-Kunci": "rahasia-uji"}).status_code == 200


def test_minat_bidang_dan_pengalaman(klien):
    k = klien.get("/api/kuesioner").json()
    assert len(k["bidang"]["butir"]) == 16 and k["pengalaman"][0]["nilai"] == 0
    bidang = {b["kode"]: 1 for b in k["bidang"]["butir"]} | {"DATA": 5}

    # Tanpa dua jawaban itu (isian lama) komponennya dilewati.
    lama = klien.get(f"/api/rekomendasi/{klien.post('/api/rekomendasi', json=masukan()).json()['id']}").json()
    assert "bidang" not in lama["hasil"]["rekomendasi"][0]["kbf"]["komponen"]

    rid = klien.post("/api/rekomendasi", json=masukan(bidang=bidang, pengalaman_tahun=0)).json()["id"]
    h = klien.get(f"/api/rekomendasi/{rid}").json()
    teratas = h["hasil"]["rekomendasi"][0]
    assert {"bidang", "kesiapan"} <= set(teratas["kbf"]["komponen"])
    assert abs(sum(teratas["kbf"]["bobot"].values()) - 1) < 1e-3
    assert h["data_diri"]["pengalaman_tahun"] == 0 and h["data_diri"]["bidang"]["Data & analitik"] == 1.0
    # Minat hanya pada data dan belum berpengalaman: profesi senior tidak di puncak.
    assert teratas["pengalaman_min_tahun"] <= 1

    assert klien.post("/api/rekomendasi", json=masukan(bidang={"DATA": 5})).status_code == 422
    assert klien.post("/api/rekomendasi", json=masukan(bidang=bidang | {"DATA": 9})).status_code == 422


def test_alias_skill(klien):
    skill = {s["id"]: s for s in klien.get("/api/kuesioner").json()["skill"]}
    assert "ReactJS" in skill["SK016"]["alias"] and len(skill) == 305


def test_sumber_belajar_dan_panduan(klien):
    rid = klien.post("/api/rekomendasi", json=masukan(skill={"SK015": 2})).json()["id"]
    d = klien.get(f"/api/rekomendasi/{rid}/profesi/C001").json()
    react = next(s for s in d["kesenjangan"]["belum"] if s["skill_id"] == "SK016")
    assert react["belajar"] and all(b["url"].startswith("https://") for b in react["belajar"])
    assert d["profesi"]["peta_belajar"]["url"] == "https://roadmap.sh/frontend"
    assert len(d["profesi"]["proyek"]) == 2

    klien.put(f"/api/rekomendasi/{rid}/target", json={"profesi_id": "C001"})
    r = klien.get(f"/api/rekomendasi/{rid}/roadmap").json()
    assert r["target"]["proyek"] and all("belajar" in s for t in r["tahap"] for s in t["skill"])
