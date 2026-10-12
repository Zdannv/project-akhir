# Sistem Rekomendasi Profesi Bidang Teknologi Informasi — Hybrid Filtering

Proyek akhir. Merekomendasikan profesi TI dengan menggabungkan
**Knowledge-Based Filtering** (syarat mutlak, minat RIASEC, kepribadian Big
Five, finansial, stabilitas) dan **Content-Based Filtering** (cosine similarity
skill):

    Skor_Final = α · Skor_KBF + (1 − α) · Skor_CBF        α = 0,6

Proyek ini berdiri sendiri dan terpisah dari Navika (proyek magang). Yang
diambil dari sana hanya gaya tampilan dan aset gambarnya.

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

## Pengujian dan evaluasi

```bash
cd backend
.venv/bin/python -m pytest                   # 22 uji: mesin (white-box) dan API (black-box)
.venv/bin/python scripts/evaluasi.py         # menulis docs/hasil-evaluasi.md
```

`evaluasi.py` punya dua bagian: simulasi persona sintetis (ablasi KBF/CBF/hibrida,
kepekaan α, Iachan vs korelasi) dan metrik dari responden sungguhan yang
tersimpan di `data/pa.db` (Hit Rate@K, Precision@K, SUS, Cronbach's α).

## Susunan

```
data/sumber/     berkas sumber: workbook lowongan, O*NET, pelengkap kurasi
data/kb/         basis pengetahuan hasil bangun_kb.py
data/pa.db       jawaban responden (tidak masuk repo)
backend/app/     kuesioner.py · kbf.py · cbf.py · hibrida.py · main.py (API)
backend/scripts/ bangun_kb.py · evaluasi.py
frontend/        React + Vite + Tailwind
docs/            keputusan-desain.md · hasil-evaluasi.md
```

Alasan di balik tiap keputusan, dan bedanya dengan buku proposal, ada di
[docs/keputusan-desain.md](docs/keputusan-desain.md).
