import { ArrowLeft, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ambilKuesioner, kirimSus } from '../api'
import { Galat, Kerangka, Memuat, kartu, tombolUtama, useData } from '../komponen/umum'

/** Kuesioner System Usability Scale: 10 butir, skala 1 - 5. */
export default function Penilaian() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const { data, galat, muat } = useData(ambilKuesioner, 'kuesioner')
  const [jawaban, setJawaban] = useState<Record<number, number>>({})
  const [kirim, setKirim] = useState(false)
  const [gagal, setGagal] = useState<string | null>(null)

  if (muat) return <Kerangka><Memuat /></Kerangka>
  if (galat || !data) return <Kerangka><Galat pesan={galat ?? 'Gagal memuat.'} /></Kerangka>
  const lengkap = data.sus.every((_, i) => jawaban[i])

  async function simpan() {
    setKirim(true)
    setGagal(null)
    try {
      await kirimSus(id, data!.sus.map((_, i) => jawaban[i]))
      navigate(`/hasil/${id}`)
    } catch (e) {
      setGagal((e as Error).message)
      setKirim(false)
    }
  }

  return (
    <Kerangka>
      <Link to={`/hasil/${id}`} className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900">
        <ArrowLeft className="size-4" aria-hidden /> Kembali ke hasil
      </Link>
      <h1 className="mt-4 text-xl font-bold text-slate-900">Penilaian kemudahan penggunaan</h1>
      <p className="mt-1 text-sm text-slate-600">1 = sangat tidak setuju, 5 = sangat setuju.</p>

      <ol className="mt-5 space-y-3">
        {data.sus.map((teks, i) => (
          <li key={teks} className={kartu}>
            <p className="text-sm text-slate-800">{i + 1}. {teks}</p>
            <div className="mt-3 grid grid-cols-5 gap-2" role="radiogroup" aria-label={teks}>
              {[1, 2, 3, 4, 5].map((n) => (
                <button key={n} type="button" role="radio" aria-checked={jawaban[i] === n}
                  onClick={() => setJawaban({ ...jawaban, [i]: n })}
                  className={`rounded-lg border py-2 text-sm font-semibold ${jawaban[i] === n ? 'border-teal-600 bg-teal-600 text-white' : 'border-slate-300 bg-white text-slate-600 hover:border-teal-500'}`}>
                  {n}
                </button>
              ))}
            </div>
          </li>
        ))}
      </ol>

      {gagal && <div className="mt-4"><Galat pesan={gagal} /></div>}
      <button type="button" className={`${tombolUtama} mt-6`} disabled={!lengkap || kirim} onClick={simpan}>
        {kirim && <Loader2 className="size-4 animate-spin" aria-hidden />} Simpan penilaian
      </button>
    </Kerangka>
  )
}
