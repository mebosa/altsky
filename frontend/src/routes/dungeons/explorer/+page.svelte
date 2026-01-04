<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

  let container: HTMLDivElement;
  let canvas: HTMLCanvasElement;
  let renderer: THREE.WebGLRenderer;
  let scene: THREE.Scene;
  let camera: THREE.PerspectiveCamera;
  let controls: OrbitControls;
  let animationId: number;
  let group: THREE.Group;
  let selectedRoomId = 'tic_tac_toe';

  // --- Room Generators ---

  function getTicTacToeRoom() {
    const width = 15;
    const height = 8;
    const depth = 15;
    const blocks: { x: number; y: number; z: number; type: string }[] = [];

    // Floor & Ceiling
    for (let x = 0; x < width; x++) {
      for (let z = 0; z < depth; z++) {
        blocks.push({ x, y: 0, z, type: 'stone_brick' });
        if (x === 0 || x === width - 1 || z === 0 || z === depth - 1) {
           blocks.push({ x, y: height - 1, z, type: 'stone_brick' });
        }
      }
    }

    // Walls
    for (let y = 1; y < height; y++) {
      for (let x = 0; x < width; x++) {
        blocks.push({ x, y, z: 0, type: 'stone_brick' });
        if (x < 6 || x > 8 || y > 4) blocks.push({ x, y, z: depth - 1, type: 'stone_brick' });
      }
      for (let z = 0; z < depth; z++) {
        blocks.push({ x: 0, y, z, type: 'stone_brick' });
        blocks.push({ x: width - 1, y, z, type: 'stone_brick' });
      }
    }
    
    // Front Wall (South) fix
    for (let y = 1; y < height; y++) {
        for (let x = 0; x < width; x++) {
             if (x < 6 || x > 8 || y > 4) blocks.push({ x, y, z: depth - 1, type: 'stone_brick' });
        }
    }

    // Board
    const boardStartX = 5;
    const boardStartY = 2;
    for(let bx = 0; bx < 5; bx++) {
        for(let by = 0; by < 5; by++) {
            blocks.push({ x: boardStartX + bx, y: boardStartY + by, z: 1, type: 'obsidian' });
        }
    }
    for(let r=0; r<3; r++) {
        for(let c=0; c<3; c++) {
            blocks.push({ x: boardStartX + 1 + (c*1), y: boardStartY + 1 + (r*1), z: 2, type: 'quartz' });
        }
    }

    // Secret
    blocks.push({ x: 13, y: 1, z: 13, type: 'chest' });

    return { width, height, depth, blocks };
  }

  function getThreeWeirdosRoom() {
    const width = 13;
    const height = 7;
    const depth = 13;
    const blocks: { x: number; y: number; z: number; type: string }[] = [];

    // Floor
    for (let x = 0; x < width; x++) {
      for (let z = 0; z < depth; z++) {
        blocks.push({ x, y: 0, z, type: 'stone_brick' });
      }
    }

    // Walls
    for (let y = 1; y < height; y++) {
      for (let x = 0; x < width; x++) {
        blocks.push({ x, y, z: 0, type: 'stone_brick' });
        blocks.push({ x, y, z: depth - 1, type: 'stone_brick' });
      }
      for (let z = 1; z < depth - 1; z++) {
        blocks.push({ x: 0, y, z, type: 'stone_brick' });
        blocks.push({ x: width - 1, y, z, type: 'stone_brick' });
      }
    }

    // The 3 Chests (Weirdos)
    blocks.push({ x: 4, y: 1, z: 6, type: 'chest' });
    blocks.push({ x: 6, y: 1, z: 6, type: 'chest' });
    blocks.push({ x: 8, y: 1, z: 6, type: 'chest' });

    // Water trough
    for(let x=3; x<10; x++) {
        blocks.push({ x, y: 0, z: 8, type: 'water' });
    }

    return { width, height, depth, blocks };
  }

  function getEntranceRoom() {
    const width = 11;
    const height = 6;
    const depth = 11;
    const blocks: { x: number; y: number; z: number; type: string }[] = [];

    // Floor (Green Carpet feel)
    for (let x = 0; x < width; x++) {
      for (let z = 0; z < depth; z++) {
        blocks.push({ x, y: 0, z, type: 'grass' });
      }
    }

    // Walls
    for (let y = 1; y < height; y++) {
      for (let x = 0; x < width; x++) {
        blocks.push({ x, y, z: 0, type: 'stone_brick' });
        blocks.push({ x, y, z: depth - 1, type: 'stone_brick' });
      }
      for (let z = 1; z < depth - 1; z++) {
        blocks.push({ x: 0, y, z, type: 'stone_brick' });
        blocks.push({ x: width - 1, y, z, type: 'stone_brick' });
      }
    }

    // Blood Door (Redstone Block)
    blocks.push({ x: 5, y: 1, z: 0, type: 'redstone' });
    blocks.push({ x: 5, y: 2, z: 0, type: 'redstone' });

    return { width, height, depth, blocks };
  }

  const rooms: Record<string, () => { width: number, height: number, depth: number, blocks: any[] }> = {
    'tic_tac_toe': getTicTacToeRoom,
    'three_weirdos': getThreeWeirdosRoom,
    'entrance': getEntranceRoom
  };

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
    };
  }

  function loadRoom(id: string) {
    if (!group || !rooms[id]) return;

    // Clear existing
    while(group.children.length > 0){ 
        group.remove(group.children[0]); 
    }

    const data = rooms[id]();
    const geometry = new THREE.BoxGeometry(1, 1, 1);

    data.blocks.forEach(block => {
      const material = materials[block.type] || materials.stone_brick;
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(block.x, block.y, block.z);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      group.add(mesh);
    });

    // Adjust camera target if needed, or just let user pan
    if (controls) {
        controls.target.set(data.width / 2, data.height / 2, data.depth / 2);
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
          <option value="tic_tac_toe">1x1 Puzzle (Tic Tac Toe)</option>
          <option value="three_weirdos">1x1 Puzzle (Three Weirdos)</option>
          <option value="entrance">1x1 Entrance</option>
        </select>
      </div>
      <div class="legend">
        <div class="legend-item"><span class="color-box chest"></span> Secret Chest</div>
        <div class="legend-item"><span class="color-box stone"></span> Wall/Floor</div>
        <div class="legend-item"><span class="color-box obsidian"></span> Obsidian</div>
        <div class="legend-item"><span class="color-box quartz"></span> Quartz</div>
        <div class="legend-item"><span class="color-box water"></span> Water</div>
        <div class="legend-item"><span class="color-box redstone"></span> Redstone</div>
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
</style>
