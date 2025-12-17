<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { loadSkinview3d } from '$lib/skinview3d';
	import { texturePackStore } from '$lib/stores/texturePack';

	export let uuid: string;
	export let autoRotate = true;
	export let armor: { helmet?: string, chestplate?: string, leggings?: string, boots?: string } | undefined = undefined;

	let canvasEl: HTMLCanvasElement | null = null;
	let containerEl: HTMLDivElement | null = null;
	let viewer: any = null;
	let offscreenViewer: any = null;
	let armorModel1: any = null;
	let armorModel2: any = null;
	// Separate models for each piece to handle mixed sets and visibility
	let modelHelmet: any[] = [];
	let modelChestplate: any[] = [];
	let modelLeggings: any[] = [];
	let modelBoots: any[] = [];
	
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

	async function updateArmor(currentArmor: any) {
		if (!viewer || !skinview3dLib || !offscreenViewer) return;
		
		console.log('updateArmor called. Pack:', $texturePackStore, 'Armor:', currentArmor);

		// Clean up all existing armor models
		const cleanup = (models: any | any[]) => {
			if (Array.isArray(models)) {
				models.forEach(model => {
					if (model) viewer.playerObject.remove(model);
				});
				return [];
			} else if (models) {
				viewer.playerObject.remove(models);
				return []; // Return empty array to be safe if assigning to array var
			}
			return [];
		};

		armorModel1 = cleanup(armorModel1); // These are unused now but kept for safety
		armorModel2 = cleanup(armorModel2);
		modelHelmet = cleanup(modelHelmet);
		modelChestplate = cleanup(modelChestplate);
		modelLeggings = cleanup(modelLeggings);
		modelBoots = cleanup(modelBoots);
		
		if (!currentArmor) return;

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
					return true;
				}
				return false;
			} catch (e) {
				console.warn("Failed to process skin texture", e);
				return false;
			}
		};

		// Helper to create an armor layer model
		const createArmorLayer = async (itemId: string | undefined, color: string | undefined, skinUrl: string | undefined, layer: 1 | 2, scale: number, visibleParts: string[]) => {
			if (!itemId) return [];

			let urls: { url: string, isOverlay: boolean, useColor: boolean }[] = [];
			let isSkinUrl = false;

			if ($texturePackStore === 'furfsky') {
				if (skinUrl) {
					// If it's a skull (has skinUrl), prefer the skin texture.
					// FurfSky armor textures are for armor models, not skulls.
					urls.push({ url: skinUrl, isOverlay: false, useColor: false });
					isSkinUrl = true;
				} else {
					urls.push({ url: `/api/texture/armor/${itemId}/${layer}`, isOverlay: false, useColor: false });
				}
			} else {
				if (skinUrl) {
					urls.push({ url: skinUrl, isOverlay: false, useColor: false });
					isSkinUrl = true;
				} else {
					// Vanilla mapping
					const getVanillaName = (id: string) => {
						if (id.includes('DIAMOND')) return 'diamond';
						if (id.includes('IRON')) return 'iron';
						if (id.includes('GOLD')) return 'gold';
						if (id.includes('CHAIN')) return 'chainmail';
						return 'leather'; // Default fallback
					};
					const name = getVanillaName(itemId);
					
					if (name === 'leather') {
						// For leather, we need BOTH the base (brown) and the overlay (colored)
						urls.push({ 
							url: `https://cdn.jsdelivr.net/gh/InventivetalentDev/minecraft-assets@1.8.9/assets/minecraft/textures/models/armor/${name}_layer_${layer}.png`,
							isOverlay: false,
							useColor: false // Base layer is NOT tinted
						});
						urls.push({ 
							url: `https://cdn.jsdelivr.net/gh/InventivetalentDev/minecraft-assets@1.8.9/assets/minecraft/textures/models/armor/${name}_layer_${layer}_overlay.png`,
							isOverlay: true,
							useColor: true // Overlay layer IS tinted
						});
					} else {
						urls.push({ 
							url: `https://cdn.jsdelivr.net/gh/InventivetalentDev/minecraft-assets@1.8.9/assets/minecraft/textures/models/armor/${name}_layer_${layer}.png`,
							isOverlay: false,
							useColor: true // Non-leather vanilla armor can be tinted
						});
					}
				}
			}

			const createdModels: any[] = [];

			for (const texInfo of urls) {
				try {
					let model;
					try {
						model = new PlayerObject();
					} catch (e) {
						model = new PlayerObject({ model: 'default' });
					}

					model.scale.set(scale, scale, scale);
					
					// Slight scale offset for overlay to prevent z-fighting
					if (texInfo.isOverlay) {
						const overlayScale = scale + 0.002;
						model.scale.set(overlayScale, overlayScale, overlayScale);
					}
					
					// Load texture
					let success = false;
					if ($texturePackStore === 'furfsky' && !isSkinUrl) {
						// Use our API which returns processed images
						const res = await fetch(texInfo.url);
						if (res.ok) {
							success = await loadSkinToPlayerObject(model, texInfo.url);
						} else if (skinUrl) {
							// Fallback to skinUrl if FurfSky missing
							success = await loadSkinToPlayerObject(model, skinUrl);
							// Disable color for skin fallback
							texInfo.useColor = false;
						}
					} else {
						// Load directly from URL for vanilla
						success = await loadSkinToPlayerObject(model, texInfo.url);
					}

					if (!success) {
						console.warn(`Failed to load texture for ${itemId}, skipping model`);
						continue;
					}

					// Fix transparency and apply color
					model.traverse((child: any) => {
						if (child.isMesh && child.material) {
							child.material.transparent = true;
							child.material.alphaTest = 0.001;
							
							// Apply color if needed
							if (texInfo.useColor && color && !isSkinUrl) {
								const hexColor = color.startsWith('#') ? color : '#' + color;
								child.material.color.set(hexColor);
							}
							
							child.material.needsUpdate = true;
						}
					});
					
					model.renderOrder = layer === 1 ? 10 : 11;
					if (texInfo.isOverlay) model.renderOrder += 0.1;

					// Hide irrelevant parts
					const allParts = ['head', 'body', 'rightArm', 'leftArm', 'rightLeg', 'leftLeg'];
					allParts.forEach(part => {
						const isVisible = visibleParts.includes(part);
						if (model.skin[part]) {
							model.skin[part].visible = isVisible;
						}
						// Handle overlay layers (e.g. headLayer, bodyLayer)
						const layerName = part + 'Layer';
						// @ts-ignore
						if (model.skin[layerName]) {
							// @ts-ignore
							model.skin[layerName].visible = isVisible;
						}
					});

					viewer.playerObject.add(model);
					createdModels.push(model);

				} catch (e) {
					console.warn(`Failed to load armor layer for ${itemId}`, e);
				}
			}
			
			return createdModels;
		};

		const getArmorInfo = (partData: any) => {
			if (!partData) return { id: undefined, color: undefined, skin_url: undefined };
			if (typeof partData === 'string') return { id: partData, color: undefined, skin_url: undefined };
			return { id: partData.id, color: partData.color, skin_url: partData.skin_url };
		};

		// Layer 1 Scale: 1.15, Layer 2 Scale: 1.10
		
		// Helmet: Layer 1, Head only
		const helmetInfo = getArmorInfo(currentArmor.helmet);
		modelHelmet = await createArmorLayer(helmetInfo.id, helmetInfo.color, helmetInfo.skin_url, 1, 1.15, ['head']);
		// Lower helmet position slightly to fit better (skinview3d units)
		modelHelmet.forEach(m => m.position.y = -2.0); 
		
		// Chestplate: Layer 1, Body + Arms
		const chestplateInfo = getArmorInfo(currentArmor.chestplate);
		modelChestplate = await createArmorLayer(chestplateInfo.id, chestplateInfo.color, chestplateInfo.skin_url, 1, 1.15, ['body', 'rightArm', 'leftArm']);
		
		// Leggings: Layer 2, Body + Legs
		const leggingsInfo = getArmorInfo(currentArmor.leggings);
		modelLeggings = await createArmorLayer(leggingsInfo.id, leggingsInfo.color, leggingsInfo.skin_url, 2, 1.15, ['body', 'rightLeg', 'leftLeg']);
		
		// Boots: Layer 1, Legs only
		const bootsInfo = getArmorInfo(currentArmor.boots);
		modelBoots = await createArmorLayer(bootsInfo.id, bootsInfo.color, bootsInfo.skin_url, 1, 1.15, ['rightLeg', 'leftLeg']);
		
		console.log('Armor updated');
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
