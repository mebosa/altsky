<script lang="ts">
  import type { ProfileSummaryResponse } from './profileTypes';
  
  export let summary: ProfileSummaryResponse;
</script>

<div class="card empty-card">
  <div class="empty-icon">⛏️</div>
  <h3>Heart of the Mountain</h3>
  <p>Hypixel API 변경으로 인해 현재 데이터를 불러올 수 없습니다.</p>
  <p class="sub-text">Data is currently unavailable due to Hypixel API changes.</p>
</div>

<style>
  .empty-card {
    padding: 60px 20px;
    text-align: center;
    background-color: rgba(30, 41, 59, 0.5); /* surface-800/50 */
    border-radius: 0.5rem;
    border: 1px solid rgba(51, 65, 85, 1); /* surface-700 */
  }

  .empty-icon {
    font-size: 4rem;
    margin-bottom: 16px;
    opacity: 0.4;
  }

  h3 {
    margin: 0 0 8px;
    color: #e2e8f0; /* surface-200 */
    font-size: 1.25rem;
    font-weight: bold;
  }

  p {
    margin: 0;
    color: #94a3b8; /* surface-400 */
  }

  .sub-text {
    font-size: 0.875rem;
    margin-top: 4px;
    opacity: 0.8;
  }
</style>
