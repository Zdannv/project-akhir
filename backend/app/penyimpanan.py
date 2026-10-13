"""Penyimpanan jawaban responden.

Dua tempat simpan, satu antarmuka:

  * SQLite    bawaan, untuk pengembangan dan demo luring. Satu berkas
              (data/pa.db atau PA_DB), tabelnya dibuat otomatis.
  * Postgres  dipakai kalau DATABASE_URL diisi, mis. Supabase saat aplikasi
              di-hosting. Tabelnya dibuat lewat supabase/migrations/.

Yang disimpan adalah jawaban MENTAH kuesioner, bukan hanya hasilnya, supaya
rekomendasi bisa dihitung ulang kalau rumus atau bobotnya berubah.

Hanya API yang membuka koneksi ke basis data. Peramban tidak pernah
mengaksesnya langsung, jadi di Supabase semua tabel dikunci dengan RLS tanpa
kebijakan: kunci publik (anon) tidak bisa membaca apa pun.
"""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .kb import AKAR

SKEMA_SQLITE = """
create table if not exists responden (
  id              text primary key,
  dibuat          text not null,
  nama            text not null,
  jenis           text not null,          -- 'mahasiswa' | 'profesional'
  profesi_aktual  text,                   -- id profesi; ground truth uji pakar
  masukan         text not null,          -- json: jawaban mentah
  hasil           text not null,          -- json: keluaran mesin saat itu
  induk           text,                   -- isian sebelumnya yang diperbarui isian ini
  target          text                    -- profesi tujuan yang dipilih, kalau ada
);
create table if not exists roadmap_centang (
  responden_id  text not null references responden(id) on delete cascade,
  skill_id      text not null,
  primary key (responden_id, skill_id)
);
create table if not exists umpan_balik (
  responden_id  text not null references responden(id) on delete cascade,
  profesi_id    text not null,
  relevan       integer not null,         -- 1 relevan, 0 tidak
  primary key (responden_id, profesi_id)
);
create table if not exists sus (
  responden_id  text primary key references responden(id) on delete cascade,
  jawaban       text not null,            -- json: 10 nilai 1..5
  skor          real not null
);
"""


def pakai_postgres() -> bool:
    return bool(os.environ.get("DATABASE_URL"))


def berkas_db() -> Path:
    return Path(os.environ.get("PA_DB", AKAR / "data" / "pa.db"))


def tersedia() -> bool:
    """Apakah ada tempat simpan yang bisa dibaca (untuk skrip evaluasi)."""
    return pakai_postgres() or berkas_db().exists()


class _Koneksi:
    """Pembungkus tipis supaya SQL yang sama jalan di SQLite dan Postgres.

    SQL ditulis dengan penanda `?`. Nilai JSON dilewatkan lewat `j()`, yang
    menjadi teks di SQLite dan jsonb di Postgres.
    """

    def __init__(self, mentah, postgres: bool) -> None:
        self.mentah, self._pg = mentah, postgres

    def j(self, nilai):
        if self._pg:
            from psycopg.types.json import Jsonb
            return Jsonb(nilai)
        return json.dumps(nilai, ensure_ascii=False)

    def jalankan(self, sql: str, param: tuple = ()) -> list[dict]:
        kursor = self.mentah.execute(sql.replace("?", "%s") if self._pg else sql, param)
        if not kursor.description:
            return []
        return [dict(b) for b in kursor.fetchall()]


@contextmanager
def koneksi():
    postgres = pakai_postgres()
    if postgres:
        import psycopg
        from psycopg.rows import dict_row
        # prepare_threshold=None: pooler Supabase (mode transaksi) tidak
        # mendukung prepared statement. Koneksi dibuka per permintaan karena
        # fungsi serverless tidak menyimpan koneksi antarpanggilan.
        k = psycopg.connect(os.environ["DATABASE_URL"], prepare_threshold=None, row_factory=dict_row)
    else:
        k = sqlite3.connect(berkas_db())
        k.row_factory = sqlite3.Row
        k.execute("pragma foreign_keys = on")
    try:
        yield _Koneksi(k, postgres)
        k.commit()
    finally:
        k.close()


def siapkan() -> None:
    """SQLite: membuat dan memutakhirkan tabel. Postgres: tabel dikelola migrasi."""
    if pakai_postgres():
        return
    berkas_db().parent.mkdir(parents=True, exist_ok=True)
    with koneksi() as k:
        k.mentah.executescript(SKEMA_SQLITE)
        # Basis data dari versi sebelumnya belum punya dua kolom ini.
        ada = {b["name"] for b in k.jalankan("pragma table_info(responden)")}
        for kolom in ("induk", "target"):
            if kolom not in ada:
                k.jalankan(f"alter table responden add column {kolom} text")


