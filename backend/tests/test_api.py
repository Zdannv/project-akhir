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
