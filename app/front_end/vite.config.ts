import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

const port = process.env.PORT ? parseInt(process.env.PORT) : 5173;
const domain = process.env.DOMAIN || 'localhost';
const origin = `http://${domain}:${port}`;

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
    server: {
    host: '0.0.0.0',
    port: port,
    origin: origin
  }
});
