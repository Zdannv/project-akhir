/**
 * Pencarian profesi dengan filter.
 *
 * Kotak cari di Explore cukup untuk "saya tahu nama profesinya"; menjelajah
 * dengan filter sektor, pola kerja, dan gaji butuh satu layar sendiri. Semua
 * penyaringan dikerjakan di peramban: datanya hanya 35 profesi dan sudah
 * terbawa bersama hasil rekomendasi.
 */
import { Building2, CircleDollarSign, Laptop, PieChart, Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ambilHasil, gaji, pita, type Hasil, type Ringkas } from '../api'
import { AppBottomNav, AppTopNav, KepalaLayar } from '../komponen/AppNav'
import { Galat, Memuat } from '../komponen/umum'
import { useData } from '../komponen/useData'

const URUT = [
  { kode: 'skor', label: 'Paling cocok' },
  { kode: 'gaji', label: 'Gaji tertinggi' },
  { kode: 'nama', label: 'Nama A–Z' },
] as const
type Urut = (typeof URUT)[number]['kode']

const GAJI_MIN = [0, 5, 8, 10, 15]

export default function Cari() {
  const { id = '' } = useParams()
  const { data, galat, muat } = useData(() => ambilHasil(id), id)
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <AppTopNav id={id} />
      <KepalaLayar ke={`/explore/${id}`} judul="Cari Profesi" subjudul="35 profesi bidang TI" />
      {muat ? <Memuat /> : galat || !data ? (
        <div className="mx-auto w-full max-w-3xl flex-1 p-6"><Galat pesan={galat ?? 'Gagal memuat.'} /></div>
      ) : <Isi id={id} d={data} />}
      <AppBottomNav id={id} />
    </div>
  )
}

