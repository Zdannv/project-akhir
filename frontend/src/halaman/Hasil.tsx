import { ChevronRight, ThumbsDown, ThumbsUp } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { ambilHasil, kirimUmpanBalik, NAMA_RIASEC, persen, rupiah, type Rekomendasi } from '../api'
import { Batang, Galat, Kerangka, Memuat, kartu, tombolSekunder, useData } from '../komponen/umum'

export default function HalamanHasil() {
  const { id = '' } = useParams()
  const { data, galat, muat, setData } = useData(() => ambilHasil(id), id)
  if (muat) return <Kerangka><Memuat /></Kerangka>
  if (galat || !data) return <Kerangka><Galat pesan={galat ?? 'Hasil tidak ditemukan.'} /></Kerangka>

  const h = data.hasil

  // Penilaian relevansi disimpan satu per satu; tampilan diperbarui lebih dulu
  // dan dikembalikan kalau penyimpanannya gagal.
  async function nilai(pid: string, relevan: boolean) {
    const lama = data!
    setData({ ...lama, umpan_balik: { ...lama.umpan_balik, [pid]: relevan } })
    try {
      await kirimUmpanBalik(id, { [pid]: relevan })
    } catch {
      setData(lama)
    }
  }

  return (
    <Kerangka>
      <p className="text-sm text-slate-500">Hasil untuk {data.nama}</p>
      <h1 className="mt-1 text-2xl font-bold text-slate-900">Lima profesi TI yang paling cocok</h1>
      <p className="mt-2 text-sm leading-relaxed text-slate-600">
        Kode minatmu <strong className="text-slate-900">{h.kode_holland}</strong>{' '}
        ({[...h.kode_holland].map((c) => NAMA_RIASEC[c]).join(' · ')}).{' '}
        {h.n_lolos} dari {h.n_lolos + h.n_tersaring} profesi lolos penyaringan syarat, lalu diurutkan dengan
        skor akhir = {h.konfigurasi.alpha} × KBF + {(1 - h.konfigurasi.alpha).toFixed(1)} × CBF.
      </p>

      {h.rekomendasi.length === 0 && (
        <div className="mt-6"><Galat pesan="Tidak ada profesi yang lolos penyaringan dengan syarat yang kamu isi." /></div>
      )}

      <ol className="mt-6 space-y-4">
        {h.rekomendasi.map((r) => (
          <KartuProfesi key={r.profesi_id} id={id} r={r} relevan={data.umpan_balik[r.profesi_id]} nilai={nilai} />
        ))}
      </ol>

      {h.tersaring.length > 0 && (
        <details className={`${kartu} mt-6`}>
          <summary className="cursor-pointer text-sm font-semibold text-slate-800">
            {h.tersaring.length} profesi tidak diikutkan karena syaratnya tidak terpenuhi
          </summary>
          <ul className="mt-3 space-y-2 text-sm">
            {h.tersaring.map((t) => (
              <li key={t.profesi_id}>
                <span className="font-medium text-slate-800">{t.nama}</span>
                <span className="text-slate-600"> — {t.alasan.map((a) => a.pesan).join(' ')}</span>
              </li>
            ))}
          </ul>
        </details>
      )}

      <details className={`${kartu} mt-4`}>
        <summary className="cursor-pointer text-sm font-semibold text-slate-800">Peringkat lengkap {h.n_lolos} profesi</summary>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs text-slate-500">
              <tr><th className="py-1 pr-3">#</th><th className="pr-3">Profesi</th><th className="pr-3 text-right">KBF</th><th className="pr-3 text-right">CBF</th><th className="text-right">Akhir</th></tr>
            </thead>
            <tbody>
              {h.peringkat_lengkap.map((b) => (
                <tr key={b.profesi_id} className="border-t border-slate-100">
                  <td className="py-1.5 pr-3 text-slate-500">{b.peringkat}</td>
                  <td className="pr-3"><Link className="text-teal-800 hover:underline" to={`/hasil/${id}/profesi/${b.profesi_id}`}>{b.nama}</Link></td>
                  <td className="pr-3 text-right tabular-nums">{b.skor_kbf.toFixed(3)}</td>
                  <td className="pr-3 text-right tabular-nums">{b.skor_cbf.toFixed(3)}</td>
                  <td className="text-right font-semibold tabular-nums">{b.skor.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      <div className={`${kartu} mt-6 flex flex-wrap items-center justify-between gap-3`}>
        <p className="text-sm text-slate-700">
          {data.skor_sus === null
            ? 'Bantu penelitian ini dengan menilai kemudahan penggunaan sistem (10 pertanyaan singkat).'
            : `Terima kasih, penilaianmu sudah tersimpan (skor SUS ${data.skor_sus}).`}
        </p>
        <Link to={`/hasil/${id}/penilaian`} className={tombolSekunder}>
          {data.skor_sus === null ? 'Isi penilaian' : 'Ubah penilaian'}
        </Link>
      </div>
    </Kerangka>
  )
}

function KartuProfesi({ id, r, relevan, nilai }: {
  id: string; r: Rekomendasi; relevan: boolean | undefined; nilai: (pid: string, relevan: boolean) => void
}) {
  const g = r.kesenjangan
  return (
    <li className={kartu}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold text-teal-700">#{r.peringkat} · {r.sektor}</p>
          <h2 className="mt-0.5 text-lg font-semibold text-slate-900">{r.nama}</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            {rupiah(r.gaji_min)} – {rupiah(r.gaji_maks)} · {r.pola_kerja.join(' / ')} · tipe {r.kode_holland}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-2xl font-bold tabular-nums text-slate-900">{persen(r.skor)}</p>
          <p className="text-xs text-slate-500">skor akhir</p>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <div className="mb-1 flex justify-between text-xs text-slate-600"><span>Kecocokan profil (KBF)</span><span className="tabular-nums">{persen(r.kbf.skor)}</span></div>
          <Batang nilai={r.kbf.skor} />
        </div>
        <div>
          <div className="mb-1 flex justify-between text-xs text-slate-600"><span>Kemiripan skill (CBF)</span><span className="tabular-nums">{persen(r.cbf.skor)}</span></div>
          <Batang nilai={r.cbf.skor} warna="bg-indigo-500" />
        </div>
      </div>

      <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-slate-700">
        {r.alasan.map((a) => <li key={a}>{a}</li>)}
      </ul>
      <p className="mt-3 text-sm text-slate-600">
        Skill wajib terpenuhi: <strong className="text-slate-900">{g.wajib_terpenuhi} dari {g.wajib_total}</strong>
        {g.belum.length > 0 && <> · perlu dikejar: {g.belum.slice(0, 3).map((s) => s.nama).join(', ')}{g.belum.length > 3 && ', …'}</>}
      </p>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>Menurutmu relevan?</span>
          <button type="button" aria-pressed={relevan === true} aria-label="Relevan" onClick={() => nilai(r.profesi_id, true)}
            className={`rounded-lg border p-2 ${relevan === true ? 'border-teal-600 bg-teal-600 text-white' : 'border-slate-300 text-slate-600 hover:bg-slate-50'}`}>
            <ThumbsUp className="size-4" aria-hidden />
          </button>
          <button type="button" aria-pressed={relevan === false} aria-label="Tidak relevan" onClick={() => nilai(r.profesi_id, false)}
            className={`rounded-lg border p-2 ${relevan === false ? 'border-rose-600 bg-rose-600 text-white' : 'border-slate-300 text-slate-600 hover:bg-slate-50'}`}>
            <ThumbsDown className="size-4" aria-hidden />
          </button>
        </div>
        <Link to={`/hasil/${id}/profesi/${r.profesi_id}`} className="inline-flex items-center gap-1 text-sm font-semibold text-teal-800 hover:underline">
          Lihat detail <ChevronRight className="size-4" aria-hidden />
        </Link>
      </div>
    </li>
  )
}

