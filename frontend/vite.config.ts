import { defineConfig, loadEnv, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { fileURLToPath, URL } from 'node:url'

// Compose supplies the host URL; keep Vite's default output outside Docker.
const browserUrl: Plugin = {
  name: 'development-browser-url',
  configureServer(server) {
    const url = process.env.DEV_BROWSER_URL
    if (url) {
      server.printUrls = () => {
        server.config.logger.info(`  ➜  Browser: ${url}/`)
      }
    }
  },
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), 'API_PROXY_')
  return {
    plugins: [vue(), tailwindcss(), browserUrl],
    resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
    server: {
      // Allow HTTP checks from other containers on the Compose network.
      allowedHosts: ['frontend'],
      proxy: {
        '/api': {
          target: env.API_PROXY_TARGET || 'http://127.0.0.1:5000',
        },
      },
    },
  }
})