function Isi({ id, d }: { id: string; d: Hasil }) {
  const semua = d.hasil.peringkat_lengkap
  const [q, setQ] = useState('')
  const [sektor, setSektor] = useState<string[]>([])
  const [pola, setPola] = useState<string[]>([])
  const [gajiMin, setGajiMin] = useState(0)
  const [urut, setUrut] = useState<Urut>('skor')

  const daftarSektor = useMemo(() => [...new Set(semua.map((p) => p.sektor))].sort(), [semua])
  const daftarPola = useMemo(() => [...new Set(semua.flatMap((p) => p.pola_kerja))].sort(), [semua])

  const hasil = useMemo(() => {
    const kata = q.trim().toLowerCase()
    const lolos = semua.filter((p) =>
      (!kata || p.nama.toLowerCase().includes(kata) || p.deskripsi.toLowerCase().includes(kata)) &&
      (sektor.length === 0 || sektor.includes(p.sektor)) &&
      (pola.length === 0 || p.pola_kerja.some((x) => pola.includes(x))) &&
      // Gaji minimum dibandingkan dengan batas ATAS rentang: profesinya masih bisa mencapai angka itu.
      p.gaji_maks >= gajiMin * 1_000_000)
    const banding: Record<Urut, (a: Ringkas, b: Ringkas) => number> = {
      skor: (a, b) => a.peringkat - b.peringkat,
      gaji: (a, b) => b.gaji_maks - a.gaji_maks,
      nama: (a, b) => a.nama.localeCompare(b.nama),
    }
    return [...lolos].sort(banding[urut])
  }, [semua, q, sektor, pola, gajiMin, urut])

  const adaFilter = q.trim() !== '' || sektor.length > 0 || pola.length > 0 || gajiMin > 0
  const alih = (daftar: string[], v: string) => (daftar.includes(v) ? daftar.filter((x) => x !== v) : [...daftar, v])

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 pb-12 pt-5 sm:px-6">
      <div className="relative">
        <label htmlFor="cari" className="sr-only">Cari profesi</label>
        <Search className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden />
        <input id="cari" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Cari nama atau deskripsi profesi.."
          className="w-full rounded-full border border-slate-200 bg-white py-3 pl-11 pr-4 text-[13.5px] text-slate-900 outline-none placeholder:text-slate-400 focus:border-violet-400" />
      </div>

      <Kelompok judul="Sektor">
        {daftarSektor.map((s) => <Chip key={s} on={sektor.includes(s)} onClick={() => setSektor(alih(sektor, s))}>{s}</Chip>)}
      </Kelompok>
      <Kelompok judul="Pola kerja">
        {daftarPola.map((s) => <Chip key={s} on={pola.includes(s)} onClick={() => setPola(alih(pola, s))}><span className="capitalize">{s}</span></Chip>)}
      </Kelompok>
      <Kelompok judul="Gaji bisa mencapai">
        {GAJI_MIN.map((g) => <Chip key={g} on={gajiMin === g} onClick={() => setGajiMin(g)}>{g === 0 ? 'Semua' : `≥ Rp ${g} juta`}</Chip>)}
      </Kelompok>

      <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-4">
        <p className="text-[13px] text-slate-600">
          <strong className="font-semibold text-slate-900">{hasil.length}</strong> profesi
          {adaFilter && (
            <button type="button" onClick={() => { setQ(''); setSektor([]); setPola([]); setGajiMin(0) }} className="ml-3 inline-flex items-center gap-1 text-[12.5px] font-semibold text-violet-700 hover:text-violet-800">
              <X className="size-3.5" aria-hidden /> Hapus filter
            </button>
          )}
        </p>
        <label className="flex items-center gap-2 text-[12.5px] text-slate-500">
          Urutkan
          <select value={urut} onChange={(e) => setUrut(e.target.value as Urut)} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[12.5px] font-semibold text-slate-900 outline-none focus:border-violet-400">
            {URUT.map((u) => <option key={u.kode} value={u.kode}>{u.label}</option>)}
          </select>
        </label>
      </div>

      {hasil.length === 0 ? (
        <p className="mt-8 text-center text-[13.5px] text-slate-500">Tidak ada profesi yang cocok dengan filter ini.</p>
      ) : (
        <ul className="mt-4 grid gap-3 sm:grid-cols-2">
          {hasil.map((p) => {
            const b = pita(p.skor)
            const warna = { hijau: 'bg-emerald-50 text-emerald-700', biru: 'bg-sky-50 text-sky-700', kuning: 'bg-amber-50 text-amber-700', abu: 'bg-slate-100 text-slate-600' }[b.nada]
            return (
              <li key={p.profesi_id}>
                <Link to={`/explore/${id}/profesi/${p.profesi_id}`} className="flex h-full flex-col gap-2 rounded-2xl border border-slate-200 bg-white p-4 transition-colors hover:border-slate-300">
                  <span className="inline-flex w-fit max-w-full items-center gap-1 rounded-md bg-indigo-50 px-2 py-1 text-[11px] font-medium text-indigo-700">
                    <Building2 className="size-3 shrink-0" aria-hidden /> <span className="truncate">{p.sektor}</span>
                  </span>
                  <h2 className="text-[15px] font-semibold leading-snug text-slate-900">{p.nama}</h2>
                  <dl className="flex flex-col gap-1.5 text-[12.5px] text-slate-600">
                    <div className="flex items-center gap-2"><CircleDollarSign className="size-3.5 shrink-0 text-slate-400" aria-hidden /><dd>{gaji(p.gaji_min, p.gaji_maks)}</dd></div>
                    <div className="flex items-center gap-2"><Laptop className="size-3.5 shrink-0 text-slate-400" aria-hidden /><dd className="capitalize">{p.pola_kerja.join(' / ')}</dd></div>
                  </dl>
                  <div className="mt-auto flex items-center gap-2 border-t border-slate-100 pt-3">
                    <PieChart className="size-3.5 shrink-0 text-slate-500" aria-hidden />
                    <span className="text-[12.5px] font-semibold text-slate-900">{Math.round(p.skor * 100)}%</span>
                    <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${warna}`}>{b.label}</span>
                    <span className="ml-auto text-[11.5px] text-slate-400">#{p.peringkat}</span>
                  </div>
                </Link>
              </li>
            )
          })}
        </ul>
      )}

      {d.hasil.tersaring.length > 0 && (
        <p className="mt-6 text-[12px] leading-relaxed text-slate-400">
          {d.hasil.tersaring.length} profesi tidak ditampilkan karena syarat mutlaknya tidak terpenuhi; daftarnya ada di bagian bawah Explore.
        </p>
      )}
    </main>
  )
}

function Kelompok({ judul, children }: { judul: string; children: React.ReactNode }) {
  return (
    <fieldset className="mt-5">
      <legend className="text-[12px] font-bold uppercase tracking-wide text-slate-500">{judul}</legend>
      <div className="mt-2.5 flex flex-wrap gap-2">{children}</div>
    </fieldset>
  )
}

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button type="button" aria-pressed={on} onClick={onClick}
      className={`rounded-full px-3.5 py-2 text-[13px] font-medium shadow-sm ring-1 transition-colors ${on ? 'bg-[#F1EBFF] text-[#7033FF] ring-[#DDD0FF]' : 'bg-white text-slate-900 ring-slate-200 hover:bg-slate-50'}`}>
      {children}
    </button>
  )
}