def _json(nilai):
    return json.loads(nilai) if isinstance(nilai, str) else nilai


def _waktu(nilai) -> str:
    return nilai if isinstance(nilai, str) else nilai.isoformat(timespec="seconds")


def _rakit(k: _Koneksi, baris: list[dict]) -> list[dict]:
    """Melengkapi baris responden dengan penilaian, SUS, dan centang roadmap.

    Tiga tabel anak diambil sekaligus untuk semua responden yang diminta,
    bukan satu per satu: dasbor peneliti memuat puluhan responden, dan di
    hosting tiap kueri adalah satu perjalanan jaringan.
    """
    if not baris:
        return []
    ids = tuple(b["id"] for b in baris)
    tanda = ",".join("?" * len(ids))
    relevan: dict[str, dict[str, bool]] = {}
    for r in k.jalankan(f"select * from umpan_balik where responden_id in ({tanda})", ids):
        relevan.setdefault(r["responden_id"], {})[r["profesi_id"]] = bool(r["relevan"])
    sus = {r["responden_id"]: r["skor"]
           for r in k.jalankan(f"select responden_id, skor from sus where responden_id in ({tanda})", ids)}
    centang: dict[str, set[str]] = {}
    for r in k.jalankan(f"select * from roadmap_centang where responden_id in ({tanda})", ids):
        centang.setdefault(r["responden_id"], set()).add(r["skill_id"])
    return [{
        "id": b["id"], "dibuat": _waktu(b["dibuat"]), "nama": b["nama"], "jenis": b["jenis"],
        "profesi_aktual": b["profesi_aktual"],
        "masukan": _json(b["masukan"]), "hasil": _json(b["hasil"]),
        "umpan_balik": relevan.get(b["id"], {}), "skor_sus": sus.get(b["id"]),
        "induk": b["induk"], "target": b["target"], "centang": centang.get(b["id"], set()),
    } for b in baris]


def simpan_responden(masukan: dict, hasil: dict, induk: str | None = None) -> str:
    rid = uuid.uuid4().hex
    with koneksi() as k:
        k.jalankan(
            "insert into responden (id, dibuat, nama, jenis, profesi_aktual, masukan, hasil, induk) "
            "values (?,?,?,?,?,?,?,?)",
            (rid, datetime.now(timezone.utc).isoformat(timespec="seconds"),
             masukan["nama"], masukan["jenis_responden"], masukan.get("profesi_aktual"),
             k.j(masukan), k.j(hasil), induk),
        )
    return rid


def ambil_responden(rid: str) -> dict | None:
    with koneksi() as k:
        hasil = _rakit(k, k.jalankan("select * from responden where id = ?", (rid,)))
    return hasil[0] if hasil else None


def perbarui_hasil(rid: str, hasil: dict) -> None:
    with koneksi() as k:
        k.jalankan("update responden set hasil = ? where id = ?", (k.j(hasil), rid))


def simpan_umpan_balik(rid: str, penilaian: dict[str, bool]) -> None:
    with koneksi() as k:
        for pid, v in penilaian.items():
            k.jalankan(
                "insert into umpan_balik (responden_id, profesi_id, relevan) values (?,?,?) "
                "on conflict (responden_id, profesi_id) do update set relevan = excluded.relevan",
                (rid, pid, int(v)),
            )


def simpan_sus(rid: str, jawaban: list[int], skor: float) -> None:
    with koneksi() as k:
        k.jalankan(
            "insert into sus (responden_id, jawaban, skor) values (?,?,?) on conflict (responden_id) "
            "do update set jawaban = excluded.jawaban, skor = excluded.skor",
            (rid, k.j(jawaban), skor),
        )


def semua_responden() -> list[dict]:
    with koneksi() as k:
        return _rakit(k, k.jalankan("select * from responden order by dibuat"))


def responden_terakhir() -> list[dict]:
    """Satu isian per orang: yang tidak pernah diperbarui oleh isian lain."""
    with koneksi() as k:
        return _rakit(k, k.jalankan(
            "select * from responden where id not in "
            "(select induk from responden where induk is not null) order by dibuat"))


def simpan_target(rid: str, profesi_id: str | None) -> None:
    with koneksi() as k:
        k.jalankan("update responden set target = ? where id = ?", (profesi_id, rid))


def simpan_centang(rid: str, skill_id: str, selesai: bool) -> None:
    with koneksi() as k:
        if selesai:
            k.jalankan("insert into roadmap_centang (responden_id, skill_id) values (?,?) "
                       "on conflict (responden_id, skill_id) do nothing", (rid, skill_id))
        else:
            k.jalankan("delete from roadmap_centang where responden_id = ? and skill_id = ?", (rid, skill_id))
