import { Loader2 } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'

export function Kerangka({ children, lebar = 'max-w-3xl' }: { children: ReactNode; lebar?: string }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className={`mx-auto flex ${lebar} items-center justify-between px-4 py-3`}>
          <Link to="/" className="text-[15px] font-semibold text-slate-900">
            Rekomendasi Profesi <span className="text-teal-700">TI</span>
          </Link>
          <span className="text-xs text-slate-500">Hybrid KBF + CBF</span>
        </div>
      </header>
      <main className={`mx-auto ${lebar} px-4 py-8`}>{children}</main>
    </div>
  )
}

export function Memuat() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center" aria-busy>
      <Loader2 className="size-6 animate-spin text-teal-700" aria-hidden />
    </div>
  )
}

export function Galat({ pesan }: { pesan: string }) {
  return <p className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">{pesan}</p>
}

/** Memuat data sekali per kunci; mengembalikan data, status muat, dan galat. */
export function useData<T>(ambil: () => Promise<T>, kunci: string) {
  const [keadaan, setKeadaan] = useState<{ kunci: string; data?: T; galat?: string }>({ kunci })
  useEffect(() => {
    let batal = false
    ambil()
      .then((data) => !batal && setKeadaan({ kunci, data }))
      .catch((e: Error) => !batal && setKeadaan({ kunci, galat: e.message }))
    return () => {
      batal = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kunci])
  const segar = keadaan.kunci === kunci
  return {
    data: segar ? keadaan.data : undefined,
    galat: segar ? keadaan.galat : undefined,
    muat: !segar || (!keadaan.data && !keadaan.galat),
    setData: (data: T) => setKeadaan({ kunci, data }),
  }
}

export function Batang({ nilai, warna = 'bg-teal-600' }: { nilai: number; warna?: string }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
      <div className={`h-full rounded-full ${warna}`} style={{ width: `${Math.max(0, Math.min(1, nilai)) * 100}%` }} />
    </div>
  )
}

export const tombolUtama =
  'inline-flex items-center justify-center gap-2 rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-teal-800 disabled:cursor-not-allowed disabled:bg-slate-300'
export const tombolSekunder =
  'inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50'
export const kartu = 'rounded-xl border border-slate-200 bg-white p-5'
