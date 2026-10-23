import { defineConfig } from 'vite';
export default defineConfig({
  server: { proxy: { '/api': 'http://127.0.0.1:8001' } },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        entryFileNames: 'assets/learning-coach-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: asset => asset.names?.some(name => name.endsWith('.css'))
          ? 'assets/learning-coach-[hash][extname]' : 'assets/[name]-[hash][extname]',
      },
    },
  },
});
