/** Potongan tampilan profesi yang dipakai Explore dan layar detail. */
import { Building2, ChevronRight, CircleDollarSign, Laptop, PieChart, Signal } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { gaji, pita, type Ringkas } from '../api'

const NADA = {
  hijau: { kotak: 'border-emerald-200 bg-emerald-50', teks: 'text-emerald-700', chip: 'bg-emerald-50 text-emerald-700' },
  biru: { kotak: 'border-sky-200 bg-sky-50', teks: 'text-sky-700', chip: 'bg-sky-50 text-sky-700' },
  kuning: { kotak: 'border-amber-200 bg-amber-50', teks: 'text-amber-700', chip: 'bg-amber-50 text-amber-700' },
}

export function LencanaPita({ skor }: { skor: number }) {
  const p = pita(skor)
  const n = NADA[p.nada]
  return (
    <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-[12.5px] ${n.kotak}`}>
      <PieChart className={`size-3.5 ${n.teks}`} aria-hidden />
      <span className="font-semibold text-slate-900">{Math.round(skor * 100)}%</span>
      <span className={n.teks}>{p.label}</span>
    </span>
  )
}

/** Kartu profesi — satu-satunya bentuk kartu di Explore. */
export function KartuProfesi({ id, p, alasan, tampilDeskripsi = false }: {
  id: string; p: Ringkas; alasan?: string; tampilDeskripsi?: boolean
}) {
  const b = pita(p.skor)
  return (
    <Link
      to={`/explore/${id}/profesi/${p.profesi_id}`}
      className="group flex w-[260px] shrink-0 snap-start flex-col rounded-2xl border border-slate-200 bg-white transition-colors hover:border-slate-300 sm:w-[268px]"
    >
      <div className="flex flex-col gap-2.5 p-4">
        <div className="flex items-start justify-between gap-2">
          <span className="inline-flex max-w-full items-center gap-1 rounded-md bg-indigo-50 px-2 py-1 text-[11px] font-medium text-indigo-700">
            <Building2 className="size-3 shrink-0" aria-hidden />
            <span className="truncate">{p.sektor}</span>
          </span>
          <ChevronRight className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden />
        </div>
        <h3 className="text-[15px] font-semibold leading-snug text-slate-900">{p.nama}</h3>
        {tampilDeskripsi && <p className="line-clamp-3 text-[13px] leading-relaxed text-slate-500">{p.deskripsi}</p>}
        <dl className="mt-0.5 flex flex-col gap-1.5 text-[12.5px] text-slate-600">
          <div className="flex items-center gap-2">
            <CircleDollarSign className="size-3.5 shrink-0 text-slate-400" aria-hidden />
            <dd>{gaji(p.gaji_min, p.gaji_maks)}</dd>
          </div>
          <div className="flex items-center gap-2">
            <Signal className="size-3.5 shrink-0 text-slate-400" aria-hidden />
            <dd>{p.senioritas}</dd>
          </div>
          <div className="flex items-center gap-2">
            <Laptop className="size-3.5 shrink-0 text-slate-400" aria-hidden />
            <dd className="capitalize">{p.pola_kerja.join(' / ')}</dd>
          </div>
        </dl>
      </div>
      <div className="mt-auto border-t border-slate-100 px-4 py-3">
        <div className="flex items-center gap-2">
          <PieChart className="size-3.5 shrink-0 text-slate-500" aria-hidden />
          <span className="text-[12.5px] font-semibold text-slate-900">{Math.round(p.skor * 100)}%</span>
          <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${NADA[b.nada].chip}`}>{b.label}</span>
        </div>
        {alasan && <p className="mt-2 text-[12.5px] leading-relaxed text-slate-500">{alasan}</p>}
      </div>
    </Link>
  )
}

/** Satu baris kartu yang bisa digeser, dengan judul dan keterangan. */
export function BarisKartu({ judul, keterangan, children }: { judul: string; keterangan?: string; children: ReactNode }) {
  return (
    <section className="py-5">
      <div className="px-4 sm:px-6">
        <h2 className="text-[17px] font-bold tracking-tight text-slate-900">{judul}</h2>
        {keterangan && <p className="mt-0.5 text-[13px] leading-relaxed text-slate-500">{keterangan}</p>}
      </div>
      <div className="mt-4 flex snap-x snap-mandatory items-stretch gap-3 overflow-x-auto px-4 pb-2 sm:px-6 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {children}
        <div className="w-1 shrink-0" aria-hidden />
      </div>
    </section>
  )
}

/** Sakelar tab berbentuk pil. */
export function TabSwitch<T extends string>({ tabs, aktif, onPilih }: {
  tabs: readonly { kode: T; label: string }[]; aktif: T; onPilih: (kode: T) => void
}) {
  return (
    <div role="tablist" className="inline-flex max-w-full items-center gap-1 overflow-x-auto rounded-full bg-slate-100 p-1">
      {tabs.map((t) => {
        const on = t.kode === aktif
        return (
          <button
            key={t.kode} role="tab" type="button" aria-selected={on} onClick={() => onPilih(t.kode)}
            className={`shrink-0 whitespace-nowrap rounded-full px-3.5 py-2 text-[13px] transition-colors ${
              on ? 'bg-white font-semibold text-slate-900 shadow-sm' : 'font-medium text-slate-500 hover:text-slate-700'
            }`}
          >
            {t.label}
          </button>
        )
      })}
    </div>
  )
}

const R = 68
const PANJANG = Math.PI * R

/** Busur skor kecocokan: setengah lingkaran dengan angka besar di tengah. */
export function BusurSkor({ skor }: { skor: number | null }) {
  const nilai = skor == null ? 0 : Math.max(0, Math.min(100, Math.round(skor * 100)))
  const lintasan = `M ${92 - R} 92 A ${R} ${R} 0 0 1 ${92 + R} 92`
  return (
    <div className="relative mx-auto w-[184px]">
      <svg viewBox="0 0 184 100" className="w-full" role="img"
        aria-label={skor == null ? 'Skor kecocokan tidak tersedia' : `Skor kecocokan ${nilai} persen`}>
        <path d={lintasan} fill="none" stroke="#E5E7EB" strokeWidth={20} strokeLinecap="round" />
        {nilai > 0 && (
          <path d={lintasan} fill="none" stroke="#6D4AFF" strokeWidth={20} strokeLinecap="round"
            strokeDasharray={`${(nilai / 100) * PANJANG} ${PANJANG}`} />
        )}
      </svg>
      <div className="pointer-events-none absolute inset-x-0 bottom-1 flex items-baseline justify-center">
        {skor == null ? (
          <span className="text-[15px] font-semibold text-slate-400">Tidak dinilai</span>
        ) : (
          <>
            <span className="text-[34px] font-bold leading-none tracking-tight text-slate-900">{nilai}</span>
            <span className="text-[17px] font-semibold text-slate-900">%</span>
          </>
        )}
      </div>
    </div>
  )
}
