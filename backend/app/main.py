"""API sistem rekomendasi profesi TI.

Jalankan:  uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import kuesioner as q
from . import penyimpanan as db
from .cbf import LABEL_TINGKAT, kesenjangan_skill
from .hibrida import Konfigurasi, rekomendasi
from .kb import AKAR, muat_kb
from .kbf import DOMISILI_LAIN, ProfilPengguna
from .sus import BUTIR_SUS, skor_sus


@asynccontextmanager
async def daur_hidup(_: FastAPI):
    muat_kb()
    db.siapkan()
    yield


app = FastAPI(title="Sistem Rekomendasi Profesi TI", version="1.0.0", lifespan=daur_hidup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


class Masukan(BaseModel):
    nama: str = Field(min_length=1, max_length=80)
    jenis_responden: Literal["mahasiswa", "profesional"] = "mahasiswa"
    profesi_aktual: str | None = None
    jenjang: str
    prodi_id: str | None = None
    domisili: str
    bersedia_relokasi: bool
    ekspektasi_gaji: int = Field(ge=0, le=1_000_000_000)
    punya_tanggungan: bool
    riasec: dict[str, int]
    big5: dict[str, int]
    skill: dict[str, int] = Field(default_factory=dict)

    @field_validator("nama")
    @classmethod
    def _rapikan(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("nama tidak boleh kosong")
        return v


class UmpanBalik(BaseModel):
    penilaian: dict[str, bool]


class JawabanSus(BaseModel):
    jawaban: list[int]


def _profil(m: Masukan) -> ProfilPengguna:
    kb = muat_kb()
    if m.jenjang not in {j["kode"] for j in kb.jenjang}:
        raise HTTPException(422, "jenjang pendidikan tidak dikenal")
    if m.domisili not in kb.kota and m.domisili != DOMISILI_LAIN:
        raise HTTPException(422, "domisili tidak dikenal")
    if m.profesi_aktual and not kb.cari_profesi(m.profesi_aktual):
        raise HTTPException(422, "profesi_aktual tidak dikenal")
    id_skill = {s["id"] for s in kb.skill}
    for sid, tingkat in m.skill.items():
        if sid not in id_skill or tingkat not in LABEL_TINGKAT:
            raise HTTPException(422, f"skill tidak sah: {sid}")
    try:
        return ProfilPengguna(
            riasec=q.skor_riasec(m.riasec), big5=q.skor_big5(m.big5),
            rank_pendidikan=kb.rank_jenjang(m.jenjang), domisili=m.domisili,
            bersedia_relokasi=m.bersedia_relokasi, ekspektasi_gaji=m.ekspektasi_gaji,
            punya_tanggungan=m.punya_tanggungan, skill=m.skill,
        )
    except ValueError as e:
        raise HTTPException(422, str(e)) from e


@app.get("/api/kuesioner")
def ambil_kuesioner() -> dict:
    """Semua yang dibutuhkan formulir: butir, pilihan, dan daftar skill."""
    kb = muat_kb()
    return {
        "riasec": {
            "skala": q.LABEL_SKALA_MINAT,
            "butir": [{"kode": k, "teks": t} for k, _, t in q.BUTIR_RIASEC],
        },
        "big5": {
            "skala": q.LABEL_SKALA_SETUJU,
            "awalan": q.AWALAN_BIG5,
            "butir": [{"kode": k, "teks": t} for k, _, _, t in q.BUTIR_BIG5],
        },
        "sus": BUTIR_SUS,
        "jenjang": kb.jenjang,
        "kota": kb.kota + [DOMISILI_LAIN],
        "prodi": [{"id": p["id"], "nama": f"{p['nama']} ({p['jenjang']})"} for p in kb.prodi],
        "skill": [{"id": s["id"], "nama": s["nama"], "kategori": s["kategori"], "tipe": s["tipe"]}
                  for s in kb.skill],
        "tingkat_skill": LABEL_TINGKAT,
        "profesi": [{"id": p["id"], "nama": p["nama"]} for p in kb.profesi],
    }


@app.post("/api/rekomendasi", status_code=201)
def buat_rekomendasi(m: Masukan) -> dict:
    profil = _profil(m)
    hasil = rekomendasi(profil, muat_kb(), Konfigurasi())
    hasil["profil"] = {"riasec": profil.riasec, "big5": profil.big5}
    rid = db.simpan_responden(m.model_dump(), hasil)
    return {"id": rid}


def _responden(rid: str) -> dict:
    r = db.ambil_responden(rid)
    if r is None:
        raise HTTPException(404, "hasil tidak ditemukan")
    return r


@app.get("/api/rekomendasi/{rid}")
def ambil_rekomendasi(rid: str) -> dict:
    r = _responden(rid)
    return {
        "id": r["id"], "nama": r["nama"], "dibuat": r["dibuat"], "jenis": r["jenis"],
        "hasil": r["hasil"], "umpan_balik": r["umpan_balik"], "skor_sus": r["skor_sus"],
        "data_diri": _data_diri(r["masukan"]),
    }


def _data_diri(m: dict) -> dict:
    """Ringkasan masukan untuk layar Profil — tanpa jawaban kuesioner mentah."""
    kb = muat_kb()
    nama_skill = kb.nama_skill()
    return {
        "jenjang": next(j["nama"] for j in kb.jenjang if j["kode"] == m["jenjang"]),
        "prodi": next((f"{p['nama']} ({p['jenjang']})" for p in kb.prodi if p["id"] == m.get("prodi_id")), None),
        "domisili": m["domisili"],
        "bersedia_relokasi": m["bersedia_relokasi"],
        "ekspektasi_gaji": m["ekspektasi_gaji"],
        "punya_tanggungan": m["punya_tanggungan"],
        "skill": [{"nama": nama_skill[sid], "tingkat": LABEL_TINGKAT[t]}
                  for sid, t in sorted(m["skill"].items(), key=lambda x: -x[1])],
    }


@app.get("/api/rekomendasi/{rid}/profesi/{pid}")
def detail_profesi(rid: str, pid: str) -> dict:
    """Detail satu profesi dari sudut pandang responden ini."""
    r = _responden(rid)
    kb = muat_kb()
    p = kb.cari_profesi(pid)
    if p is None:
        raise HTTPException(404, "profesi tidak ditemukan")
    baris = next((b for b in r["hasil"]["rekomendasi"] if b["profesi_id"] == pid), None)
    ringkas = next((b for b in r["hasil"]["peringkat_lengkap"] if b["profesi_id"] == pid), None)
    tersaring = next((t for t in r["hasil"]["tersaring"] if t["profesi_id"] == pid), None)
    return {
        "profesi": p,
        "profil": r["hasil"]["profil"],
        "kode_holland_pengguna": r["hasil"]["kode_holland"],
        "penilaian": baris,
        "ringkas": ringkas,
        "tersaring": tersaring,
        "relevan": r["umpan_balik"].get(pid),
        "kesenjangan": kesenjangan_skill(r["masukan"]["skill"], kb.skill_profesi(pid), kb.nama_skill()),
        "prodi_terkait": [x["nama"] for x in kb.prodi if pid in x["profesi"]],
    }


@app.post("/api/rekomendasi/{rid}/umpan-balik", status_code=204)
def kirim_umpan_balik(rid: str, u: UmpanBalik) -> None:
    r = _responden(rid)
    sah = {b["profesi_id"] for b in r["hasil"]["rekomendasi"]}
    if not u.penilaian or set(u.penilaian) - sah:
        raise HTTPException(422, "penilaian hanya untuk profesi yang direkomendasikan")
    db.simpan_umpan_balik(rid, u.penilaian)


@app.post("/api/rekomendasi/{rid}/sus")
def kirim_sus(rid: str, j: JawabanSus) -> dict:
    _responden(rid)
    try:
        skor = skor_sus(j.jawaban)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    db.simpan_sus(rid, j.jawaban, skor)
    return {"skor": skor}


# Antarmuka hasil build (frontend/dist) dilayani dari server yang sama, supaya
# demo cukup satu perintah dan tetap jalan tanpa internet.
DIST = AKAR / "frontend" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{jalur:path}", include_in_schema=False)
    def antarmuka(jalur: str) -> FileResponse:
        berkas = (DIST / jalur).resolve()
        if jalur and berkas.is_file() and DIST.resolve() in berkas.parents:
            return FileResponse(berkas)
        return FileResponse(DIST / "index.html")
