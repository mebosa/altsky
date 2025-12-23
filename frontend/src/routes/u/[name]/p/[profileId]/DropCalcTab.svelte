<script lang="ts">
  import { formatNumber } from '$lib/utils';
  import type { ProfileSummaryResponse } from './profileTypes';

  export let summary: ProfileSummaryResponse;

  // 사용자의 실제 스탯 가져오기
  $: computed = summary.computed_stats?.stats || summary.stats || {};
  $: userMagicFind = computed.magic_find ?? 0;
  $: userPetLuck = computed.pet_luck ?? 0;
  $: userLuck = computed.luck ?? 0;

  // 입력 값들
  let baseDropRateInput = '1'; // 사용자 입력용 (% 단위)
  let dropRateMode: 'percent' | 'fraction' = 'percent';
  let fractionNumerator = '1';
  let fractionDenominator = '100';

  // 스탯 입력 (기본값은 사용자 스탯)
  let magicFind: number | null = null;
  let petLuck: number | null = null;
  let looting = 0;
  let luck: number | null = null;

  // 실제 적용될 값 (null이면 유저 스탯 사용)
  $: effectiveMagicFind = magicFind ?? userMagicFind;
  $: effectivePetLuck = petLuck ?? userPetLuck;
  $: effectiveLuck = luck ?? userLuck;

  // 커스텀 배수 (일부 아이템은 특정 스탯만 적용)
  let magicFindMultiplier = 1;
  let petLuckMultiplier = 1;
  let lootingMultiplier = 1;
  let luckMultiplier = 1;

  // 드롭 타입 프리셋
  type DropType = 'normal' | 'pet' | 'rng' | 'bestiary' | 'custom';
  let dropType: DropType = 'normal';

  // 프리셋에 따른 배수 설정
  const presets: Record<DropType, { mf: number; pet: number; looting: number; luck: number; description: string }> = {
    normal: { mf: 1, pet: 0, looting: 1, luck: 1, description: 'Standard mob drops' },
    pet: { mf: 1, pet: 1, looting: 0, luck: 1, description: 'Pet drops (Pet Luck applies)' },
    rng: { mf: 1, pet: 0, looting: 0, luck: 0, description: 'RNG drops (MF only)' },
    bestiary: { mf: 0.5, pet: 0, looting: 1, luck: 0.5, description: 'Bestiary drops' },
    custom: { mf: 1, pet: 1, looting: 1, luck: 1, description: 'Custom settings' }
  };

  // 드롭 타입 변경 시 배수 업데이트
  function onDropTypeChange() {
    if (dropType !== 'custom') {
      const preset = presets[dropType];
      magicFindMultiplier = preset.mf;
      petLuckMultiplier = preset.pet;
      lootingMultiplier = preset.looting;
      luckMultiplier = preset.luck;
    }
  }

  // 기본 드롭률 계산
  let baseDropRate = 0.01;
  $: {
    if (dropRateMode === 'percent') {
      const parsed = parseFloat(baseDropRateInput);
      baseDropRate = isNaN(parsed) ? 0 : parsed / 100;
    } else {
      const num = parseFloat(fractionNumerator);
      const den = parseFloat(fractionDenominator);
      baseDropRate = (isNaN(num) || isNaN(den) || den === 0) ? 0 : num / den;
    }
  }

  // 최종 드롭 확률 계산
  $: totalBonus = 
    (effectiveMagicFind * magicFindMultiplier) + 
    (effectivePetLuck * petLuckMultiplier) + 
    (looting * 15 * lootingMultiplier) + 
    (effectiveLuck * luckMultiplier);

  $: effectiveRate = Math.min(baseDropRate * (1 + totalBonus / 100), 1);

  // 확률 표시 형식 변환
  function formatPercent(rate: number): string {
    if (rate === 0) return '0%';
    if (rate >= 1) return '100%';
    if (rate >= 0.01) return `${(rate * 100).toFixed(2)}%`;
    if (rate >= 0.0001) return `${(rate * 100).toFixed(4)}%`;
    return `${(rate * 100).toExponential(2)}%`;
  }

  function formatFraction(rate: number): string {
    if (rate === 0) return '0';
    if (rate >= 1) return '1/1';
    const denominator = Math.round(1 / rate);
    return `1/${denominator.toLocaleString()}`;
  }

  // 평균 시도 횟수
  $: avgTries = effectiveRate > 0 ? Math.ceil(1 / effectiveRate) : Infinity;

  // 특정 횟수 내 드롭 확률 계산
  let targetTries = 100;
  $: probabilityWithinTries = effectiveRate > 0 
    ? 1 - Math.pow(1 - effectiveRate, targetTries) 
    : 0;

  // 드롭률 증가량
  $: rateIncrease = effectiveRate > 0 && baseDropRate > 0
    ? ((effectiveRate / baseDropRate - 1) * 100).toFixed(1)
    : '0';

  // 스탯 리셋 함수
  function resetToUserStats() {
    magicFind = null;
    petLuck = null;
    luck = null;
    looting = 0;
  }
