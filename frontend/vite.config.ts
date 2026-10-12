import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // API FastAPI di port 8000; saat build, antarmuka dilayani dari server yang sama.
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
})
