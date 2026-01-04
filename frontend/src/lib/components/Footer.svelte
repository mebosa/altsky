<script lang="ts">
  const currentYear = new Date().getFullYear();
</script>

<footer class="footer">
  <div class="content">
    <div class="left">
      <div class="brand">
        <span class="logo-text">AltSky</span>
        <span class="version">v1.0</span>
      </div>
      <p class="copyright">© {currentYear} AltSky. Not affiliated with Hypixel.</p>
    </div>

    <div class="links">
      <a href="https://github.com/altsky/altsky" target="_blank" rel="noreferrer">GitHub</a>
      <a href="https://discord.gg/hypixel" target="_blank" rel="noreferrer">Discord</a>
      <a href="/about">About</a>
    </div>
  </div>
</footer>

<style>
  .footer {
    margin-top: auto;
    padding: 48px 24px;
    border-top: 1px solid var(--theme-border);
    background: var(--theme-surface);
    backdrop-filter: blur(12px);
  }

  .content {
    max-width: 960px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 24px;
  }

  .left {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .brand {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .logo-text {
    font-weight: 700;
    font-size: 1.1rem;
    color: var(--theme-text-primary);
  }

  .version {
    font-size: 0.8rem;
    color: var(--theme-text-secondary);
    font-family: monospace;
  }

  .copyright {
    font-size: 0.9rem;
    color: var(--theme-text-secondary);
    margin: 0;
  }

  .links {
    display: flex;
    gap: 24px;
  }

  .links a {
    color: var(--theme-text-secondary);
    text-decoration: none;
    font-size: 0.95rem;
    transition: color 0.2s;
  }

  .links a:hover {
    color: var(--theme-text-primary);
  }

  @media (max-width: 600px) {
    .content {
      flex-direction: column;
      align-items: flex-start;
    }
    
    .links {
      width: 100%;
      justify-content: flex-start;
    }
  }
</style>
