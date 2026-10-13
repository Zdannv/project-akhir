/**
 * Dasbor peneliti: metrik pengujian dari responden yang sudah terkumpul.
 *
 * Angkanya dihitung fungsi yang sama dengan scripts/evaluasi.py. Halaman ini
 * tidak ditautkan dari mana pun; dibuka langsung lewat /peneliti.
 */
import { Download, KeyRound, RefreshCw } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { ambilPeneliti, persen, unduhEkspor, type Peneliti as Data } from '../api'
import { Galat, Lambang, Memuat } from '../komponen/umum'
import { useData } from '../komponen/useData'

export default function Peneliti() {
  // Kunci hanya disimpan di memori halaman ini, tidak di penyimpanan peramban.
  const [kunci, setKunci] = useState('')
  const [ketik, setKetik] = useState('')
  const [putaran, setPutaran] = useState(0)
  const { data, galat, muat } = useData(() => ambilPeneliti(kunci), `peneliti/${kunci}/${putaran}`)
  const [gagalUnduh, setGagalUnduh] = useState<string | null>(null)

  async function unduh() {
    setGagalUnduh(null)
    try {
      const url = URL.createObjectURL(await unduhEkspor(kunci))
      const a = document.createElement('a')
      a.href = url
      a.download = 'responden.csv'
      a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      setGagalUnduh((e as Error).message)
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-slate-200">
        <div className="mx-auto flex h-16 max-w-5xl items-center gap-3 px-4 sm:px-6">
          <Lambang className="size-8 shrink-0" />
          <span className="leading-tight">
            <span className="block text-[13px] font-semibold text-slate-900">Dasbor Peneliti</span>
            <span className="block text-[11px] text-slate-400">Rekomendasi Profesi TI</span>
          </span>
          {data && (
            <div className="ml-auto flex gap-2">
              <button type="button" onClick={() => setPutaran((n) => n + 1)} className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-4 py-2 text-[12.5px] font-semibold text-slate-700 hover:bg-slate-200">
                <RefreshCw className="size-3.5" aria-hidden /> Muat ulang
              </button>
              <button type="button" onClick={unduh} disabled={data.n === 0} className="inline-flex items-center gap-1.5 rounded-full bg-violet-600 px-4 py-2 text-[12.5px] font-semibold text-white hover:bg-violet-700 disabled:bg-violet-300">
                <Download className="size-3.5" aria-hidden /> Unduh CSV
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        {muat ? <Memuat /> : galat || !data ? (
          <div className="mx-auto max-w-sm">
            <Galat pesan={galat ?? 'Gagal memuat.'} />
            <form className="mt-4 flex gap-2" onSubmit={(e) => { e.preventDefault(); setKunci(ketik) }}>
              <div className="relative flex-1">
                <KeyRound className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-slate-400" aria-hidden />
                <input type="password" value={ketik} onChange={(e) => setKetik(e.target.value)} placeholder="Kunci peneliti" aria-label="Kunci peneliti" autoComplete="off"
                  className="w-full rounded-full border border-slate-200 py-3 pl-11 pr-4 text-[13.5px] outline-none focus:border-violet-400" />
              </div>
              <button type="submit" className="rounded-full bg-violet-600 px-5 text-[13.5px] font-semibold text-white hover:bg-violet-700">Buka</button>
            </form>
          </div>
        ) : data.n === 0 ? (
          <p className="py-16 text-center text-[13.5px] text-slate-500">Belum ada responden. Data muncul di sini setelah kuesioner diisi.</p>
        ) : <Isi d={data} />}
        {gagalUnduh && <div className="mt-4"><Galat pesan={gagalUnduh} /></div>}
      </main>
    </div>
  )
}

const angka = (x: number, digit = 1) => x.toLocaleString('id-ID', { minimumFractionDigits: digit, maximumFractionDigits: digit })

function Isi({ d }: { d: Data }) {
  const hibrida = d.pakar?.['Hibrida bawaan (korelasi, α = 0,5)']
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kotak label="Responden" nilai={String(d.n)} ket={`${d.n_pakar ?? 0} profesional TI`} />
        <Kotak label="Hit Rate@5 (uji pakar)" nilai={hibrida ? persen(hibrida['hit@5']) : '–'} ket="target ≥ 60%" baik={hibrida ? hibrida['hit@5'] >= 0.6 : undefined} />
        <Kotak label="Precision@5" nilai={d.presisi?.['5'] ? persen(d.presisi['5'][0]) : '–'} ket={d.presisi?.['5'] ? `${d.presisi['5'][1]} responden menilai lengkap` : 'belum ada yang menilai 5 teratas'} />
        <Kotak label="Skor SUS" nilai={d.sus ? angka(d.sus[0]) : '–'} ket={d.sus ? `${d.sus[1]} responden · ambang 68` : 'belum ada'} baik={d.sus ? d.sus[0] >= 68 : undefined} />
      </div>

      {d.pakar && (
        <Bagian judul="Uji pakar: posisi profesi aktual di daftar rekomendasi" ket="Dihitung ulang dari jawaban mentah untuk tiap konfigurasi.">
          <Tabel kepala={['Konfigurasi', 'Hit@1', 'Hit@3', 'Hit@5', 'MRR']}
            baris={Object.entries(d.pakar).map(([nama, m]) => [nama, persen(m['hit@1']), persen(m['hit@3']), persen(m['hit@5']), angka(m.mrr, 3)])} />
        </Bagian>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {d.presisi && (
          <Bagian judul="Precision@K" ket="Dari penilaian relevan / tidak relevan oleh responden.">
            <Tabel kepala={['K', 'Precision', 'n']} baris={Object.entries(d.presisi).map(([k, v]) => [k, v ? persen(v[0]) : '–', v ? String(v[1]) : '0'])} />
          </Bagian>
        )}
        {d.reliabilitas && (
          <Bagian judul="Reliabilitas kuesioner (Cronbach's α)" ket="Big Five hanya dua butir per dimensi, jadi α rendah di sana lazim.">
            <Tabel kepala={['Skala', 'α']} baris={Object.entries(d.reliabilitas).map(([k, v]) => [k, v === null ? '–' : angka(v, 2)])} />
          </Bagian>
        )}
      </div>

      <Bagian judul="Skill di luar pilihan" ket={`Rata-rata ${angka(d.n_skill ?? 0)} skill dipilih per responden. Di bawah ini skill yang diketik sendiri — bahan perluasan basis pengetahuan.`}>
        {d.skill_lain && d.skill_lain.length > 0 ? (
          <ul className="flex flex-wrap gap-2">
            {d.skill_lain.map(([s, n]) => <li key={s} className="rounded-full bg-slate-100 px-3 py-1.5 text-[12.5px] font-medium text-slate-700">{s} <span className="text-slate-400">× {n}</span></li>)}
          </ul>
        ) : <p className="text-[13px] text-slate-400">Belum ada.</p>}
      </Bagian>

      <Bagian judul="Responden" ket="Satu baris per orang; isian yang sudah diperbarui hanya dihitung versi terakhirnya.">
        <Tabel kepala={['Waktu', 'Nama', 'Jenis', 'Kode', 'Rekomendasi #1', 'Profesi aktual', 'Posisi', 'Dinilai', 'SUS']}
          baris={(d.responden ?? []).map((r) => [
            new Date(r.dibuat).toLocaleString('id-ID', { dateStyle: 'short', timeStyle: 'short' }), r.nama, r.jenis, r.kode_holland,
            r.teratas ?? '–', r.profesi_aktual ?? '–', r.posisi_aktual === null ? '–' : `#${r.posisi_aktual}`, `${r.n_dinilai}/5`,
            r.skor_sus === null ? '–' : angka(r.skor_sus),
          ])} />
      </Bagian>
    </div>
  )
}

function Kotak({ label, nilai, ket, baik }: { label: string; nilai: string; ket: string; baik?: boolean }) {
  return (
    <div className="rounded-2xl border border-slate-200 p-4">
      <p className="text-[12px] text-slate-500">{label}</p>
      <p className={`mt-1 text-[26px] font-bold leading-none tracking-tight ${baik === undefined ? 'text-slate-900' : baik ? 'text-emerald-600' : 'text-amber-600'}`}>{nilai}</p>
      <p className="mt-1.5 text-[11.5px] text-slate-400">{ket}</p>
    </div>
  )
}

function Bagian({ judul, ket, children }: { judul: string; ket?: string; children: ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-200 p-4">
      <h2 className="text-[15px] font-semibold text-slate-900">{judul}</h2>
      {ket && <p className="mt-0.5 text-[12.5px] leading-relaxed text-slate-500">{ket}</p>}
      <div className="mt-3">{children}</div>
    </section>
  )
}

function Tabel({ kepala, baris }: { kepala: string[]; baris: string[][] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-[13px]">
        <thead className="text-[11.5px] text-slate-500">
          <tr>{kepala.map((k, i) => <th key={k} className={`whitespace-nowrap py-1.5 pr-4 font-medium ${i > 0 && kepala.length <= 5 ? 'text-right' : ''}`}>{k}</th>)}</tr>
        </thead>
        <tbody>
          {baris.map((b, n) => (
            <tr key={n} className="border-t border-slate-100">
              {b.map((sel, i) => <td key={i} className={`whitespace-nowrap py-2 pr-4 ${i === 0 ? 'text-slate-900' : 'text-slate-700'} ${i > 0 && kepala.length <= 5 ? 'text-right tabular-nums' : ''}`}>{sel}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
