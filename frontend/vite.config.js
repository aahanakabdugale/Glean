import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'
import path from 'path'

// Builds into /simulator/dist so Python server can serve the app
// without any Node.js requirement for judges.
export default defineConfig({
  plugins: [svelte()],
  build: {
    outDir: path.resolve(import.meta.dirname, '../simulator/dist'),
    emptyOutDir: true,
  },
})
