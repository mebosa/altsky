<script lang='ts'>
  export let label = '';
  export let value: string | number | null = null;
</script>

<div class='stat'>
  <div class='v'>{value ?? '-'}</div>
  <div class='l'>{label}</div>
</div>

<style>
  .stat{padding:14px 16px;border:1px solid #e5e7eb;border-radius:12px;background:#fff}
  .v{font-size:22px;font-weight:700}
  .l{font-size:12px;color:#6b7280;margin-top:2px}
</style>