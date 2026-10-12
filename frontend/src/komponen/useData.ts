import { useEffect, useState } from 'react'

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
    // `ambil` dibuat ulang tiap render; yang menentukan muat ulang adalah kuncinya.
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
