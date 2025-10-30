<script lang='ts'>
  export let name = '';
  export let uuid = '';
  const face = (uuid ? \https://crafatar.com/avatars/\?size=64&overlay\ : '');
</script>

<div class='wrap'>
  {#if uuid}<img class='head' alt={name} src={face} />{/if}
  <div>
    <h1>AltSky — {name}</h1>
    {#if uuid}<p class='uuid'>{uuid}</p>{/if}
  </div>
</div>

<style>
  .wrap{display:flex;gap:14px;align-items:center;margin-bottom:12px}
  .head{width:64px;height:64px;border-radius:10px;border:1px solid #e5e7eb;background:#f9fafb}
  h1{margin:0;font-size:32px}
  .uuid{margin:4px 0 0 0;color:#6b7280;font-family:ui-monospace, SFMono-Regular, Menlo, monospace;font-size:12px}
</style>