# Sistem Rekomendasi Profesi Bidang Teknologi Informasi — Hybrid Filtering

Proyek akhir. Merekomendasikan profesi TI dengan menggabungkan
**Knowledge-Based Filtering** (syarat mutlak, minat RIASEC, minat bidang TI,
kepribadian Big Five, kesiapan pengalaman, finansial, stabilitas) dan **Content-Based Filtering** (cosine similarity
skill):

    Skor_Final = α · Skor_KBF + (1 − α) · Skor_CBF        α = 0,5

## Fitur

- **Profil karier** — kuesioner empat langkah: latar belakang, minat (RIASEC),
  kepribadian (Big Five), dan keahlian. Pencarian skill mengenali nama lain
  ("ReactJS", "Postgres"), dan skill yang tidak ada di daftar bisa diketik sendiri.
- **Explore** — lima profesi teratas beserta alasannya, peringkat lengkap, dan
  profesi yang tersaring berikut sebabnya.
- **Cari & filter** — menjelajah 35 profesi menurut sektor, pola kerja, dan gaji.
- **Detail profesi** — tiga tab: Analisa (rincian skor, diagram radar minat),
  Skill & Kompetensi (analisis kesenjangan skill), Insight (gaji, jenjang karier).
- **Profesi tujuan & roadmap** — skill yang belum dikuasai disusun tiga tahap,
  dengan simulasi: kalau skill ini dipelajari, cakupan, skor, dan peringkatnya
  jadi berapa.
- **Bahan belajar** — tiap skill punya tautan dokumentasi resmi, kursus gratis,
  dan video tutorial YouTube (kebanyakan berbahasa Indonesia); tiap profesi punya peta belajar, ide proyek
  portofolio, dan tautan lowongan.
- **Penilaian** — relevansi tiap rekomendasi dan kuesioner SUS.
- **Dasbor peneliti** (`/peneliti`) — Hit Rate@K, Precision@K, SUS, Cronbach's α,
  daftar responden, dan ekspor CSV.

## Menjalankan

Butuh Python 3.11+ dan Node 20+.

```bash
# 1. Backend
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/bangun_kb.py        # membangun data/kb/basis_pengetahuan.json

# 2. Antarmuka (sekali build, lalu dilayani backend)
cd ../frontend
npm install && npm run build

# 3. Jalankan
cd ../backend
.venv/bin/uvicorn app.main:app --port 8000
```

Buka http://127.0.0.1:8000. Setelah di-build, aplikasinya jalan tanpa internet.

Untuk pengembangan antarmuka: jalankan backend seperti di atas, lalu
`npm run dev` di `frontend/` dan buka http://localhost:5173.

## Hosting

Vercel (antarmuka + API Python) dan Supabase (Postgres). Langkahnya ada di
[docs/HOSTING.md](docs/HOSTING.md).

## Pengujian dan evaluasi

```bash
cd backend
.venv/bin/python -m pytest                   # 33 uji: mesin (white-box) dan API (black-box)
.venv/bin/python scripts/evaluasi.py         # menulis docs/hasil-evaluasi.md
.venv/bin/python scripts/kalibrasi.py        # mencari bobot dari data responden profesional
```

`evaluasi.py` punya dua bagian: simulasi persona sintetis (ablasi KBF/CBF/hibrida,
kepekaan α, Iachan vs korelasi, ruang vektor CBF) dan metrik dari responden
sungguhan yang tersimpan di `data/pa.db` (Hit Rate@K, Precision@K, SUS,
Cronbach's α, skill di luar pilihan). Angka yang sama tampil langsung di dasbor
peneliti.

## Dasbor peneliti

Buka http://127.0.0.1:8000/peneliti dari komputer yang menjalankan server.
Kalau aplikasinya dipasang di server yang bisa diakses orang lain, isi variabel
lingkungan `PA_KUNCI_PENELITI` sebelum menjalankan; dasbor lalu meminta kunci itu.

## Susunan

```
data/sumber/     berkas sumber: workbook lowongan, O*NET, pelengkap kurasi
data/kb/         basis pengetahuan hasil bangun_kb.py
data/pa.db       jawaban responden (tidak masuk repo)
backend/app/     kuesioner.py · kbf.py · cbf.py · hibrida.py · roadmap.py ·
                 evaluasi.py · main.py (API)
backend/scripts/ bangun_kb.py · evaluasi.py
frontend/        React + Vite + Tailwind
api/             titik masuk API di Vercel
supabase/        skema basis data untuk hosting
docs/            keputusan-desain.md · hasil-evaluasi.md
```

Alasan di balik tiap keputusan, dan bedanya dengan buku proposal, ada di
[docs/keputusan-desain.md](docs/keputusan-desain.md).
