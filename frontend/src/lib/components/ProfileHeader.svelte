<script lang="ts">
  export let name = '';
  export let uuid = '';

  $: face = uuid ? `https://crafatar.com/avatars/${uuid}?size=64&overlay` : '';
</script>

<div class="wrap">
  {#if face}
    <img class="head" alt={name} src={face} />
  {/if}
  <div>
    <h1>{name}</h1>
    {#if uuid}
      <p class="uuid">{uuid}</p>
    {/if}
  </div>
</div>

<style>
  .wrap {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
  }

  .head {
    width: 64px;
    height: 64px;
    border-radius: 12px;
    border: 1px solid var(--theme-control-border);
    background: var(--theme-control-bg);
    box-shadow: var(--neu-elevated);
  }

  h1 {
    margin: 0;
    font-size: 2rem;
    color: var(--theme-text-primary);
  }

  .uuid {
    margin: 4px 0 0;
    color: var(--theme-text-soft);
    font-family: ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace;
    font-size: 0.8rem;
  }
</style>