</script>

<section id="drop-calc" class="section">
  <h2>Drop Chance Calculator</h2>
  <p class="section-desc">Calculate effective drop rates with Magic Find, Pet Luck, Looting, and Luck.</p>

  <!-- User Stats Display -->
  <div class="user-stats-banner">
    <span class="banner-label">Your Stats:</span>
    <div class="stat-badges">
      <span class="stat-badge mf">✦ MF {formatNumber(userMagicFind)}</span>
      <span class="stat-badge pet">🐾 Pet Luck {formatNumber(userPetLuck)}</span>
      <span class="stat-badge luck">🍀 Luck {formatNumber(userLuck)}</span>
    </div>
    <button class="reset-btn" on:click={resetToUserStats}>Reset Stats</button>
  </div>

  <div class="calc-grid">
    <!-- Base Drop Rate Input -->
    <div class="calc-card">
      <h3>Base Drop Rate</h3>
      <div class="mode-toggle">
        <button 
          class:active={dropRateMode === 'percent'} 
          on:click={() => dropRateMode = 'percent'}
        >
          Percent
        </button>
        <button 
          class:active={dropRateMode === 'fraction'} 
          on:click={() => dropRateMode = 'fraction'}
        >
          Fraction
        </button>
      </div>

      {#if dropRateMode === 'percent'}
        <div class="input-group">
          <input 
            type="number" 
            bind:value={baseDropRateInput} 
            min="0" 
            max="100" 
            step="0.0001"
            placeholder="1"
          />
          <span class="unit">%</span>
        </div>
      {:else}
        <div class="fraction-input">
          <input 
            type="number" 
            bind:value={fractionNumerator} 
            min="1" 
            step="1"
            placeholder="1"
          />
          <span class="divider">/</span>
          <input 
            type="number" 
            bind:value={fractionDenominator} 
            min="1" 
            step="1"
            placeholder="100"
          />
        </div>
      {/if}
      <p class="hint">e.g. 1% = 1/100, 0.01% = 1/10000</p>
    </div>

    <!-- Drop Type Selection -->
    <div class="calc-card">
      <h3>Drop Type</h3>
      <div class="drop-types">
        {#each Object.entries(presets) as [key, preset]}
          <button 
            class="type-btn" 
            class:active={dropType === key}
            on:click={() => { dropType = key as DropType; onDropTypeChange(); }}
          >
            <span class="type-name">
              {#if key === 'normal'}Normal
              {:else if key === 'pet'}Pet
              {:else if key === 'rng'}RNG
              {:else if key === 'bestiary'}Bestiary
              {:else}Custom
              {/if}
            </span>
          </button>
        {/each}
      </div>
      <p class="hint">{presets[dropType].description}</p>
    </div>
  </div>

  <!-- Stat Inputs -->
  <div class="calc-card stats-card">
    <h3>Stat Inputs</h3>
    <div class="stats-grid">
      <div class="stat-input">
        <label>
          <span class="stat-icon mf">✦</span>
          Magic Find
        </label>
        <div class="input-row">
          <input 
            type="number" 
            value={magicFind ?? userMagicFind}
            on:input={(e) => magicFind = e.currentTarget.value ? parseFloat(e.currentTarget.value) : null}
            min="0" 
            step="1" 
            placeholder={String(userMagicFind)}
          />
          {#if dropType === 'custom'}
            <span class="multiplier">×</span>
            <input 
              type="number" 
              bind:value={magicFindMultiplier} 
              min="0" 
              max="2" 
              step="0.1"
              class="mult-input"
            />
          {:else}
            <span class="applied" class:zero={magicFindMultiplier === 0}>
              {magicFindMultiplier > 0 ? `×${magicFindMultiplier}` : 'N/A'}
            </span>
          {/if}
        </div>
      </div>

      <div class="stat-input">
        <label>
          <span class="stat-icon pet">🐾</span>
          Pet Luck
        </label>
        <div class="input-row">
          <input 
            type="number" 
            value={petLuck ?? userPetLuck}
            on:input={(e) => petLuck = e.currentTarget.value ? parseFloat(e.currentTarget.value) : null}
            min="0" 
            step="1" 
            placeholder={String(userPetLuck)}
          />
          {#if dropType === 'custom'}
            <span class="multiplier">×</span>
            <input 
              type="number" 
              bind:value={petLuckMultiplier} 
              min="0" 
              max="2" 
              step="0.1"
              class="mult-input"
            />
          {:else}
            <span class="applied" class:zero={petLuckMultiplier === 0}>
              {petLuckMultiplier > 0 ? `×${petLuckMultiplier}` : 'N/A'}
            </span>
          {/if}
        </div>
      </div>

      <div class="stat-input">
        <label>
          <span class="stat-icon looting">⚔</span>
          Looting Level
        </label>
        <div class="input-row">
          <input type="number" bind:value={looting} min="0" max="5" step="1" />
          {#if dropType === 'custom'}
            <span class="multiplier">×</span>
            <input 
              type="number" 
              bind:value={lootingMultiplier} 
              min="0" 
              max="2" 
              step="0.1"
              class="mult-input"
            />
          {:else}
            <span class="applied" class:zero={lootingMultiplier === 0}>
              {lootingMultiplier > 0 ? `×${lootingMultiplier}` : 'N/A'}
            </span>
          {/if}
        </div>
        <span class="stat-hint">+15% bonus per level</span>
      </div>

      <div class="stat-input">
        <label>
          <span class="stat-icon luck">🍀</span>
          Luck
        </label>
        <div class="input-row">
          <input 
            type="number" 
            value={luck ?? userLuck}
            on:input={(e) => luck = e.currentTarget.value ? parseFloat(e.currentTarget.value) : null}
            min="0" 
            step="1" 
            placeholder={String(userLuck)}
          />
          {#if dropType === 'custom'}
            <span class="multiplier">×</span>
            <input 
              type="number" 
              bind:value={luckMultiplier} 
              min="0" 
              max="2" 
              step="0.1"
              class="mult-input"
            />
          {:else}
            <span class="applied" class:zero={luckMultiplier === 0}>
              {luckMultiplier > 0 ? `×${luckMultiplier}` : 'N/A'}
            </span>
          {/if}
        </div>
      </div>
    </div>

    <div class="total-bonus">
      <span>Total Bonus:</span>
      <strong>+{totalBonus.toFixed(1)}%</strong>
    </div>
  </div>

  <!-- Results -->
  <div class="calc-card result-card">
    <h3>Results</h3>
    
    <div class="result-grid">
      <div class="result-item main">
        <span class="result-label">Effective Drop Rate</span>
        <span class="result-value big">{formatPercent(effectiveRate)}</span>
        <span class="result-sub">{formatFraction(effectiveRate)}</span>
      </div>

      <div class="result-item">
        <span class="result-label">vs Base Rate</span>
        <span class="result-value">+{rateIncrease}%</span>
      </div>

      <div class="result-item">
        <span class="result-label">Avg. Attempts</span>
        <span class="result-value">
          {avgTries === Infinity ? '∞' : avgTries.toLocaleString()}
        </span>
      </div>
    </div>

    <div class="probability-calc">
      <div class="prob-input">
        <input type="number" bind:value={targetTries} min="1" step="1" />
        <span>attempts</span>
      </div>
      <div class="prob-result">
        <span class="prob-value">{(probabilityWithinTries * 100).toFixed(2)}%</span>
        <span class="prob-desc">chance to drop at least once</span>
      </div>
    </div>
  </div>

  <!-- Info Panel -->
  <div class="calc-card info-card">
    <h3>💡 How It Works</h3>
    <ul>
      <li><strong>Magic Find</strong>: Applies to most drops, +1% per point</li>
      <li><strong>Pet Luck</strong>: Pet drops only, +1% per point</li>
      <li><strong>Looting</strong>: +15% bonus per enchant level</li>
      <li><strong>Luck</strong>: Some drops only, +1% per point</li>
      <li>Formula: <code>EffectiveRate = BaseRate × (1 + TotalBonus/100)</code></li>
    </ul>
  </div>
</section>

<style>
  .section {
    background: color-mix(in srgb, var(--theme-surface) 96%, transparent);
    border: 1px solid var(--theme-surface-border);
    border-radius: 18px;
    padding: 28px;
    box-shadow: var(--neu-elevated);
  }

  h2 {
    font-size: 1.4rem;
    margin: 0 0 6px;
    color: var(--theme-text-primary);
  }

  h3 {
    font-size: 1rem;
    margin: 0 0 14px;
    color: var(--theme-text-primary);
    font-weight: 600;
  }

  .section-desc {
    color: var(--theme-text-soft);
    margin: 0 0 20px;
    font-size: 0.9rem;
  }

  .user-stats-banner {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    padding: 14px 18px;
    background: color-mix(in srgb, var(--theme-accent) 10%, transparent);
    border: 1px solid color-mix(in srgb, var(--theme-accent) 30%, transparent);
    border-radius: 12px;
    margin-bottom: 20px;
  }

  .banner-label {
    color: var(--theme-text-soft);
    font-size: 0.9rem;
  }

  .stat-badges {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
  }

  .stat-badge {
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    background: color-mix(in srgb, var(--theme-surface) 80%, transparent);
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 60%, transparent);
  }

  .stat-badge.mf { color: #60a5fa; border-color: rgba(96, 165, 250, 0.3); }
  .stat-badge.pet { color: #f472b6; border-color: rgba(244, 114, 182, 0.3); }
  .stat-badge.luck { color: #4ade80; border-color: rgba(74, 222, 128, 0.3); }

  .reset-btn {
    margin-left: auto;
    padding: 8px 14px;
    border-radius: 8px;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    background: color-mix(in srgb, var(--theme-surface) 90%, transparent);
    color: var(--theme-text-soft);
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
  }

  .reset-btn:hover {
    background: color-mix(in srgb, var(--theme-accent) 15%, transparent);
    border-color: var(--theme-accent);
    color: var(--theme-accent);
  }

  .calc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 16px;
    margin-bottom: 16px;
  }

  .calc-card {
    padding: 18px;
    background: color-mix(in srgb, var(--theme-surface) 70%, transparent);
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 60%, transparent);
    border-radius: 14px;
  }

  .stats-card {
    margin-bottom: 16px;
  }

  .mode-toggle {
    display: flex;
    gap: 8px;
    margin-bottom: 14px;
  }

  .mode-toggle button {
    flex: 1;
    padding: 8px 14px;
    border-radius: 8px;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    background: color-mix(in srgb, var(--theme-form-bg) 92%, transparent);
    color: var(--theme-text-soft);
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
  }

  .mode-toggle button.active {
    background: color-mix(in srgb, var(--theme-accent) 20%, transparent);
    border-color: var(--theme-accent);
    color: var(--theme-accent);
  }

  .input-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .input-group input {
    flex: 1;
    padding: 10px 14px;
    font-size: 1rem;
    border: 1px solid color-mix(in srgb, var(--theme-form-border) 90%, transparent);
    border-radius: 10px;
    background: color-mix(in srgb, var(--theme-form-bg) 92%, #040915 8%);
    color: var(--theme-text-primary);
    box-shadow: var(--neu-inset);
  }

  .input-group input:focus {
    outline: none;
    border-color: var(--theme-accent);
  }

  .unit {
    font-size: 1rem;
    color: var(--theme-text-soft);
    font-weight: 600;
  }

  .fraction-input {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .fraction-input input {
    flex: 1;
    padding: 10px 14px;
    font-size: 1rem;
    text-align: center;
    border: 1px solid color-mix(in srgb, var(--theme-form-border) 90%, transparent);
    border-radius: 10px;
    background: color-mix(in srgb, var(--theme-form-bg) 92%, #040915 8%);
    color: var(--theme-text-primary);
    box-shadow: var(--neu-inset);
  }

  .fraction-input input:focus {
    outline: none;
    border-color: var(--theme-accent);
  }

  .divider {
    font-size: 1.2rem;
    color: var(--theme-text-soft);
  }

  .hint {
    margin: 10px 0 0;
    color: var(--theme-text-soft);
    font-size: 0.8rem;
  }

  .drop-types {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .type-btn {
    padding: 8px 14px;
    border-radius: 8px;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 80%, transparent);
    background: color-mix(in srgb, var(--theme-form-bg) 92%, transparent);
    color: var(--theme-text-primary);
    cursor: pointer;
    transition: all 0.2s;
    font-size: 0.85rem;
  }

  .type-btn:hover {
    border-color: var(--theme-accent);
  }

  .type-btn.active {
    background: color-mix(in srgb, var(--theme-accent) 18%, transparent);
    border-color: var(--theme-accent);
    color: var(--theme-accent);
  }

  .type-name {
    font-weight: 500;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 14px;
  }

  .stat-input {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .stat-input label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--theme-text-primary);
  }

  .stat-icon {
    font-size: 0.9rem;
  }

  .stat-icon.mf { color: #60a5fa; }
  .stat-icon.pet { color: #f472b6; }
  .stat-icon.looting { color: #fb923c; }
  .stat-icon.luck { color: #4ade80; }

  .input-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .input-row input {
    flex: 1;
    padding: 8px 12px;
    font-size: 0.9rem;
    border: 1px solid color-mix(in srgb, var(--theme-form-border) 90%, transparent);
    border-radius: 8px;
    background: color-mix(in srgb, var(--theme-form-bg) 92%, #040915 8%);
    color: var(--theme-text-primary);
    box-shadow: var(--neu-inset);
  }

  .input-row input:focus {
    outline: none;
    border-color: var(--theme-accent);
  }

  .mult-input {
    max-width: 60px;
  }

  .multiplier {
    color: var(--theme-text-soft);
    font-size: 0.8rem;
  }

  .applied {
    font-size: 0.75rem;
    color: var(--theme-accent);
    font-weight: 500;
    padding: 3px 8px;
    background: color-mix(in srgb, var(--theme-accent) 15%, transparent);
    border-radius: 5px;
    white-space: nowrap;
  }

  .applied.zero {
    color: var(--theme-text-soft);
    background: color-mix(in srgb, var(--theme-text-soft) 10%, transparent);
  }

  .stat-hint {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
  }

  .total-bonus {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 16px;
    padding: 12px 16px;
    background: color-mix(in srgb, var(--theme-accent) 10%, transparent);
    border-radius: 10px;
    border: 1px solid color-mix(in srgb, var(--theme-accent) 30%, transparent);
  }

  .total-bonus span {
    color: var(--theme-text-soft);
    font-size: 0.9rem;
  }

  .total-bonus strong {
    font-size: 1.2rem;
    color: var(--theme-accent);
  }

  .result-card {
    background: linear-gradient(
      135deg,
      color-mix(in srgb, var(--theme-accent) 8%, var(--theme-surface) 70%),
      color-mix(in srgb, var(--theme-surface) 80%, transparent)
    );
    margin-bottom: 16px;
  }

  .result-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 16px;
  }

  .result-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 16px;
    background: color-mix(in srgb, var(--theme-surface) 80%, transparent);
    border-radius: 12px;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 60%, transparent);
  }

  .result-item.main {
    background: color-mix(in srgb, var(--theme-accent) 12%, var(--theme-surface) 88%);
    border-color: color-mix(in srgb, var(--theme-accent) 40%, transparent);
  }

  .result-label {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
    margin-bottom: 6px;
  }

  .result-value {
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--theme-text-primary);
  }

  .result-value.big {
    font-size: 1.6rem;
    color: var(--theme-accent);
  }

  .result-sub {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    margin-top: 4px;
  }

  .probability-calc {
    padding: 14px;
    background: color-mix(in srgb, var(--theme-surface) 70%, transparent);
    border-radius: 10px;
    border: 1px solid color-mix(in srgb, var(--theme-surface-border) 60%, transparent);
  }

  .prob-input {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
  }

  .prob-input input {
    width: 80px;
    padding: 8px 12px;
    font-size: 0.9rem;
    text-align: center;
    border: 1px solid color-mix(in srgb, var(--theme-form-border) 90%, transparent);
    border-radius: 8px;
    background: color-mix(in srgb, var(--theme-form-bg) 92%, #040915 8%);
    color: var(--theme-text-primary);
  }

  .prob-input input:focus {
    outline: none;
    border-color: var(--theme-accent);
  }

  .prob-input span {
    color: var(--theme-text-soft);
    font-size: 0.85rem;
  }

  .prob-result {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .prob-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--theme-accent);
  }

  .prob-desc {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
  }

  .info-card {
    background: color-mix(in srgb, var(--theme-surface) 85%, transparent);
  }

  .info-card ul {
    margin: 0;
    padding-left: 18px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .info-card li {
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    line-height: 1.4;
  }

  .info-card li strong {
    color: var(--theme-text-primary);
  }

  .info-card code {
    background: color-mix(in srgb, var(--theme-accent) 15%, transparent);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.8rem;
    color: var(--theme-accent);
  }

  @media (max-width: 640px) {
    .section {
      padding: 20px;
    }

    .user-stats-banner {
      flex-direction: column;
      align-items: flex-start;
    }

    .reset-btn {
      margin-left: 0;
      width: 100%;
    }

    .stats-grid {
      grid-template-columns: 1fr;
    }

    .result-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
