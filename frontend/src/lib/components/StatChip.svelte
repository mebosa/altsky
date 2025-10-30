<script lang="ts">
  export let label: string;
  export let value: string | number | undefined = "-";
</script>

<span style="
  display:inline-flex;align-items:center;gap:.4rem;
  padding:.25rem .6rem;border:1px solid #e5e7eb;border-radius:9999px;
  background:#fafafa;font-size:.9rem;
">
  <strong style="font-weight:600;color:#111827">{label}</strong>
  <span style="color:#374151">{value ?? "-"}</span>
</span>
