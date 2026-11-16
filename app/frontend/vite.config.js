import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 构建产物直接输出到仓库根（GitHub Pages 从仓库根部署）
// emptyOutDir=false 防止清空根目录的既有静态页面；文件名固定 hash-free，避免重复部署累积
export default defineConfig({
  base: '/travel-tracker/',
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000'
    }
  },
  build: {
    outDir: '../../',
    emptyOutDir: false,
    assetsDir: 'assets',
    rollupOptions: {
      input: {
        home: 'index.html',
        study: 'study.html'
      },
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name].[ext]'
      }
    }
  }
})
