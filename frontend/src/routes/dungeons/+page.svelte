<script lang="ts">
  import { onMount } from 'svelte';

  // Placeholder for future implementation
  const features = [
    {
      title: 'Dashboard',
      description: 'View your dungeon stats, class levels, and recent runs.',
      icon: '📊',
      link: '/dungeons/dashboard',
      status: 'Available'
    },
    {
      title: 'Room Explorer',
      description: 'Explore dungeon rooms in 3D and learn secrets.',
      icon: '🗺️',
      link: '/dungeons/explorer',
      status: 'Beta'
    },
    {
      title: 'Profit Calculator',
      description: 'Calculate expected value from dungeon chests.',
      icon: '💰',
      link: '/dungeons/profit',
      status: 'Planned'
    },
    {
      title: 'Training Center',
      description: 'Practice dungeon puzzles and improve your skills.',
      icon: '🧩',
      link: '/dungeons/training',
      status: 'Planned'
    }
  ];
</script>

<svelte:head>
  <title>Hypixel SkyBlock Dungeons | AltSky</title>
  <meta name="description" content="Hypixel SkyBlock Dungeons tools. Room explorer, profit calculator, and puzzle trainers." />
</svelte:head>

<div class="wrap">
  <div class="header">
    <a href="/" class="back-link">← Back to Home</a>
    <h1>Dungeons Hub</h1>
    <p class="subtitle">Master the Catacombs with our suite of dungeon tools.</p>
  </div>

  <div class="features-grid">
    {#each features as feature}
      <div class="feature-card">
        <div class="card-header">
          <span class="icon">{feature.icon}</span>
          <span class="status-badge">{feature.status}</span>
        </div>
        <h3>{feature.title}</h3>
        <p>{feature.description}</p>
        <a href={feature.link} class="card-link">Open Tool</a>
      </div>
    {/each}
  </div>
</div>

<style>
  .wrap {
    max-width: 960px;
    margin: 40px auto;
    padding: 0 18px;
    color: var(--theme-text-primary);
  }

  .header {
    margin-bottom: 40px;
  }

  .back-link {
    display: inline-block;
    margin-bottom: 16px;
    color: var(--theme-text-soft);
    text-decoration: none;
    font-size: 14px;
    transition: color 0.2s;
  }

  .back-link:hover {
    color: var(--theme-accent);
  }

  h1 {
    font-size: 42px;
    margin: 0 0 12px;
    background: linear-gradient(135deg, #fff 0%, #ccc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .subtitle {
    color: var(--theme-text-soft);
    font-size: 18px;
    margin: 0;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
  }

  .feature-card {
    background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    border-radius: 16px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    box-shadow: var(--neu-soft);
    backdrop-filter: blur(10px);
  }

  .feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
    border-color: color-mix(in srgb, var(--theme-accent) 40%, transparent);
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 16px;
  }

  .icon {
    font-size: 32px;
  }

  .status-badge {
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.1);
    color: var(--theme-text-soft);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  h3 {
    margin: 0 0 8px;
    font-size: 20px;
    color: var(--theme-text-primary);
  }

  p {
    margin: 0 0 20px;
    color: var(--theme-text-soft);
    line-height: 1.5;
    flex-grow: 1;
  }

  .card-link {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 10px 20px;
    background: var(--theme-accent);
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    transition: background 0.2s;
  }

  .card-link:hover {
    background: color-mix(in srgb, var(--theme-accent) 80%, black);
  }
</style>
