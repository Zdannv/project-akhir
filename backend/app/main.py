"""API sistem rekomendasi profesi TI.

Jalankan:  uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Literal

import csv
import io
import os
import secrets

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import evaluasi as ev
from . import kuesioner as q
from . import penyimpanan as db
from . import roadmap as rm
from .cbf import LABEL_TINGKAT, kesenjangan_skill
from .hibrida import Konfigurasi, rekomendasi
from .kb import AKAR, muat_kb
from .kbf import DOMISILI_LAIN, ProfilPengguna, catatan_lokasi  # noqa: F401
from .sus import BUTIR_PENJELASAN, BUTIR_SUS, periksa_penjelasan, skor_sus


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
    # Seberapa cocok profesi itu menurut profesional sendiri (1..5). Profesi yang dijalani belum tentu
    # yang paling cocok; uji pakar dihitung ulang khusus responden yang merasa cocok (>= 4).
    kecocokan_profesi: int | None = Field(default=None, ge=1, le=5)
    jenjang: str
    prodi_id: str | None = None
    domisili: str
    bersedia_relokasi: bool
    ekspektasi_gaji: int = Field(ge=0, le=1_000_000_000)
    punya_tanggungan: bool
    riasec: dict[str, int]
    big5: dict[str, int]
    skill: dict[str, int] = Field(default_factory=dict)
    # Minat per bidang kerja TI (kode bidang -> 1..5) dan pengalaman di TI.
    # Dua-duanya opsional supaya isian lama tetap bisa dibaca.
    bidang: dict[str, int] = Field(default_factory=dict)
    pengalaman_tahun: float | None = Field(default=None, ge=0, le=50)
    # Skill yang tidak ada di pilihan, diketik sendiri. Disimpan dan dilaporkan,
    # tetapi tidak ikut dihitung: belum ada profesi yang bisa dicocokkan dengannya.
    skill_lain: list[str] = Field(default_factory=list, max_length=20)
    # Diisi kalau isian ini memperbarui isian sebelumnya.
    induk: str | None = None

    @field_validator("skill_lain")
    @classmethod
    def _rapikan_skill_lain(cls, v: list[str]) -> list[str]:
        bersih: list[str] = []
        for s in v:
            s = " ".join(s.split())[:40]
            if s and s.lower() not in {b.lower() for b in bersih}:
                bersih.append(s)
        return bersih

    @field_validator("nama")
    @classmethod
    def _rapikan(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("nama tidak boleh kosong")
        return v


class Target(BaseModel):
    profesi_id: str | None


class Centang(BaseModel):
    skill_id: str
    selesai: bool


class UmpanBalik(BaseModel):
    penilaian: dict[str, bool]


class JawabanSus(BaseModel):
    jawaban: list[int]
    penjelasan: list[int] | None = None  # evaluasi penjelasan; opsional untuk klien lama


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
    kode_bidang = {b["kode"] for b in kb.bidang}
    if m.bidang and (set(m.bidang) != kode_bidang or any(not 1 <= v <= 5 for v in m.bidang.values())):
        raise HTTPException(422, "jawaban minat bidang belum lengkap atau di luar skala 1-5")
    try:
        return ev.profil_dari_masukan(m.model_dump(), kb)
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
        "bidang": {
            "skala": q.LABEL_SKALA_MINAT,
            "butir": [{"kode": b["kode"], "teks": b["pertanyaan"], "nama": b["nama"]} for b in kb.bidang],
        },
        "pengalaman": [
            {"nilai": 0, "label": "Belum ada"},
            {"nilai": 0.5, "label": "Kurang dari 1 tahun"},
            {"nilai": 1.5, "label": "1–2 tahun"},
            {"nilai": 3, "label": "3–4 tahun"},
            {"nilai": 5, "label": "5 tahun atau lebih"},
        ],
        "sus": BUTIR_SUS,
        "penjelasan": BUTIR_PENJELASAN,
        "jenjang": kb.jenjang,
        "kota": kb.kota + [DOMISILI_LAIN],
        "prodi": [{"id": p["id"], "nama": f"{p['nama']} ({p['jenjang']})"} for p in kb.prodi],
        "skill": [{"id": s["id"], "nama": s["nama"], "kategori": s["kategori"], "tipe": s["tipe"],
                   "alias": s["alias"]} for s in kb.skill],
        "tingkat_skill": LABEL_TINGKAT,
        "profesi": [{"id": p["id"], "nama": p["nama"]} for p in kb.profesi],
    }


@app.post("/api/rekomendasi", status_code=201)
def buat_rekomendasi(m: Masukan) -> dict:
    profil = _profil(m)
    hasil = rekomendasi(profil, muat_kb(), Konfigurasi())
    hasil["profil"] = {"riasec": profil.riasec, "big5": profil.big5}
    if m.induk and db.ambil_responden(m.induk) is None:
        raise HTTPException(422, "isian sebelumnya tidak ditemukan")
    rid = db.simpan_responden(m.model_dump(exclude={"induk"}), hasil, m.induk)
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
        "target": _ringkas_target(r),
    }


def _ringkas_target(r: dict) -> dict | None:
    """Kartu profesi tujuan di Explore: nama, skor, dan progres roadmap."""
    if not r["target"]:
        return None
    kb = muat_kb()
    peta = rm.susun(ev.profil_dari_masukan(r["masukan"], kb), r["target"], r["centang"], kb)
    return {"profesi_id": r["target"], "nama": kb.cari_profesi(r["target"])["nama"],
            "progres": peta["progres"], "awal": peta["awal"], "proyeksi": peta["proyeksi"]}


@app.get("/api/rekomendasi/{rid}/masukan")
def ambil_masukan(rid: str) -> dict:
    """Jawaban mentah, untuk mengisi ulang formulir saat pengguna mengubah jawabannya."""
    return _responden(rid)["masukan"]


@app.put("/api/rekomendasi/{rid}/target", status_code=204)
def pilih_target(rid: str, t: Target) -> None:
    r = _responden(rid)
    if t.profesi_id is not None and t.profesi_id not in {
            b["profesi_id"] for b in r["hasil"]["peringkat_lengkap"]}:
        raise HTTPException(422, "profesi ini tidak lolos penyaringan, jadi tidak bisa dijadikan tujuan")
    db.simpan_target(rid, t.profesi_id)


@app.get("/api/rekomendasi/{rid}/roadmap")
def ambil_roadmap(rid: str) -> dict:
    r = _responden(rid)
    if not r["target"]:
        return {"target": None}
    kb = muat_kb()
    p = kb.cari_profesi(r["target"])
    peta = rm.susun(ev.profil_dari_masukan(r["masukan"], kb), r["target"], r["centang"], kb)
    return {"target": {"profesi_id": p["id"], "nama": p["nama"], "sektor": p["sektor"],
                       "skill_sumber": p["skill_sumber"], "peta_belajar": p["peta_belajar"],
                       "proyek": p["proyek"]}, **peta}


@app.post("/api/rekomendasi/{rid}/roadmap/centang", status_code=204)
def centang_roadmap(rid: str, c: Centang) -> None:
    r = _responden(rid)
    if not r["target"]:
        raise HTTPException(422, "pilih profesi tujuan dulu")
    if c.skill_id not in {s["skill_id"] for s in muat_kb().skill_profesi(r["target"])}:
        raise HTTPException(422, "skill ini bukan bagian dari roadmap profesi tujuan")
    db.simpan_centang(rid, c.skill_id, c.selesai)


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
        "skill_lain": m.get("skill_lain", []),
        "pengalaman_tahun": m.get("pengalaman_tahun"),
        "bidang": {b["nama"]: (m["bidang"][b["kode"]] - 1) / 4 for b in kb.bidang} if m.get("bidang") else None,
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
        "jadi_target": r["target"] == pid,
        "catatan_lokasi": catatan_lokasi(ev.profil_dari_masukan(r["masukan"], kb), p),
        "alpha": r["hasil"]["konfigurasi"]["alpha"],
        "kesenjangan": _dengan_belajar(
            kesenjangan_skill(r["masukan"]["skill"], kb.skill_profesi(pid), kb.nama_skill())),
        "prodi_terkait": [x["nama"] for x in kb.prodi if pid in x["profesi"]],
    }


def _dengan_belajar(k: dict) -> dict:
    """Skill yang belum dikuasai dilengkapi sumber belajarnya."""
    belajar = muat_kb().belajar_skill()
    return {**k, "belum": [{**s, "belajar": belajar[s["skill_id"]]} for s in k["belum"]]}


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
        if j.penjelasan is not None:
            periksa_penjelasan(j.penjelasan)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    db.simpan_sus(rid, j.jawaban, skor, j.penjelasan)
    return {"skor": skor}


# ── Dasbor peneliti ─────────────────────────────────────────────────────────
# Berisi data semua responden, jadi dijaga: kalau PA_KUNCI_PENELITI diisi,
# permintaan harus membawa kunci itu; kalau tidak, hanya bisa dibuka dari
# komputer yang menjalankan servernya.
def _peneliti(request: Request, kunci: str | None) -> None:
    rahasia = os.environ.get("PA_KUNCI_PENELITI")
    if rahasia:
        if not kunci or not secrets.compare_digest(kunci, rahasia):
            raise HTTPException(401, "kunci peneliti salah")
    elif request.client is None or request.client.host not in ("127.0.0.1", "::1", "testclient"):
        raise HTTPException(403, "dasbor peneliti hanya bisa dibuka dari komputer server")


@app.get("/api/peneliti/ringkasan")
def ringkasan_peneliti(request: Request, x_kunci: str | None = Header(default=None)) -> dict:
    _peneliti(request, x_kunci)
    kb = muat_kb()
    d = ev.data_responden(kb)
    if d is None:
        return {"n": 0}
    nama = {p["id"]: p["nama"] for p in kb.profesi}
    return {
        **d,
        "presisi": {str(k): v for k, v in d["presisi"].items()},
        "responden": [{
            "id": r["id"], "dibuat": r["dibuat"], "nama": r["nama"], "jenis": r["jenis"],
            "profesi_aktual": nama.get(r["profesi_aktual"]),
            "kode_holland": r["hasil"]["kode_holland"],
            "teratas": r["hasil"]["rekomendasi"][0]["nama"] if r["hasil"]["rekomendasi"] else None,
            "posisi_aktual": next((b["peringkat"] for b in r["hasil"]["peringkat_lengkap"]
                                   if b["profesi_id"] == r["profesi_aktual"]), None),
            "n_dinilai": len(r["umpan_balik"]), "skor_sus": r["skor_sus"],
        } for r in db.responden_terakhir()],
    }


@app.get("/api/peneliti/ekspor.csv")
def ekspor_peneliti(request: Request, x_kunci: str | None = Header(default=None)) -> Response:
    """Satu baris per responden, untuk diolah di SPSS / Excel."""
    _peneliti(request, x_kunci)
    kb = muat_kb()
    nama = {p["id"]: p["nama"] for p in kb.profesi}
    kode_r = [k for k, _, _ in q.BUTIR_RIASEC]
    kode_b = [k for k, _, _, _ in q.BUTIR_BIG5]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "dibuat", "jenis", "jenjang", "domisili", "bersedia_relokasi", "ekspektasi_gaji",
                "punya_tanggungan", "profesi_aktual", "kecocokan_profesi", "kode_holland", *kode_r, *kode_b, "n_skill",
                "skill_lain", *[f"rekomendasi_{i}" for i in range(1, 6)],
                *[f"relevan_{i}" for i in range(1, 6)], "posisi_profesi_aktual", "skor_sus",
                *[f"penjelasan_{i}" for i in range(1, len(BUTIR_PENJELASAN) + 1)]])
    for r in db.responden_terakhir():
        m, rek = r["masukan"], r["hasil"]["rekomendasi"]
        isi = lambda i: rek[i]["nama"] if i < len(rek) else ""  # noqa: E731
        rel = lambda i: ("" if i >= len(rek) or rek[i]["profesi_id"] not in r["umpan_balik"]  # noqa: E731
                         else int(r["umpan_balik"][rek[i]["profesi_id"]]))
        w.writerow([
            r["id"], r["dibuat"], r["jenis"], m["jenjang"], m["domisili"], int(m["bersedia_relokasi"]),
            m["ekspektasi_gaji"], int(m["punya_tanggungan"]), nama.get(r["profesi_aktual"], ""),
            m.get("kecocokan_profesi") or "", r["hasil"]["kode_holland"], *[m["riasec"][k] for k in kode_r], *[m["big5"][k] for k in kode_b],
            len(m["skill"]), "; ".join(m.get("skill_lain", [])), *[isi(i) for i in range(5)],
            *[rel(i) for i in range(5)],
            next((b["peringkat"] for b in r["hasil"]["peringkat_lengkap"]
                  if b["profesi_id"] == r["profesi_aktual"]), ""),
            "" if r["skor_sus"] is None else r["skor_sus"],
            *(r["penjelasan"] or [""] * len(BUTIR_PENJELASAN)),
        ])
    return Response(buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="responden.csv"'})


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
