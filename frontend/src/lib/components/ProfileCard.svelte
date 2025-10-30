<script lang="ts">
  export let cuteName = "(unknown)";
  export let lastSave: number | undefined;
  export let purse: number | undefined;
  export let profileId: string | undefined;

  const fmtTime = (t?: number) =>
    t ? new Date(t).toLocaleString() : "-";

  const fmtNum = (n?: number) =>
    typeof n === "number" ? n.toLocaleString() : "-";
</script>

<div style="
  border:1px solid #e5e7eb;border-radius:16px;padding:16px;
  background:#fff;box-shadow:0 1px 2px rgba(0,0,0,.04);
">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <h3 style="margin:0;font-size:1.1rem">{cuteName}</h3>
    {#if profileId}
      <code style="font-size:.75rem;color:#6b7280">{profileId.slice(0,8)}…</code>
    {/if}
  </div>

  <div style="margin-top:.75rem;display:flex;gap:.5rem;flex-wrap:wrap">
    <StatChip label="마지막 저장" value={fmtTime(lastSave)} />
    <StatChip label="소지 골드" value={fmtNum(purse)} />
  </div>
</div>

<style>
  :global(body){background:#f8fafc;color:#111827;font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Apple SD Gothic Neo;}
</style>

<!-- deps -->
<svelte:head><link rel="preconnect" href="https://fonts.gstatic.com" /></svelte:head>
