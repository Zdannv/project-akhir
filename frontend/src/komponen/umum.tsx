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

/** Lambang "N" yang sama dengan Navika. */
export function Lambang({ className = 'size-7' }: { className?: string }) {
  return (
    <svg viewBox="0 0 15 20" className={className} role="img" aria-label="Logo">
      <g fill="currentColor">
        <path d="M2 0 L5 0 L3 19.5 L0 19.5 Z" />
        <path d="M2.5 0 L5.5 0 L14 19.5 L11 19.5 Z" />
        <path d="M12 5.5 L15 5.5 L13.5 19.5 L10.5 19.5 Z" />
      </g>
    </svg>
  )
}
