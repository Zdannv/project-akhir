"""Penyimpanan SQLite.

Satu berkas, tanpa server: cukup untuk kebutuhan demo dan pengumpulan data
pengujian. Yang disimpan adalah jawaban MENTAH kuesioner, bukan hanya hasilnya,
supaya rekomendasi bisa dihitung ulang kalau rumus atau bobotnya berubah.
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

SKEMA = """
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


def berkas_db() -> Path:
    return Path(os.environ.get("PA_DB", AKAR / "data" / "pa.db"))


@contextmanager
def koneksi():
    k = sqlite3.connect(berkas_db())
    k.row_factory = sqlite3.Row
    k.execute("pragma foreign_keys = on")
    try:
        yield k
        k.commit()
    finally:
        k.close()


def siapkan() -> None:
    berkas_db().parent.mkdir(parents=True, exist_ok=True)
    with koneksi() as k:
        k.executescript(SKEMA)
        # Basis data dari versi sebelumnya belum punya dua kolom ini.
        ada = {b["name"] for b in k.execute("pragma table_info(responden)")}
        for kolom in ("induk", "target"):
            if kolom not in ada:
                k.execute(f"alter table responden add column {kolom} text")


def simpan_responden(masukan: dict, hasil: dict, induk: str | None = None) -> str:
    rid = uuid.uuid4().hex
    with koneksi() as k:
        k.execute(
            "insert into responden (id, dibuat, nama, jenis, profesi_aktual, masukan, hasil, induk) "
            "values (?,?,?,?,?,?,?,?)",
            (rid, datetime.now(timezone.utc).isoformat(timespec="seconds"),
             masukan["nama"], masukan["jenis_responden"], masukan.get("profesi_aktual"),
             json.dumps(masukan, ensure_ascii=False), json.dumps(hasil, ensure_ascii=False), induk),
        )
    return rid


def ambil_responden(rid: str) -> dict | None:
    with koneksi() as k:
        b = k.execute("select * from responden where id = ?", (rid,)).fetchone()
        if b is None:
            return None
        relevan = {r["profesi_id"]: bool(r["relevan"]) for r in
                   k.execute("select * from umpan_balik where responden_id = ?", (rid,))}
        sus = k.execute("select skor from sus where responden_id = ?", (rid,)).fetchone()
        centang = {r["skill_id"] for r in
                   k.execute("select skill_id from roadmap_centang where responden_id = ?", (rid,))}
    return {
        "id": b["id"], "dibuat": b["dibuat"], "nama": b["nama"], "jenis": b["jenis"],
        "profesi_aktual": b["profesi_aktual"],
        "masukan": json.loads(b["masukan"]), "hasil": json.loads(b["hasil"]),
        "umpan_balik": relevan, "skor_sus": sus["skor"] if sus else None,
        "induk": b["induk"], "target": b["target"], "centang": centang,
    }


def simpan_umpan_balik(rid: str, penilaian: dict[str, bool]) -> None:
    with koneksi() as k:
        k.executemany(
            "insert into umpan_balik values (?,?,?) "
            "on conflict (responden_id, profesi_id) do update set relevan = excluded.relevan",
            [(rid, pid, int(v)) for pid, v in penilaian.items()],
        )


def simpan_sus(rid: str, jawaban: list[int], skor: float) -> None:
    with koneksi() as k:
        k.execute(
            "insert into sus values (?,?,?) on conflict (responden_id) "
            "do update set jawaban = excluded.jawaban, skor = excluded.skor",
            (rid, json.dumps(jawaban), skor),
        )


def semua_responden() -> list[dict]:
    with koneksi() as k:
        ids = [r["id"] for r in k.execute("select id from responden order by dibuat")]
    return [ambil_responden(i) for i in ids]


def responden_terakhir() -> list[dict]:
    """Satu isian per orang: yang tidak pernah diperbarui oleh isian lain."""
    with koneksi() as k:
        ids = [r["id"] for r in k.execute(
            "select id from responden where id not in "
            "(select induk from responden where induk is not null) order by dibuat")]
    return [ambil_responden(i) for i in ids]


def simpan_target(rid: str, profesi_id: str | None) -> None:
    with koneksi() as k:
        k.execute("update responden set target = ? where id = ?", (profesi_id, rid))


def simpan_centang(rid: str, skill_id: str, selesai: bool) -> None:
    with koneksi() as k:
        if selesai:
            k.execute("insert or ignore into roadmap_centang values (?,?)", (rid, skill_id))
        else:
            k.execute("delete from roadmap_centang where responden_id = ? and skill_id = ?", (rid, skill_id))
