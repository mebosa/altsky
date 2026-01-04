<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
  import roomDataList from '$lib/data/dungeons/rooms.json';

  let container: HTMLDivElement;
  let canvas: HTMLCanvasElement;
  let renderer: THREE.WebGLRenderer;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let controls: OrbitControls;
  let animationId: number;
  let group: THREE.Group;
  let selectedRoomId = roomDataList[0].id;

  // Materials
  let materials: Record<string, THREE.Material>;

  function initMaterials() {
    materials = {
      stone_brick: new THREE.MeshStandardMaterial({ color: 0x888888 }),
      cracked_stone: new THREE.MeshStandardMaterial({ color: 0x666666 }),
      chest: new THREE.MeshStandardMaterial({ color: 0xffaa00, emissive: 0x332200 }),
      obsidian: new THREE.MeshStandardMaterial({ color: 0x111111 }),
      quartz: new THREE.MeshStandardMaterial({ color: 0xffffff }),
      water: new THREE.MeshStandardMaterial({ color: 0x0000ff, transparent: true, opacity: 0.6 }),
      grass: new THREE.MeshStandardMaterial({ color: 0x00ff00 }),
      redstone: new THREE.MeshStandardMaterial({ color: 0xff0000 }),
      gold_block: new THREE.MeshStandardMaterial({ color: 0xffd700, metalness: 0.8, roughness: 0.2 }),
    };
  }

  function loadRoom(id: string) {
    if (!group) return;
    const room = roomDataList.find(r => r.id === id);
    if (!room) return;

    // Clear existing
    while(group.children.length > 0){ 
        group.remove(group.children[0]); 
    }

    const geometry = new THREE.BoxGeometry(1, 1, 1);

    room.blocks.forEach((block: any) => {
      const material = materials[block.type] || materials.stone_brick;
      
      // Handle repeat
      const repeatX = block.repeat?.x || 1;
      const repeatY = block.repeat?.y || 1;
      const repeatZ = block.repeat?.z || 1;

      for (let rx = 0; rx < repeatX; rx++) {
        for (let ry = 0; ry < repeatY; ry++) {
          for (let rz = 0; rz < repeatZ; rz++) {
            const mesh = new THREE.Mesh(geometry, material);
            mesh.position.set(block.x + rx, block.y + ry, block.z + rz);
            mesh.castShadow = true;
            mesh.receiveShadow = true;
            group.add(mesh);
          }
        }
      }
    });

    // Adjust camera target if needed, or just let user pan
    if (controls) {
        controls.target.set(room.size.width / 2, room.size.height / 2, room.size.depth / 2);
    }
  }

  onMount(() => {
    if (!canvas) return;

    initMaterials();

    // 1. Scene Setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111111);
    // scene.fog = new THREE.Fog(0x111111, 10, 50);

    // 2. Camera Setup
    const aspect = container.clientWidth / container.clientHeight;
    camera = new THREE.PerspectiveCamera(60, aspect, 0.1, 1000);
    camera.position.set(20, 20, 20); // Default position
    
    // 3. Renderer Setup
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = true;

    // 4. Controls
    controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    
    // 5. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(10, 20, 10);
    dirLight.castShadow = true;
    scene.add(dirLight);

    // 6. Build Room
    group = new THREE.Group();
    scene.add(group);
    
    loadRoom(selectedRoomId);

    // Grid Helper
    const gridHelper = new THREE.GridHelper(30, 30, 0x444444, 0x222222);
    scene.add(gridHelper);

    // 7. Animation Loop
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // 8. Resize Handler
    const handleResize = () => {
      if (!container) return;
      const width = container.clientWidth;
      const height = container.clientHeight;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationId);
      renderer.dispose();
      // Dispose geometries and materials if needed
    };
  });

  onDestroy(() => {
    if (typeof window !== 'undefined') {
      // Cleanup logic handled in onMount return
    }
  });
</script>

<svelte:head>
  <title>Room Explorer | AltSky</title>
</svelte:head>

<div class="wrap">
  <div class="header">
    <a href="/dungeons" class="back-link">← Back to Dungeons</a>
    <h1>Room Explorer <span class="badge">Beta</span></h1>
    <p>Explore dungeon rooms in 3D. (Prototype)</p>
  </div>

  <div class="viewer-container" bind:this={container}>
    <canvas bind:this={canvas}></canvas>
    <div class="controls-overlay">
      <div class="control-group">
        <label>Room ID</label>
        <select bind:value={selectedRoomId} on:change={() => loadRoom(selectedRoomId)}>
          {#each roomDataList as room}
            <option value={room.id}>{room.name}</option>
          {/each}
        </select>
      </div>
      <div class="legend">
        <div class="legend-item"><span class="color-box chest"></span> Secret Chest</div>
        <div class="legend-item"><span class="color-box stone"></span> Wall/Floor</div>
        <div class="legend-item"><span class="color-box obsidian"></span> Obsidian</div>
        <div class="legend-item"><span class="color-box quartz"></span> Quartz</div>
        <div class="legend-item"><span class="color-box water"></span> Water</div>
        <div class="legend-item"><span class="color-box redstone"></span> Redstone</div>
        <div class="legend-item"><span class="color-box gold"></span> Gold Block</div>
      </div>
    </div>
  </div>
</div>

<style>
  .wrap {
    max-width: 1200px;
    margin: 40px auto;
    padding: 0 18px;
    color: var(--theme-text-primary);
    height: calc(100vh - 80px);
    display: flex;
    flex-direction: column;
  }

  .header {
    margin-bottom: 20px;
    flex-shrink: 0;
  }

  .back-link {
    display: inline-block;
    margin-bottom: 8px;
    color: var(--theme-text-soft);
    text-decoration: none;
    font-size: 14px;
  }

  .back-link:hover {
    color: var(--theme-accent);
  }

  h1 {
    margin: 0;
    font-size: 28px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .badge {
    font-size: 12px;
    background: var(--theme-accent);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    vertical-align: middle;
  }

  p {
    margin: 4px 0 0;
    color: var(--theme-text-soft);
  }

  .viewer-container {
    flex: 1;
    background: #000;
    border-radius: 16px;
    overflow: hidden;
    position: relative;
    border: 1px solid var(--theme-surface-border);
    box-shadow: var(--neu-elevated);
    min-height: 400px;
  }

  canvas {
    display: block;
    width: 100%;
    height: 100%;
  }

  .controls-overlay {
    position: absolute;
    top: 16px;
    left: 16px;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(8px);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-width: 200px;
  }

  .control-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  label {
    font-size: 12px;
    color: var(--theme-text-soft);
    font-weight: 600;
  }

  select {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: white;
    padding: 8px;
    border-radius: 6px;
    font-size: 14px;
    outline: none;
  }

  select:focus {
    border-color: var(--theme-accent);
  }

  .legend {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #ddd;
  }

  .color-box {
    width: 12px;
    height: 12px;
    border-radius: 2px;
  }

  .color-box.chest { background: #ffaa00; }
  .color-box.stone { background: #888888; }
  .color-box.obsidian { background: #111111; border: 1px solid #333; }
  .color-box.quartz { background: #ffffff; }
  .color-box.water { background: #0000ff; opacity: 0.6; }
  .color-box.redstone { background: #ff0000; }
  .color-box.gold { background: #ffd700; }
</style>
