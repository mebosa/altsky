<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { loadSkinview3d } from '$lib/skinview3d';

	export let uuid: string;
	export let autoRotate = true;

	let canvasEl: HTMLCanvasElement | null = null;
	let containerEl: HTMLDivElement | null = null;
	let viewer: any = null;
	let resizeObserver: ResizeObserver | null = null;

	function skinUrlForUuid(uuid: string) {
		// Crafatar supports direct skin PNGs by UUID.
		return `https://crafatar.com/skins/${encodeURIComponent(uuid)}`;
	}

	onMount(async () => {
		if (!canvasEl || !containerEl || !uuid) return;

		const skinview3d = await loadSkinview3d();

		const rect = containerEl.getBoundingClientRect();
		const width = Math.max(1, Math.floor(rect.width));
		const height = Math.max(1, Math.floor(rect.height));

		viewer = new skinview3d.SkinViewer({
			canvas: canvasEl,
			width,
			height,
			enableControls: true,
			zoom: 0.9,
			fov: 50
		});

		viewer.controls.enablePan = false;
		viewer.controls.enableZoom = true;
		viewer.controls.enableRotate = true;
		viewer.autoRotate = autoRotate;
		viewer.autoRotateSpeed = 1;

		await viewer.loadSkin(skinUrlForUuid(uuid), { model: 'auto-detect' });

		resizeObserver = new ResizeObserver((entries) => {
			const entry = entries[0];
			if (!entry || !viewer) return;
			const w = Math.max(1, Math.floor(entry.contentRect.width));
			const h = Math.max(1, Math.floor(entry.contentRect.height));
			viewer.setSize(w, h);
		});
		resizeObserver.observe(containerEl);
	});

	onDestroy(() => {
		try {
			resizeObserver?.disconnect();
		} catch {
			// noop
		}
		resizeObserver = null;

		try {
			viewer?.dispose?.();
		} catch {
			// noop
		}
		viewer = null;
	});
</script>

<div class="w-full h-full" bind:this={containerEl}>
	<canvas class="w-full h-full block" bind:this={canvasEl}></canvas>
</div>
