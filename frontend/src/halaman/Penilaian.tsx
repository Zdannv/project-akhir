/** Kuesioner System Usability Scale: 10 butir, skala 1 - 5. */
import { ArrowRight, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { ambilKuesioner, kirimSus } from '../api'
import { AppBottomNav, AppTopNav, KepalaLayar } from '../komponen/AppNav'
import { Galat, Memuat } from '../komponen/umum'
import { useData } from '../komponen/useData'

export default function Penilaian() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const { data, galat, muat } = useData(ambilKuesioner, 'kuesioner')
  const [jawaban, setJawaban] = useState<Record<number, number>>({})
  const [kirim, setKirim] = useState(false)
  const [gagal, setGagal] = useState<string | null>(null)
  const terisi = data ? data.sus.filter((_, i) => jawaban[i]).length : 0

  async function simpan() {
    if (!data) return
    setKirim(true)
    setGagal(null)
    try {
      await kirimSus(id, data.sus.map((_, i) => jawaban[i]))
      navigate(`/explore/${id}`)
    } catch (e) {
      setGagal((e as Error).message)
      setKirim(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <AppTopNav id={id} />
      <KepalaLayar ke={`/explore/${id}`} judul="Penilaian Sistem" subjudul="System Usability Scale" />
      {muat ? <Memuat /> : galat || !data ? (
        <div className="mx-auto w-full max-w-2xl flex-1 p-6"><Galat pesan={galat ?? 'Gagal memuat.'} /></div>
      ) : (
        <>
          <main className="mx-auto w-full max-w-2xl flex-1 px-4 pb-8 pt-6 sm:px-6">
            <h1 className="text-[17px] font-bold tracking-tight text-slate-900">Seberapa mudah sistem ini digunakan?</h1>
            <p className="mt-1 text-[13px] leading-relaxed text-slate-500">1 = sangat tidak setuju, 5 = sangat setuju.</p>
            <p className="mt-2 inline-flex rounded-md bg-violet-50 px-2 py-1 text-[11.5px] font-semibold text-violet-700">{terisi} dari {data.sus.length} terjawab</p>
            <ol className="mt-4 flex flex-col gap-2.5">
              {data.sus.map((teks, i) => (
                <li key={teks} className={`rounded-xl border px-4 py-3.5 transition-colors ${jawaban[i] ? 'border-violet-200 bg-violet-50/40' : 'border-slate-200 bg-white'}`}>
                  <p className="text-[13.5px] font-semibold leading-snug text-slate-900">{i + 1}. {teks}</p>
                  <div className="mt-3 flex items-center justify-between gap-1.5 sm:justify-center sm:gap-3" role="radiogroup" aria-label={teks}>
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button key={n} type="button" role="radio" aria-checked={jawaban[i] === n}
                        onClick={() => setJawaban((lama) => ({ ...lama, [i]: n }))}
                        className={`grid size-10 place-items-center rounded-full border text-[13.5px] font-semibold transition-colors ${jawaban[i] === n ? 'border-violet-600 bg-violet-600 text-white' : 'border-slate-300 bg-white text-slate-600 hover:border-violet-400'}`}>
                        {n}
                      </button>
                    ))}
                  </div>
                </li>
              ))}
            </ol>
            {gagal && <div className="mt-4"><Galat pesan={gagal} /></div>}
          </main>
          <div className="sticky bottom-[57px] z-20 border-t border-violet-100 bg-[#EDEBFA] px-4 py-3 sm:px-6 lg:bottom-0">
            <div className="mx-auto max-w-2xl">
              <button type="button" disabled={terisi < data.sus.length || kirim} onClick={simpan}
                className="flex w-full items-center justify-center gap-2 rounded-full bg-violet-600 px-6 py-3.5 text-[15px] font-semibold text-white transition-colors hover:bg-violet-700 disabled:cursor-not-allowed disabled:bg-violet-300">
                {kirim ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null} Simpan Penilaian {!kirim && <ArrowRight className="size-4" aria-hidden />}
              </button>
            </div>
          </div>
        </>
      )}
      <AppBottomNav id={id} />
    </div>
  )
}
