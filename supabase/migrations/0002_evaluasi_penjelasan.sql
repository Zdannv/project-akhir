-- 0002_evaluasi_penjelasan.sql
--
-- Empat butir evaluasi penjelasan rekomendasi (paham, membantu menilai,
-- percaya, tahu apa yang harus dipelajari), skala 1 - 5, diisi bersama SUS
-- di halaman Penilaian. Disimpan di baris SUS yang sama; NULL untuk responden
-- yang mengisi sebelum butir ini ada.
--
-- Jalankan setelah 0001. Aman diulang.

alter table public.sus add column if not exists penjelasan jsonb;
