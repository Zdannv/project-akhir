import { Loader2 } from 'lucide-react'

export function Memuat() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center" aria-busy>
      <Loader2 className="size-7 animate-spin text-violet-600" aria-hidden />
    </div>
  )
}

export function Galat({ pesan }: { pesan: string }) {
  return <p className="rounded-xl bg-rose-50 px-4 py-3 text-[13px] text-rose-700">{pesan}</p>
}

export function Batang({ nilai, warna = 'bg-violet-600', alas = 'bg-violet-100' }: { nilai: number; warna?: string; alas?: string }) {
  return (
    <div className={`h-2 w-full overflow-hidden rounded-full ${alas}`}>
      <div className={`h-full rounded-full ${warna}`} style={{ width: `${Math.max(0, Math.min(1, nilai)) * 100}%` }} />
    </div>
  )
}

/** Lambang aplikasi: lintasan menanjak menuju satu titik tujuan. */
export function Lambang({ className = 'size-8' }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} role="img" aria-label="Rekomendasi Profesi TI">
      <rect width="32" height="32" rx="8" fill="#7c3aed" />
      <path d="M9 21.5 14 14l4 4 5-8.5" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="23" cy="9.5" r="2.4" fill="#fff" />
    </svg>
  )
}

/** Avatar dari inisial nama; tanpa login tidak ada foto yang bisa diunggah. */
export function Avatar({ nama, className = 'size-10 text-[14px]' }: { nama: string; className?: string }) {
  const inisial = nama.trim().split(/\s+/).slice(0, 2).map((k) => k[0]?.toUpperCase() ?? '').join('') || '?'
  return (
    <span className={`grid shrink-0 place-items-center rounded-full bg-violet-600 font-bold text-white ${className}`} aria-hidden>
      {inisial}
    </span>
  )
}

/**
 * Diagram radar untuk membandingkan dua profil pada sumbu yang sama.
 * Nilai 0 - 1; `banding` opsional (mis. profil profesi).
 */
export function Radar({ sumbu, kamu, banding, labelBanding = 'Profesi' }: {
  sumbu: { kode: string; nama: string }[]
  kamu: Record<string, number>
  banding?: Record<string, number>
  labelBanding?: string
}) {
  const n = sumbu.length
  const R = 78
  const titik = (i: number, r: number) => {
    const sudut = (Math.PI * 2 * i) / n - Math.PI / 2
    return [130 + r * Math.cos(sudut), 112 + r * Math.sin(sudut)] as const
  }
  const bidang = (nilai: Record<string, number>) =>
    sumbu.map((s, i) => titik(i, R * Math.max(0.04, Math.min(1, nilai[s.kode] ?? 0))).join(',')).join(' ')
  return (
    <figure className="mx-auto w-full max-w-[340px]">
      <svg viewBox="0 0 260 224" className="w-full" role="img"
        aria-label={`Diagram radar: ${sumbu.map((s) => `${s.nama} ${Math.round((kamu[s.kode] ?? 0) * 100)}%`).join(', ')}`}>
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <polygon key={f} points={sumbu.map((_, i) => titik(i, R * f).join(',')).join(' ')} fill="none" stroke="#E2E8F0" strokeWidth={1} />
        ))}
        {sumbu.map((s, i) => {
          const [x, y] = titik(i, R)
          const [lx, ly] = titik(i, R + 16)
          return (
            <g key={s.kode}>
              <line x1={130} y1={112} x2={x} y2={y} stroke="#E2E8F0" strokeWidth={1} />
              <text x={lx} y={ly} textAnchor="middle" dominantBaseline="middle" className="fill-slate-500 text-[10px] font-semibold">{s.kode}</text>
            </g>
          )
        })}
        {banding && <polygon points={bidang(banding)} fill="#94A3B833" stroke="#94A3B8" strokeWidth={1.5} strokeDasharray="4 3" />}
        <polygon points={bidang(kamu)} fill="#7C3AED33" stroke="#7C3AED" strokeWidth={2} />
      </svg>
      <figcaption className="flex justify-center gap-4 text-[11.5px] text-slate-500">
        <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-violet-600" /> Kamu</span>
        {banding && <span className="flex items-center gap-1.5"><span className="size-2.5 rounded-full bg-slate-400" /> {labelBanding}</span>}
      </figcaption>
    </figure>
  )
}
