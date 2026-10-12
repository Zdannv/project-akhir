import { ArrowLeft, ArrowRight, Loader2, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ambilKuesioner, kirimMasukan, type Butir, type Kuesioner, type Masukan } from '../api'
import { Galat, Kerangka, Memuat, kartu, tombolSekunder, tombolUtama, useData } from '../komponen/umum'

const LANGKAH = ['Data diri', 'Minat', 'Kepribadian', 'Skill']

const AWAL: Masukan = {
  nama: '', jenis_responden: 'mahasiswa', profesi_aktual: null,
  jenjang: '', prodi_id: null, domisili: '', bersedia_relokasi: true,
  ekspektasi_gaji: 0, punya_tanggungan: false,
  riasec: {}, big5: {}, skill: {},
}

export default function HalamanKuesioner() {
  const { data, galat, muat } = useData(ambilKuesioner, 'kuesioner')
  if (muat) return <Kerangka><Memuat /></Kerangka>
  if (galat || !data) return <Kerangka><Galat pesan={galat ?? 'Gagal memuat kuesioner.'} /></Kerangka>
  return <Kerangka><Formulir k={data} /></Kerangka>
}

function Formulir({ k }: { k: Kuesioner }) {
  const navigate = useNavigate()
  const [langkah, setLangkah] = useState(0)
  const [m, setM] = useState<Masukan>(AWAL)
  const [kirim, setKirim] = useState(false)
  const [galat, setGalat] = useState<string | null>(null)
  const ubah = (bagian: Partial<Masukan>) => setM((lama) => ({ ...lama, ...bagian }))

  const lengkap = [
    m.nama.trim() !== '' && m.jenjang !== '' && m.domisili !== '' &&
      (m.jenis_responden === 'mahasiswa' || m.profesi_aktual !== null),
    k.riasec.butir.every((b) => m.riasec[b.kode]),
    k.big5.butir.every((b) => m.big5[b.kode]),
    true, // skill boleh kosong: mesin tetap jalan dengan KBF saja
  ][langkah]

  // Satu ketukan menaikkan tingkat: belum -> dasar -> menengah -> mahir -> belum.
  function ketukSkill(id: string) {
    setM((lama) => {
      const skill = { ...lama.skill }
      const berikut = ((skill[id] ?? 0) + 1) % 4
      if (berikut === 0) delete skill[id]
      else skill[id] = berikut
      return { ...lama, skill }
    })
  }

  function pindah(ke: number) {
    setLangkah(ke)
    window.scrollTo({ top: 0 })
  }

  async function selesai() {
    setKirim(true)
    setGalat(null)
    try {
      const { id } = await kirimMasukan({ ...m, nama: m.nama.trim() })
      navigate(`/hasil/${id}`)
    } catch (e) {
      setGalat((e as Error).message)
      setKirim(false)
    }
  }

  return (
    <>
      <ol className="mb-6 flex gap-2" aria-label="Langkah pengisian">
        {LANGKAH.map((nama, i) => (
          <li key={nama} className="flex-1">
            <div className={`h-1.5 rounded-full ${i <= langkah ? 'bg-teal-600' : 'bg-slate-200'}`} />
            <p className={`mt-1.5 text-xs ${i === langkah ? 'font-semibold text-slate-900' : 'text-slate-500'}`}>
              {i + 1}. {nama}
            </p>
          </li>
        ))}
      </ol>

      {langkah === 0 && <DataDiri k={k} m={m} ubah={ubah} />}
      {langkah === 1 && (
        <Likert
          judul="Seberapa suka kamu melakukan kegiatan berikut?"
          keterangan="Bayangkan kegiatannya, bukan apakah kamu sudah bisa melakukannya."
          butir={k.riasec.butir} skala={k.riasec.skala}
          jawaban={m.riasec} pilih={(kode, n) => setM((lama) => ({ ...lama, riasec: { ...lama.riasec, [kode]: n } }))}
        />
      )}
      {langkah === 2 && (
        <Likert
          judul={k.big5.awalan}
          keterangan="Tidak ada jawaban benar atau salah. Jawab sesuai dirimu sehari-hari."
          butir={k.big5.butir} skala={k.big5.skala}
          jawaban={m.big5} pilih={(kode, n) => setM((lama) => ({ ...lama, big5: { ...lama.big5, [kode]: n } }))}
        />
      )}
      {langkah === 3 && <PilihSkill k={k} skill={m.skill} ketuk={ketukSkill} />}

      {galat && <div className="mt-4"><Galat pesan={galat} /></div>}

      <div className="mt-6 flex justify-between">
        <button type="button" className={tombolSekunder} disabled={langkah === 0 || kirim} onClick={() => pindah(langkah - 1)}>
          <ArrowLeft className="size-4" aria-hidden /> Kembali
        </button>
        {langkah < LANGKAH.length - 1 ? (
          <button type="button" className={tombolUtama} disabled={!lengkap} onClick={() => pindah(langkah + 1)}>
            Lanjut <ArrowRight className="size-4" aria-hidden />
          </button>
        ) : (
          <button type="button" className={tombolUtama} disabled={kirim} onClick={selesai}>
            {kirim && <Loader2 className="size-4 animate-spin" aria-hidden />} Lihat rekomendasi
          </button>
        )}
      </div>
    </>
  )
}

