import { Route, Routes } from 'react-router-dom'
import Beranda from './halaman/Beranda'
import Cari from './halaman/Cari'
import DetailProfesi from './halaman/DetailProfesi'
import Explore from './halaman/Explore'
import Kuesioner from './halaman/Kuesioner'
import Peneliti from './halaman/Peneliti'
import Penilaian from './halaman/Penilaian'
import Profil from './halaman/Profil'
import Roadmap from './halaman/Roadmap'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Beranda />} />
      <Route path="/mulai" element={<Kuesioner />} />
      <Route path="/explore/:id" element={<Explore />} />
      <Route path="/explore/:id/profesi/:pid" element={<DetailProfesi />} />
      <Route path="/explore/:id/cari" element={<Cari />} />
      <Route path="/explore/:id/roadmap" element={<Roadmap />} />
      <Route path="/explore/:id/profil" element={<Profil />} />
      <Route path="/peneliti" element={<Peneliti />} />
      <Route path="/explore/:id/penilaian" element={<Penilaian />} />
      <Route path="*" element={<Beranda />} />
    </Routes>
  )
}
