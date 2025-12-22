import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

const proxyTarget =
	process.env.VITE_INTERNAL_API_BASE ??
	process.env.VITE_API_BASE ??
	'http://localhost:8000';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// Allow cloudflared or other reverse proxies to reach the dev server
		host: true,
		port: Number(process.env.VITE_DEV_PORT ?? 5173),
		allowedHosts: ['localhost', '127.0.0.1', 'altsky.info', 'www.altsky.info', '.trycloudflare.com', '.ngrok-free.dev', '.ngrok-free.app', 'frontend'],
		proxy: {
			'/api': {
				target: proxyTarget,
				changeOrigin: true,
				secure: false,
				ws: true,
				rewrite: (path) => path
			}
		},
		fs: {
			strict: false
		}
	},
	preview: {
		host: true,
		port: 4173,
		allowedHosts: ['localhost', '127.0.0.1', 'altsky.info', 'www.altsky.info', '.trycloudflare.com']
	}
});
