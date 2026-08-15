import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // In dev, proxy API calls to Django so the browser never has to deal
    // with CORS at all - /health, /check, /login etc. all get forwarded
    // to localhost:8000 transparently. (CORS is still configured on the
    // Django side too, for when you call the API directly.)
    proxy: {
      '/health': 'http://localhost:8000',
      '/check': 'http://localhost:8000',
      '/metrics': 'http://localhost:8000',
      '/login': 'http://localhost:8000',
      '/posts': 'http://localhost:8000',
      '/profile': 'http://localhost:8000',
    },
  },
})
