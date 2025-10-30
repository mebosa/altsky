<script lang='ts'>
  export let title = '';
</script>

<div class='card'>
  <h3>{title}</h3>
  <slot />
</div>

<style>
  .card{padding:16px;border:1px solid #e5e7eb;border-radius:12px;background:#fff}
  h3{margin:0 0 8px 0;font-size:14px;color:#6b7280;font-weight:600}
</style>