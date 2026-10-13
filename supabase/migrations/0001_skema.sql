-- ===========================================================================
-- 0001_skema.sql
--
-- Tabel penyimpanan jawaban responden untuk aplikasi yang di-hosting.
--
-- Jalankan sekali di Supabase: SQL Editor -> tempel -> Run. Aman diulang.
--
-- ---------------------------------------------------------------------------
-- Keamanan
-- ---------------------------------------------------------------------------
-- Hanya API (fungsi Python di Vercel) yang membaca dan menulis tabel ini,
-- lewat koneksi Postgres langsung (DATABASE_URL). Peramban tidak pernah
-- menghubungi Supabase. Karena itu RLS dinyalakan TANPA kebijakan apa pun:
-- kunci publik (anon / publishable) yang tertanam di sisi klien tidak bisa
-- membaca maupun menulis satu baris pun, walaupun kuncinya diketahui orang.
-- Koneksi API memakai peran pemilik tabel, yang tidak dibatasi RLS.
--
-- Isi tabel adalah jawaban kuesioner orang sungguhan (nama, minat,
-- kepribadian). Jangan menambah kebijakan "select untuk anon" di sini.
-- ===========================================================================

begin;

create table if not exists public.responden (
  id              text primary key,
  dibuat          timestamptz not null default now(),
  nama            text not null,
  jenis           text not null check (jenis in ('mahasiswa', 'profesional')),
  profesi_aktual  text,
  masukan         jsonb not null,
  hasil           jsonb not null,
  induk           text,
  target          text
);

comment on table public.responden is
  'Satu baris per pengisian kuesioner. masukan = jawaban mentah; hasil = keluaran mesin saat itu.';
comment on column public.responden.profesi_aktual is
  'Id profesi responden profesional; jawaban benar untuk uji pakar (Hit Rate@K).';
comment on column public.responden.induk is
  'Isian sebelumnya yang diperbarui isian ini. Evaluasi hanya menghitung isian tanpa penerus.';
comment on column public.responden.target is
  'Profesi tujuan yang dipilih untuk roadmap.';

create index if not exists idx_responden_dibuat on public.responden (dibuat);
create index if not exists idx_responden_induk on public.responden (induk) where induk is not null;

create table if not exists public.umpan_balik (
  responden_id  text not null references public.responden(id) on delete cascade,
  profesi_id    text not null,
  relevan       smallint not null check (relevan in (0, 1)),
  primary key (responden_id, profesi_id)
);

create table if not exists public.sus (
  responden_id  text primary key references public.responden(id) on delete cascade,
  jawaban       jsonb not null,
  skor          real not null
);

create table if not exists public.roadmap_centang (
  responden_id  text not null references public.responden(id) on delete cascade,
  skill_id      text not null,
  primary key (responden_id, skill_id)
);

alter table public.responden       enable row level security;
alter table public.umpan_balik     enable row level security;
alter table public.sus             enable row level security;
alter table public.roadmap_centang enable row level security;

-- Supabase memberi hak tabel ke peran anon dan authenticated secara bawaan.
-- RLS tanpa kebijakan sudah menolak mereka; hak ini dicabut juga supaya tidak
-- ada yang terbuka kalau suatu hari RLS dimatikan tanpa sengaja.
do $$
declare t text;
begin
  foreach t in array array['responden', 'umpan_balik', 'sus', 'roadmap_centang'] loop
    if exists (select 1 from pg_roles where rolname = 'anon') then
      execute format('revoke all on public.%I from anon', t);
    end if;
    if exists (select 1 from pg_roles where rolname = 'authenticated') then
      execute format('revoke all on public.%I from authenticated', t);
    end if;
  end loop;
end $$;

-- Penjaga
do $$
begin
  if (select count(*) from pg_tables where schemaname = 'public'
        and tablename in ('responden', 'umpan_balik', 'sus', 'roadmap_centang')
        and rowsecurity) <> 4 then
    raise exception '0001: RLS belum menyala di keempat tabel';
  end if;
  if exists (select 1 from pg_policies where schemaname = 'public'
               and tablename in ('responden', 'umpan_balik', 'sus', 'roadmap_centang')) then
    raise exception '0001: tabel responden tidak boleh punya kebijakan RLS; hanya API yang mengaksesnya';
  end if;
  raise notice '0001: tabel penyimpanan siap, terkunci untuk kunci publik';
end $$;

commit;
