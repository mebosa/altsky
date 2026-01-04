<script lang='ts'>
  export let title = '';
</script>

<div class='card'>
  <h3>{title}</h3>
  <slot />
</div>

<style>
  .card {
    padding: 16px;
    border-radius: 16px;
    background: var(--theme-surface);
    box-shadow: var(--neu-elevated);
    color: var(--theme-text-primary);
  }
  h3 {
    margin: 0 0 12px 0;
    font-size: 1.1rem;
    color: var(--theme-text-primary);
    font-weight: 600;
  }
</style>