import { Route, Routes } from 'react-router-dom'
import Beranda from './halaman/Beranda'
import DetailProfesi from './halaman/DetailProfesi'
import HalamanHasil from './halaman/Hasil'
import HalamanKuesioner from './halaman/Kuesioner'
import Penilaian from './halaman/Penilaian'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Beranda />} />
      <Route path="/kuesioner" element={<HalamanKuesioner />} />
      <Route path="/hasil/:id" element={<HalamanHasil />} />
      <Route path="/hasil/:id/profesi/:pid" element={<DetailProfesi />} />
      <Route path="/hasil/:id/penilaian" element={<Penilaian />} />
      <Route path="*" element={<Beranda />} />
    </Routes>
  )
}
