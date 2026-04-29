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
  },
});
