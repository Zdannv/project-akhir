# Hosting: Vercel + Supabase

Susunannya:

```
peramban ──► Vercel ──┬─ frontend/dist      antarmuka React (berkas statis)
                      └─ api/index.py       API FastAPI sebagai fungsi Python
                                │
                                ▼
                            Supabase        Postgres: jawaban responden
```

Peramban hanya berbicara dengan Vercel. Hanya API yang berbicara dengan
Supabase, lewat koneksi Postgres (`DATABASE_URL`). Karena itu kunci
`anon` / `publishable` Supabase **tidak dipakai** di proyek ini dan tidak perlu
dipasang di mana pun; semua tabel dikunci RLS tanpa kebijakan, jadi kunci
publik itu tidak bisa membaca apa pun.

Basis pengetahuan (profesi, skill, bahan belajar) tidak disimpan di Supabase.
Ia berkas `data/kb/basis_pengetahuan.json` yang ikut ter-deploy bersama API.

## 1. Supabase: buat tabel

1. Buka proyek Supabase → **SQL Editor**.
2. Tempel isi `supabase/migrations/0001_skema.sql` → **Run**.
3. Pesan terakhirnya harus `0001: tabel penyimpanan siap, terkunci untuk kunci publik`.

## 2. Supabase: ambil connection string

**Project Settings → Database → Connection string → Transaction pooler** (port
6543). Bentuknya:

```
postgresql://postgres.<ref>:<SANDI>@aws-0-<region>.pooler.supabase.com:6543/postgres
```

Ganti `<SANDI>` dengan sandi basis data. Pakai *transaction pooler*, bukan
koneksi langsung: fungsi serverless membuka koneksi baru tiap permintaan dan
koneksi langsung cepat habis.

String ini memuat sandi. Jangan tempel di chat, di kode, atau di repo.

## 3. Vercel: impor repo

1. **Add New → Project** → impor repo GitHub ini.
2. Framework Preset: **Other**. Root Directory: biarkan kosong. Perintah build
   dan folder keluaran sudah diatur `vercel.json`.
3. **Environment Variables** (Production dan Preview):

   | Nama | Isi |
   |---|---|
   | `DATABASE_URL` | connection string dari langkah 2 |
   | `PA_KUNCI_PENELITI` | kunci buatan sendiri, panjang dan acak, untuk membuka `/peneliti` |

4. **Deploy**.

Tanpa `DATABASE_URL`, API mencoba memakai SQLite, yang tidak bisa menyimpan
apa pun di Vercel: kuesioner akan gagal saat disimpan. Tanpa
`PA_KUNCI_PENELITI`, dasbor peneliti tertutup untuk semua orang (itu sengaja).

## 4. Periksa setelah deploy

- `https://<domain>/api/kuesioner` menampilkan JSON.
- Isi kuesioner sampai selesai; hasilnya tampil dan satu baris muncul di tabel
  `responden` (Supabase → Table Editor).
- `https://<domain>/peneliti` meminta kunci, lalu menampilkan data.

## Memperbarui

- **Kode atau rumus:** push ke GitHub; Vercel men-deploy ulang sendiri.
- **Daftar profesi, skill, bahan belajar:** ubah berkas di `data/sumber/`,
  jalankan `python scripts/bangun_kb.py`, commit `data/kb/basis_pengetahuan.json`, push.
- **Menghitung ulang rekomendasi tersimpan** setelah rumus berubah, dari
  komputer sendiri:

  ```bash
  cd backend
  DATABASE_URL='...' .venv/bin/python scripts/hitung_ulang.py
  ```

  Sama untuk `scripts/evaluasi.py` dan `scripts/kalibrasi.py`: dengan
  `DATABASE_URL`, mereka membaca data responden dari Supabase.

## Pengembangan lokal

Tidak berubah. Tanpa `DATABASE_URL`, aplikasi memakai SQLite di `data/pa.db`
dan jalan tanpa internet. Rangkaian uji bisa dijalankan terhadap Postgres mana
pun yang sudah diberi skema `0001`:

```bash
DATABASE_URL='postgresql://...' .venv/bin/python -m pytest
```

Uji itu **mengosongkan tabel `responden`**. Jangan arahkan ke basis data
produksi.