const kolom = 'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-teal-600 focus:outline-none'
const label = 'block text-sm font-medium text-slate-800'

function DataDiri({ k, m, ubah }: { k: Kuesioner; m: Masukan; ubah: (b: Partial<Masukan>) => void }) {
  return (
    <div className={`${kartu} space-y-5`}>
      <label className={label}>
        Nama
        <input className={kolom} value={m.nama} maxLength={80} onChange={(e) => ubah({ nama: e.target.value })} />
      </label>

      <fieldset>
        <legend className={label}>Saya mengisi sebagai</legend>
        <div className="mt-2 flex gap-2">
          {(['mahasiswa', 'profesional'] as const).map((j) => (
            <button
              key={j} type="button" aria-pressed={m.jenis_responden === j}
              onClick={() => ubah({ jenis_responden: j, profesi_aktual: j === 'mahasiswa' ? null : m.profesi_aktual })}
              className={`rounded-lg border px-3 py-2 text-sm ${m.jenis_responden === j ? 'border-teal-600 bg-teal-50 font-semibold text-teal-800' : 'border-slate-300 bg-white text-slate-700'}`}
            >
              {j === 'mahasiswa' ? 'Mahasiswa / pencari kerja' : 'Profesional TI'}
            </button>
          ))}
        </div>
      </fieldset>

      {m.jenis_responden === 'profesional' && (
        <label className={label}>
          Profesi saat ini
          <select className={kolom} value={m.profesi_aktual ?? ''} onChange={(e) => ubah({ profesi_aktual: e.target.value || null })}>
            <option value="">Pilih profesi…</option>
            {k.profesi.map((p) => <option key={p.id} value={p.id}>{p.nama}</option>)}
          </select>
          <span className="mt-1 block text-xs font-normal text-slate-500">
            Dipakai untuk menguji ketepatan sistem; tidak memengaruhi rekomendasimu.
          </span>
        </label>
      )}

      <div className="grid gap-5 sm:grid-cols-2">
        <label className={label}>
          Pendidikan terakhir / sedang ditempuh
          <select className={kolom} value={m.jenjang} onChange={(e) => ubah({ jenjang: e.target.value })}>
            <option value="">Pilih jenjang…</option>
            {k.jenjang.map((j) => <option key={j.kode} value={j.kode}>{j.nama}</option>)}
          </select>
        </label>
        <label className={label}>
          Program studi <span className="font-normal text-slate-500">(opsional)</span>
          <select className={kolom} value={m.prodi_id ?? ''} onChange={(e) => ubah({ prodi_id: e.target.value || null })}>
            <option value="">Tidak ada / lainnya</option>
            {k.prodi.map((p) => <option key={p.id} value={p.id}>{p.nama}</option>)}
          </select>
        </label>
        <label className={label}>
          Domisili
          <select className={kolom} value={m.domisili} onChange={(e) => ubah({ domisili: e.target.value })}>
            <option value="">Pilih kota…</option>
            {k.kota.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className={label}>
          Ekspektasi gaji per bulan <span className="font-normal text-slate-500">(juta rupiah, opsional)</span>
          <input
            className={kolom} type="number" min={0} max={200} step={0.5} inputMode="decimal"
            value={m.ekspektasi_gaji ? m.ekspektasi_gaji / 1_000_000 : ''}
            onChange={(e) => ubah({ ekspektasi_gaji: Math.max(0, Math.round(Number(e.target.value) * 1_000_000)) || 0 })}
          />
        </label>
      </div>

      <label className="flex items-start gap-3 text-sm text-slate-800">
        <input type="checkbox" className="mt-0.5 size-4 accent-teal-700" checked={m.bersedia_relokasi} onChange={(e) => ubah({ bersedia_relokasi: e.target.checked })} />
        <span>Saya bersedia pindah kota untuk bekerja</span>
      </label>
      <label className="flex items-start gap-3 text-sm text-slate-800">
        <input type="checkbox" className="mt-0.5 size-4 accent-teal-700" checked={m.punya_tanggungan} onChange={(e) => ubah({ punya_tanggungan: e.target.checked })} />
        <span>
          Saya menanggung kebutuhan keluarga
          <span className="block text-xs text-slate-500">Kalau ya, stabilitas pekerjaan ikut dipertimbangkan.</span>
        </span>
      </label>
    </div>
  )
}

function Likert({ judul, keterangan, butir, skala, jawaban, pilih }: {
  judul: string; keterangan: string; butir: Butir[]; skala: string[]
  jawaban: Record<string, number>; pilih: (kode: string, nilai: number) => void
}) {
  const terisi = butir.filter((b) => jawaban[b.kode]).length
  return (
    <div>
      <h1 className="text-lg font-semibold text-slate-900">{judul}</h1>
      <p className="mt-1 text-sm text-slate-600">{keterangan}</p>
      <p className="mt-1 text-xs text-slate-500">{terisi} dari {butir.length} terjawab · 1 = {skala[0]}, 5 = {skala[4]}</p>
      <ol className="mt-4 space-y-3">
        {butir.map((b, i) => (
          <li key={b.kode} className={kartu}>
            <p className="text-sm text-slate-800">{i + 1}. {b.teks}</p>
            <div className="mt-3 grid grid-cols-5 gap-2" role="radiogroup" aria-label={b.teks}>
              {skala.map((nama, n) => {
                const on = jawaban[b.kode] === n + 1
                return (
                  <button
                    key={nama} type="button" role="radio" aria-checked={on} title={nama}
                    onClick={() => pilih(b.kode, n + 1)}
                    className={`rounded-lg border py-2 text-xs transition-colors ${on ? 'border-teal-600 bg-teal-600 font-semibold text-white' : 'border-slate-300 bg-white text-slate-600 hover:border-teal-500'}`}
                  >
                    <span className="block text-sm font-semibold">{n + 1}</span>
                    <span className="hidden sm:block">{nama}</span>
                  </button>
                )
              })}
            </div>
          </li>
        ))}
      </ol>
    </div>
  )
}

function PilihSkill({ k, skill, ketuk }: { k: Kuesioner; skill: Record<string, number>; ketuk: (id: string) => void }) {
  const [cari, setCari] = useState('')
  const kelompok = useMemo(() => {
    const kata = cari.trim().toLowerCase()
    const peta = new Map<string, typeof k.skill>()
    for (const s of k.skill) {
      if (kata && !s.nama.toLowerCase().includes(kata) && !s.kategori.toLowerCase().includes(kata)) continue
      peta.set(s.kategori, [...(peta.get(s.kategori) ?? []), s])
    }
    return [...peta.entries()]
  }, [k, cari])

  const gaya = ['border-slate-300 bg-white text-slate-700', 'border-teal-300 bg-teal-50 text-teal-900', 'border-teal-500 bg-teal-100 text-teal-900', 'border-teal-700 bg-teal-700 text-white']

  return (
    <div>
      <h1 className="text-lg font-semibold text-slate-900">Skill apa saja yang sudah kamu kuasai?</h1>
      <p className="mt-1 text-sm text-slate-600">
        Ketuk skill untuk memilih; ketuk lagi untuk menaikkan tingkatnya (Dasar → Menengah → Mahir).
        {' '}{Object.keys(skill).length} skill dipilih.
      </p>
      <div className="relative mt-4">
        <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-slate-400" aria-hidden />
        <input className={`${kolom} mt-0 pl-9`} placeholder="Cari skill, mis. Python, Figma, SQL" value={cari} onChange={(e) => setCari(e.target.value)} />
      </div>
      <div className="mt-4 space-y-4">
        {kelompok.length === 0 && <p className="text-sm text-slate-500">Tidak ada skill yang cocok.</p>}
        {kelompok.map(([kategori, daftar]) => (
          <section key={kategori}>
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">{kategori}</h2>
            <div className="mt-2 flex flex-wrap gap-2">
              {daftar.map((s) => {
                const t = skill[s.id] ?? 0
                return (
                  <button key={s.id} type="button" aria-pressed={t > 0} onClick={() => ketuk(s.id)} className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${gaya[t]}`}>
                    {s.nama}{t > 0 && <span className="ml-1.5 text-xs opacity-80">· {k.tingkat_skill[String(t)]}</span>}
                  </button>
                )
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
