import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Determine if running in Docker (check for Docker-specific env or hostname patterns)
const isDocker = process.env.DOCKER_ENV === 'true' || false;

// Use container names when in Docker, localhost otherwise
const agentHost = isDocker ? 'agent' : 'localhost';
const llmHost = isDocker ? 'llm' : 'localhost';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api/agent': {
        target: `http://${agentHost}:8010`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/agent/, ''),
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
      '/api/llm': {
        target: `http://${llmHost}:8001`,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/llm/, ''),
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
})
