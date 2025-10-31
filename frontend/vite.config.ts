import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// Allow cloudflared or other reverse proxies to reach the dev server
		host: true,
		port: Number(process.env.VITE_DEV_PORT ?? 5173),
		allowedHosts: ['localhost', '127.0.0.1', '.trycloudflare.com']
	}
});
