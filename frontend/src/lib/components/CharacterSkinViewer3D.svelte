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

			// Try to load cape
			viewer.loadCape(null); // Reset cape

			try {
				const response = await fetch(`https://api.capes.dev/load/${cleanUuid}`);
				if (response.ok) {
					const data = await response.json();
					// Priority: Minecraft > Optifine > MinecraftCapes > etc. > LabyMod
					const capeTypes = ['minecraft', 'optifine', 'minecraftcapes', 'tlauncher', '5zig', 'cloaksplus', 'mantle', 'labymod'];
					let capeUrl = null;
					
					for (const type of capeTypes) {
						if (data[type] && data[type].exists && data[type].imageUrl) {
							capeUrl = data[type].imageUrl;
							console.log(`Found ${type} cape: ${capeUrl}`);
							break;
						}
					}

					if (capeUrl) {
						await viewer.loadCape(capeUrl);
					} else {
						// Fallback to Visage/Crafatar if capes.dev finds nothing (unlikely but safe)
						const capeProviders = [
							`https://visage.surgeplay.com/cape/${cleanUuid}`,
							`https://crafatar.com/capes/${cleanUuid}`
						];
						for (const url of capeProviders) {
							try {
								await viewer.loadCape(url);
								break;
							} catch (e) {
								// ignore
							}
						}
					}
				}
			} catch (e) {
				console.warn('Failed to load cape from capes.dev', e);
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

			let urls: { url: string, isOverlay: boolean }[] = [];

			if ($texturePackStore === 'furfsky') {
				if (skinUrl) {
					// If it's a skull (has skinUrl), prefer the skin texture.
					// FurfSky armor textures are for armor models, not skulls.
					urls.push({ url: skinUrl, isOverlay: false });
				} else {
					urls.push({ url: `/api/texture/armor/${itemId}/${layer}`, isOverlay: false });
				}
			} else {
				if (skinUrl) {
					urls.push({ url: skinUrl, isOverlay: false });
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
						// Default leather color if not dyed
						if (!color) color = '#A06540';
						const cleanColor = color.replace(/#/g, '');
						
						// For leather, we need BOTH the base (colored) and the overlay (static)
						// In 1.8.9: layer_1 is the colored part, overlay is the static brown part
						urls.push({ 
							// Request TINTED texture from backend
							url: `/api/texture/vanilla-armor/${name}/${layer}?color=${cleanColor}&_t=${Date.now()}`,
							isOverlay: false,
							useColor: false // We rely on server-side tinting
						});
						urls.push({ 
							url: `https://cdn.jsdelivr.net/gh/InventivetalentDev/minecraft-assets@1.8.9/assets/minecraft/textures/models/armor/${name}_layer_${layer}_overlay.png`,
							isOverlay: true,
							useColor: false
						});
					} else {
						// Non-leather vanilla armor (diamond, iron, etc.)
						if (color) {
							const cleanColor = color.replace(/#/g, '');
							urls.push({ 
								url: `/api/texture/vanilla-armor/${name}/${layer}?color=${cleanColor}&_t=${Date.now()}`,
								isOverlay: false,
								useColor: false
							});
						} else {
							urls.push({ 
								url: `https://cdn.jsdelivr.net/gh/InventivetalentDev/minecraft-assets@1.8.9/assets/minecraft/textures/models/armor/${name}_layer_${layer}.png`,
								isOverlay: false,
								useColor: false
							});
						}
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
					
					// Use our API or CDN directly
					// success = await loadSkinToPlayerObject(model, texInfo.url);
					
					// Manual fetch with retry
					const maxRetries = 3;
					for (let attempt = 1; attempt <= maxRetries; attempt++) {
						try {
							console.log(`[Armor] Fetching ${texInfo.url} (Attempt ${attempt}/${maxRetries})`);
							const resp = await fetch(texInfo.url);
							if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
							const blob = await resp.blob();
							const blobUrl = URL.createObjectURL(blob);
							
							// Load the blob URL
							success = await loadSkinToPlayerObject(model, blobUrl);
							
							// Clean up
							URL.revokeObjectURL(blobUrl);
							
							if (success) break; // Exit retry loop on success
						} catch (err) {
							console.error(`[Armor] Failed to fetch ${texInfo.url} (Attempt ${attempt}/${maxRetries})`, err);
							success = false;
							if (attempt < maxRetries) {
								// Wait before retrying
								await new Promise(resolve => setTimeout(resolve, 500 * attempt));
							}
						}
					}

					if (!success) {
						console.warn(`Failed to load texture for ${itemId}, skipping model`);
						continue;
					}

					// Fix transparency
					model.traverse((child: any) => {
						if (child.isMesh) {
							if (!child.material) return;
							const materials = Array.isArray(child.material) ? child.material : [child.material];
							materials.forEach((mat: any) => {
								mat.transparent = true;
								mat.alphaTest = 0.001;
								mat.side = 2; // DoubleSide
								
								// Reset color to white to ensure texture color is used
								if (mat.color) mat.color.set(0xffffff);
								
								mat.needsUpdate = true;
							});
						}
					});
					
					// Render Order:
					// Inner Layer (Layer 2) should be drawn BEFORE Outer Layer (Layer 1) for proper transparency
					// Layer 2 Base: 10
					// Layer 2 Overlay: 10.1
					// Layer 1 Base: 11
					// Layer 1 Overlay: 11.1
					model.renderOrder = layer === 2 ? 10 : 11;
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

					// Hide cape, elytra, and ears on armor models by scaling them to 0
					// This avoids potential issues with visibility toggling or if they share materials
					if (model.cape) {
						model.cape.visible = false;
						model.cape.scale.set(0, 0, 0);
					}
					if (model.elytra) {
						model.elytra.visible = false;
						model.elytra.scale.set(0, 0, 0);
					}
					if (model.ears) {
						model.ears.visible = false;
						model.ears.scale.set(0, 0, 0);
					}

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
		// User requested -1.3
		modelHelmet.forEach(m => m.position.y = -1.3); 
		
		// Chestplate: Layer 1, Body + Arms
		const chestplateInfo = getArmorInfo(currentArmor.chestplate);
		modelChestplate = await createArmorLayer(chestplateInfo.id, chestplateInfo.color, chestplateInfo.skin_url, 1, 1.15, ['body', 'rightArm', 'leftArm']);
		
		// Leggings: Layer 2, Body + Legs (Inner layer, smaller scale)
		const leggingsInfo = getArmorInfo(currentArmor.leggings);
		// Increased scale to 1.15 as requested
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
