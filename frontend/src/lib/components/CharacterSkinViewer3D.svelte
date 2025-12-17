<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { loadSkinview3d } from '$lib/skinview3d';
	import { texturePackStore } from '$lib/stores/texturePack';

	export let uuid: string;
	export let autoRotate = true;
	export let armor: { 
		helmet?: string, 
		chestplate?: string, 
		leggings?: string, 
		boots?: string,
		helmetColor?: string | null,
		chestplateColor?: string | null,
		leggingsColor?: string | null,
		bootsColor?: string | null
	} | undefined = undefined;

	let canvasEl: HTMLCanvasElement | null = null;
	let containerEl: HTMLDivElement | null = null;
	let viewer: any = null;
	let offscreenViewer: any = null;
	let armorModel1: any = null;
	let armorModel2: any = null;
	let resizeObserver: ResizeObserver | null = null;
	let error: string | null = null;
	let loading = true;

	async function updateSkin() {
		if (viewer && uuid) {
			loading = true;
			error = null;
			
			// Try multiple skin providers in order
			const cleanUuid = uuid.replace(/-/g, '');
			const providers = [
				`https://visage.surgeplay.com/skin/${cleanUuid}`,
				`https://crafatar.com/skins/${cleanUuid}`,
				`https://minotar.net/skin/${cleanUuid}`
			];

			for (const url of providers) {
				try {
					console.log(`Attempting to load skin from: ${url}`);
					await viewer.loadSkin(url, { model: 'auto-detect' });
					loading = false;
					break; // Success
				} catch (e) {
					console.warn(`Failed to load skin from ${url}:`, e);
				}
			}
			
			if (loading) {
				// If all providers fail
				console.error('All skin providers failed');
				error = 'Failed to load skin';
				loading = false;
			}
		}
	}

	let skinview3dLib: any = null;

	// Old function removed to avoid duplication


	$: if (viewer && uuid) {
		updateSkin();
	}

	// Reactively update armor when dependencies change
	$: if (viewer && skinview3dLib && offscreenViewer && $texturePackStore) {
		// We include armor in the dependency check by passing it or just referencing it
		updateArmor(armor);
	}

	async function updateArmor(currentArmor: typeof armor) {
		if (!viewer || !skinview3dLib || !offscreenViewer) return;
		
		console.log('updateArmor called. Pack:', $texturePackStore, 'Armor:', currentArmor);

		// If not using FurfSky, remove custom armor and return
		if ($texturePackStore !== 'furfsky') {
			console.log('Not using FurfSky, removing armor layers');
			if (armorModel1) {
				viewer.scene.remove(armorModel1);
				viewer.playerObject.remove(armorModel1);
				armorModel1 = null;
			}
			if (armorModel2) {
				viewer.scene.remove(armorModel2);
				viewer.playerObject.remove(armorModel2);
				armorModel2 = null;
			}
			// TODO: Implement Vanilla armor rendering here using standard textures
			// For now, we just hide the custom armor as requested/implied by "Vanilla" mode
			return;
		}
		
		// Clean up existing armor to rebuild
		if (armorModel1) {
			viewer.playerObject.remove(armorModel1);
			armorModel1 = null;
		}
		if (armorModel2) {
			viewer.playerObject.remove(armorModel2);
			armorModel2 = null;
		}
		
		if (!currentArmor) return;
		
		const layer1Id = currentArmor.chestplate || currentArmor.helmet || currentArmor.boots;
		const layer2Id = currentArmor.leggings;
		
		console.log('Layer 1 ID:', layer1Id);
		console.log('Layer 2 ID:', layer2Id);

		// Use the library class directly
		const PlayerObject = skinview3dLib.PlayerObject;

		// Helper to load skin onto a PlayerObject using the shared offscreen viewer
		const loadSkinToPlayerObject = async (playerObj: any, url: string) => {
			try {
				await offscreenViewer.loadSkin(url);
				const texture = offscreenViewer.playerObject.skin.map;
				if (texture) {
					const newTexture = texture.clone();
					newTexture.needsUpdate = true;
					playerObj.skin.map = newTexture;
					playerObj.skin.modelType = 'default';
				}
			} catch (e) {
				console.warn("Failed to process skin texture", e);
			}
		};
		
		if (layer1Id) {
			try {
				const url = `/api/texture/armor/${layer1Id}/1`;
				console.log('Fetching armor layer 1:', url);
				const res = await fetch(url);
				if (res.ok) {
					// Create empty PlayerObject
					try {
						armorModel1 = new PlayerObject();
					} catch (e) {
						armorModel1 = new PlayerObject({ model: 'default' });
					}
					
					// Scale up slightly to avoid z-fighting
					// Layer 1 (Chest/Boots/Helmet) needs to be larger than skin outer layer (approx 1.05)
					armorModel1.scale.set(1.15, 1.15, 1.15); 
					
					await loadSkinToPlayerObject(armorModel1, url);
					
					// Fix transparency and render order for armor
					armorModel1.traverse((child: any) => {
						if (child.isMesh && child.material) {
							child.material.transparent = true;
							child.material.alphaTest = 0.001;
							child.material.needsUpdate = true;
						}
					});
					armorModel1.renderOrder = 10;

					// Add to player object for animation
					viewer.playerObject.add(armorModel1);
					
					// Ensure visible
					armorModel1.visible = true;
					
					console.log('Armor layer 1 loaded and added to player', armorModel1);
				} else {
					console.warn('Failed to fetch armor layer 1:', res.status);
				}
			} catch (e) {
				console.warn("Failed to load armor layer 1", e);
			}
		}
		
		if (layer2Id) {
			 try {
				const url = `/api/texture/armor/${layer2Id}/2`;
				console.log('Fetching armor layer 2:', url);
				const res = await fetch(url);
				if (res.ok) {
					try {
						armorModel2 = new PlayerObject();
					} catch (e) {
						armorModel2 = new PlayerObject({ model: 'default' });
					}

					armorModel2.scale.set(1.10, 1.10, 1.10);

					await loadSkinToPlayerObject(armorModel2, url);
					
					// Fix transparency and render order for armor
					armorModel2.traverse((child: any) => {
						if (child.isMesh && child.material) {
							child.material.transparent = true;
							child.material.alphaTest = 0.001;
							child.material.needsUpdate = true;
						}
					});
					armorModel2.renderOrder = 11;

					viewer.playerObject.add(armorModel2);
					armorModel2.visible = true;
					
					console.log('Armor layer 2 loaded and added to player', armorModel2);
				} else {
					console.warn('Failed to fetch armor layer 2:', res.status);
				}
			} catch (e) {
				console.warn("Failed to load armor layer 2", e);
			}
		}
	}

	onMount(async () => {
		if (!canvasEl || !containerEl) return;

		try {
			skinview3dLib = await loadSkinview3d();

			// Create shared offscreen viewer for texture processing
			offscreenViewer = new skinview3dLib.SkinViewer({
				canvas: document.createElement('canvas'),
				width: 64,
				height: 64,
				renderPaused: true
			});

			const rect = containerEl.getBoundingClientRect();
			const width = Math.max(1, Math.floor(rect.width));
			const height = Math.max(1, Math.floor(rect.height));

			viewer = new skinview3dLib.SkinViewer({
				canvas: canvasEl,
				width,
				height,
				enableControls: true,
				zoom: 0.9,
				fov: 50,
				alpha: true 
			});

			// Set initial background to transparent or a specific color if needed
			// viewer.background = 0x000000; // or null for transparent

			viewer.controls.enablePan = false;
			viewer.controls.enableZoom = true;
			viewer.controls.enableRotate = true;
			viewer.autoRotate = autoRotate;
			viewer.autoRotateSpeed = 1;

			if (uuid) {
				await updateSkin();
			}

			resizeObserver = new ResizeObserver((entries) => {
				const entry = entries[0];
				if (!entry || !viewer) return;
				const w = Math.max(1, Math.floor(entry.contentRect.width));
				const h = Math.max(1, Math.floor(entry.contentRect.height));
				viewer.setSize(w, h);
			});
			resizeObserver.observe(containerEl);
		} catch (e) {
			console.error('Failed to initialize skinview3d', e);
			error = 'Failed to init 3D viewer';
			loading = false;
		}
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
		
		try {
			offscreenViewer?.dispose?.();
		} catch {
			// noop
		}
		offscreenViewer = null;
	});
</script>

<div class="viewer-container" bind:this={containerEl}>
	{#if error}
		<div class="status-msg error">{error}</div>
	{/if}
	<canvas bind:this={canvasEl}></canvas>
</div>

<style>
	.viewer-container {
		width: 100%;
		height: 100%;
		display: block;
		position: relative;
		min-height: 200px; /* Ensure minimum height */
	}
	
	canvas {
		display: block;
		width: 100%;
		height: 100%;
		outline: none;
	}

	.status-msg {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		color: var(--theme-text-soft, #ccc);
		font-size: 0.9rem;
		pointer-events: none;
	}
	
	.error {
		color: #ff6b6b;
	}
</style>
