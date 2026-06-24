import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 3456,
    open: false,
    fs: {
      allow: ['.'],
    },
  },
  build: {
    target: 'esnext',
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('interpretation.js') || id.includes('yoga-') || id.includes('planet-house-details')) {
            return 'jyotish-reference';
          }
          if (id.includes('skill-map.js') || id.includes('mevg-audit.js')) {
            return 'product-audit';
          }
        },
      },
    },
  },
});
