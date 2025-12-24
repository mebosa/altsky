<script lang="ts">
  import type { ProfileSummaryResponse, Pet } from './profileTypes';
  import { formatNumber } from '$lib/utils';

  export let summary: ProfileSummaryResponse;

  $: pets = summary.pets ?? [];
  $: petScore = summary.pet_score ?? 0;
  $: activePet = pets.find((p) => p.active) ?? null;

  // Calculate Magic Find bonus from pet score based on SkyCrypt rewards
  function getMagicFindBonus(score: number): number {
    if (score >= 500) return 13;
    if (score >= 450) return 12;
    if (score >= 375) return 11;
    if (score >= 325) return 10;
    if (score >= 275) return 9;
    if (score >= 225) return 8;
    if (score >= 175) return 7;
    if (score >= 130) return 6;
    if (score >= 100) return 5;
    if (score >= 75) return 4;
    if (score >= 50) return 3;
    if (score >= 25) return 2;
    if (score >= 10) return 1;
    return 0;
  }

  $: magicFindBonus = getMagicFindBonus(petScore);
  $: sortedPets = [...pets].sort((a, b) => {
    // Active pet first
    if (a.active && !b.active) return -1;
    if (!a.active && b.active) return 1;
    // Then by rarity
    const rarityOrder = ['MYTHIC', 'LEGENDARY', 'EPIC', 'RARE', 'UNCOMMON', 'COMMON'];
    const aRarity = rarityOrder.indexOf(a.tier);
    const bRarity = rarityOrder.indexOf(b.tier);
    if (aRarity !== bRarity) return aRarity - bRarity;
    // Then by level
    return b.level - a.level;
  });

  // Group pets by rarity
  $: petsByRarity = sortedPets.reduce(
    (acc, pet) => {
      const tier = pet.tier || 'COMMON';
      if (!acc[tier]) acc[tier] = [];
      acc[tier].push(pet);
      return acc;
    },
    {} as Record<string, Pet[]>
  );

  const rarityOrder = ['MYTHIC', 'LEGENDARY', 'EPIC', 'RARE', 'UNCOMMON', 'COMMON'];
  const rarityColors: Record<string, string> = {
    COMMON: '#aaaaaa',
    UNCOMMON: '#55ff55',
    RARE: '#5555ff',
    EPIC: '#aa00aa',
    LEGENDARY: '#ffaa00',
    MYTHIC: '#ff55ff'
  };

  const rarityLabels: Record<string, string> = {
    COMMON: 'Common',
    UNCOMMON: 'Uncommon',
    RARE: 'Rare',
    EPIC: 'Epic',
    LEGENDARY: 'Legendary',
    MYTHIC: 'Mythic'
  };

  const rarityGradients: Record<string, string> = {
    COMMON: 'linear-gradient(135deg, rgba(170,170,170,0.15), rgba(170,170,170,0.05))',
    UNCOMMON: 'linear-gradient(135deg, rgba(85,255,85,0.15), rgba(85,255,85,0.05))',
    RARE: 'linear-gradient(135deg, rgba(85,85,255,0.15), rgba(85,85,255,0.05))',
    EPIC: 'linear-gradient(135deg, rgba(170,0,170,0.15), rgba(170,0,170,0.05))',
    LEGENDARY: 'linear-gradient(135deg, rgba(255,170,0,0.15), rgba(255,170,0,0.05))',
    MYTHIC: 'linear-gradient(135deg, rgba(255,85,255,0.15), rgba(255,85,255,0.05))'
  };

  // Pet texture data from SkyCrypt (texture hash for each pet type)
  // Format: type -> texture hash (without /head/ prefix)
  const petTextures: Record<string, string | Record<string, string>> = {
    ARMADILLO: 'c1eb6df4736ae24dd12a3d00f91e6e3aa7ade6bbefb0978afef2f0f92461018f',
    BAT: '382fc3f71b41769376a9e92fe3adbaac3772b999b219c9d6b4680ba9983e527',
    BLAZE: 'b78ef2e4cf2c41a2d14bfde9caff10219f5b1bf5b35a49eb51c6467882cb5f0',
    CHICKEN: '7f37d524c3eed171ce149887ea1dee4ed399904727d521865688ece3bac75e',
    HORSE: '36fcd3ec3bc84bafb4123ea479471f9d2f42d8fb9c5f11cf5f4e0d93226',
    JERRY: '822d8e751c8f2fd4c8942c44bdb2f5ca4d8ae8e575ed3eb34c18a86e93b',
    OCELOT: '5657cd5c2989ff97570fec4ddcdc6926a68a3393250c1be1f0b114a1db1',
    PIGMAN: '63d9cb6513f2072e5d4e426d70a5557bc398554c880d4e7b7ec8ef4945eb02f2',
    RABBIT: '117bffc1972acd7f3b4a8f43b5b6c7534695b8fd62677e0306b2831574b',
    FROG: '45852a95928897746012988fbd5dbaa1b7b7a5fb65157016f4ff3f245374c08',
    SHEEP: '64e22a46047d272e89a1cfa13e9734b7e12827e235c2012c1a95962874da0',
    SILVERFISH: 'da91dab8391af5fda54acd2c0b18fbd819b865e1a8f1d623813fa761e924540',
    WITHER_SKELETON: 'f5ec964645a8efac76be2f160d7c9956362f32b6517390c59c3085034f050cff',
    SKELETON_HORSE: '47effce35132c86ff72bcae77dfbb1d22587e94df3cbc2570ed17cf8973a',
    WOLF: 'dc3dd984bb659849bd52994046964c22725f717e986b12d548fd169367d494',
    ENDERMAN: '6eab75eaa5c9f2c43a0d23cfdce35f4df632e9815001850377385f7b2f039ce1',
    PHOENIX: '23aaf7b1a778949696cb99d4f04ad1aa518ceee256c72e5ed65bfa5c2d88d9e',
    MAGMA_CUBE: '38957d5023c937c4c41aa2412d43410bda23cf79a9f6ab36b76fef2d7c429',
    FLYING_FISH: { default: '40cd71fbbbbb66c7baf7881f415c64fa84f6504958a57ccdb8589252647ea', mythic: 'b0e2363c2d41a9d323ba625de8c0637063a36fe85a045de275a7b7739ded6051' },
    BLUE_WHALE: 'dab779bbccc849f88273d844e8ca2f3a67a1699cb216c0a11b44326ce2cc20',
    TIGER: 'fc42638744922b5fcf62cd9bf27eeab91b2e72d6c70e86cc5aa3883993e9d84',
    LION: '38ff473bd52b4db2c06f1ac87fe1367bce7574fac330ffac7956229f82efba1',
    PARROT: '5df4b3401a4d06ad66ac8b5c4d189618ae617f9c143071c8ac39a563cf4e4208',
    SNOWMAN: '11136616d8c4a87a54ce78a97b551610c2b2c8f6d410bc38b858f974b113b208',
    TURTLE: '212b58c841b394863dbcc54de1c2ad2648af8f03e648988c1f9cef0bc20ee23c',
    BEE: '7e941987e825a24ea7baafab9819344b6c247c75c54a691987cd296bc163c263',
    ENDER_DRAGON: 'aec3ff563290b13ff3bcc36898af7eaa988b6cc18dc254147f58374afe9b21b9',
    GUARDIAN: '221025434045bda7025b3e514b316a4b770c6faa4ba9adb4be3809526db77f9d',
    SQUID: '01433be242366af126da434b8735df1eb5b3cb2cede39145974e9c483607bac',
    GIRAFFE: '176b4e390f2ecdb8a78dc611789ca0af1e7e09229319c3a7aa8209b63b9',
    ELEPHANT: '7071a76f669db5ed6d32b48bb2dba55d5317d7f45225cb3267ec435cfa514',
    MONKEY: '13cf8db84807c471d7c6922302261ac1b5a179f96d1191156ecf3e1b1d3ca',
    SPIDER: 'cd541541daaff50896cd258bdbdd4cf80c3ba816735726078bfe393927e57f1',
    ENDERMITE: '5a1a0831aa03afb4212adcbb24e5dfaa7f476a1173fce259ef75a85855',
    GHOUL: '87934565bf522f6f4726cdfe127137be11d37c310db34d8c70253392b5ff5b',
    JELLYFISH: '913f086ccb56323f238ba3489ff2a1a34c0fdceeafc483acff0e5488cfd6c2f1',
    PIG: '621668ef7cb79dd9c22ce3d1f3f4cb6e2559893b6df4a469514e667c16aa4',
    ROCK: 'cb2b5d48e57577563aca31735519cb622219bc058b1f34648b67b8e71bc0fa',
    SKELETON: 'fca445749251bdd898fb83f667844e38a1dff79a1529f79a42447a0599310ea4',
    ZOMBIE: '56fc854bb84cf4b7697297973e02b79bc10698460b51a639c60e5e417734e11',
    DOLPHIN: 'cefe7d803a45aa2af1993df2544a28df849a762663719bfefc58bf389ab7f5',
    BABY_YETI: 'ab126814fc3fa846dad934c349628a7a1de5b415021a03ef4211d62514d5',
    MEGALODON: 'a94ae433b301c7fb7c68cba625b0bd36b0b14190f20e34a7c8ee0d9de06d53b9',
    GOLEM: '89091d79ea0f59ef7ef94d7bba6e5f17f2f7d4572c44f90f76c4819a714',
    HOUND: 'b7c8bef6beb77e29af8627ecdc38d86aa2fea7ccd163dc73c00f9f258f9a1457',
    TARANTULA: '8300986ed0a04ea79904f6ae53f49ed3a0ff5b1df62bba622ecbd3777f156df8',
    BLACK_CAT: 'e4b45cbaa19fe3d68c856cd3846c03b5f59de81a480eec921ab4fa3cd81317',
    SPIRIT: '8d9ccc670677d0cebaad4058d6aaf9acfab09abea5d86379a059902f2fe22655',
    GRIFFIN: '4c27e3cb52a64968e60c861ef1ab84e0a0cb5f07be103ac78da67761731f00c8',
    MITHRIL_GOLEM: 'c1b2dfe8ed5dffc5b1687bc1c249c39de2d8a6c3d90305c95f6d1a1a330a0b1',
    GRANDMA_WOLF: '4e794274c1bb197ad306540286a7aa952974f5661bccf2b725424f6ed79c7884',
    RAT: 'a8abb471db0ab78703011979dc8b40798a941f3a4dec3ec61cbeec2af8cffe8',
    BAL: 'c469ba2047122e0a2de3c7437ad3dd5d31f1ac2d27abde9f8841e1d92a8c5b75',
    SCATHA: 'df03ad96092f3f789902436709cdf69de6b727c121b3c2daef9ffa1ccaed186c',
    GOLDEN_DRAGON: '2e9f9b1fc014166cb46a093e5349b2bf6edd201b680d62e48dbf3af9b0459116',
    AMMONITE: 'a074a7bd976fe6aba1624161793be547d54c835cf422243a851ba09d1e650553',
    BINGO: 'd4cd9c707c7092d4759fe2b2b6a713215b6e39919ec4e7afb1ae2b6f8576674c',
    MOOSHROOM_COW: '2b52841f2fd589e0bc84cbabf9e1c27cb70cac98f8d6b3dd065e55a4dcb70d77',
    SNAIL: '50a9933a3b10489d38f6950c4e628bfcf9f7a27f8d84666f04f14d5374252972',
    KUUDRA: '1f0239fb498e5907ede12ab32629ee95f0064574a9ffdff9fc3a1c8e2ec17587',
    DROPLET_WISP: 'b412e70375ec99ee38ae94b30e9b10752d459662b54794dfe66fe6a183c672d3',
    FROST_WISP: '1d8ad9936d758c5ea30b0b7cc7c67c2bfcea829ecf2425c0b50fc92a26ae23d0',
    GLACIAL_WISP: '3e2018feebe1a99177b3cb196d4e44521268b4b3eb56e6419cb0253cdbf0456c',
    SUBZERO_WISP: '7a0eb37e58c942eca4d33ab44e26eb1910c783788510b0a53b6f4d18881e237e',
    REINDEER: 'a2df65c6fd19a58bee38252192ac7ce2cf1dc8632c3547a9228b6b697240d098',
    RIFT_FERRET: 'b6b11399448260185da1d17e54c984515faab6d8585f00972451ec2b43d46f94',
    EERIE: 'c3af70c6ff76ba48f24ee8a2063a5b50bbfabf409f4795248a292f8289f47c98',
    SLUG: '7a79d0fd677b54530961117ef84adc206e2cc5045c1344d61d776bf8ac2fe1ba',
    OWL: 'da3216da54e7368fb40b721239ad95e07ef4f97d93f1c42ff319bab9a53882af',
    TYRANNOSAURUS: '93f28ec96df59c67e9d2fc2e7e3d055fa31646e4111add9fe26a692801964126',
    SPINOSAURUS: 'd3c9d479471a2f13f22548315159591720992e70c920fef83a901b7186720e3c',
    GOBLIN: '7309d8dc35a638a04b915a3b15a1452ceeae0d7ea42bcdadb21b03046987515c',
    ANKYLOSAURUS: 'c1aa836b9096c417903299a6c5ab41738c19648ac439fed4bcbe6c32605338dc',
    PENGUIN: '37534e97f36e5a8335928e171ec99608bee7fb16e260afb301025b3b17eeefc4',
    MAMMOTH: '6b10715732cd1fd49fa1b6187947c307dd4687105cf033840607f9d6234743ad',
    MOLE: '727baaafc09978d4bda73e16afdde85ec13b0f95ad989524c5fcaa717cf06b4a',
    GLACITE_GOLEM: 'af132a6593876d3c377d503fd66eca3fb938743251f7b16a9870c60b7388c8a3',
  };

  // Pet skins data (skin name -> texture hash)
  const petSkins: Record<string, string> = {
    ENDERMAN_SLAYER: '2e9f9b1fc014166cb46a093e5349b2bf6edd201b680d62e48dbf3af9b0459116',
    WOLF_GOLDEN: 'b4a0f3a3c6b8e7d9c2e1f0a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4',
    // Add more skins as needed
  };

  // Pet max levels (default 100, except special cases)
  const petMaxLevels: Record<string, number> = {
    GOLDEN_DRAGON: 200,
  };

  // Get max level for a pet type
  function getPetMaxLevel(petType: string): number {
    return petMaxLevels[petType] || 100;
  }

  // Check if pet is at max level
  function isPetMaxed(pet: Pet): boolean {
    return pet.level >= getPetMaxLevel(pet.type);
  }

  // Format pet name from type
  function formatPetName(type: string): string {
    return type
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  }

  // Get pet texture URL from local server
  function getPetTextureUrl(pet: Pet): string {
    // Check for pet skin first
    if (pet.skin && petSkins[pet.skin]) {
      // Pet skins still use mc-heads.net for now
      return `https://mc-heads.net/head/${petSkins[pet.skin]}`;
    }
    
    const texture = petTextures[pet.type];
    
    if (typeof texture === 'object') {
      // Handle pets with rarity-specific textures (e.g., FLYING_FISH)
      const suffix = pet.tier.toLowerCase() === 'mythic' ? '_mythic' : '';
      return `/pets/${pet.type.toLowerCase()}${suffix}.png`;
    } else if (texture) {
      // Use local server image
      return `/pets/${pet.type.toLowerCase()}.png`;
    } else {
      // Fallback - return empty to use fallback display
      return '';
    }
  }

  // Count stats
  $: totalPets = pets.length;
  $: uniquePetTypes = new Set(pets.map((p) => p.type)).size;
  $: maxLevelPets = pets.filter((p) => isPetMaxed(p)).length;
  $: rarityCounts = rarityOrder.reduce(
    (acc, rarity) => {
      acc[rarity] = pets.filter((p) => p.tier === rarity).length;
      return acc;
    },
    {} as Record<string, number>
  );

  // Handle image load error - try mc-heads.net fallback, then show text fallback
  function handleImageError(event: Event) {
    const img = event.target as HTMLImageElement;
    const petType = img.dataset.petType || img.alt;
    const currentSrc = img.src;
    
    // If currently loading from local, try mc-heads.net
    if (!currentSrc.includes('mc-heads.net') && !currentSrc.includes('sky.shiiyu.moe')) {
      const texture = petTextures[petType];
      const hash = typeof texture === 'string' ? texture : (texture as Record<string, string>)?.default;
      if (hash) {
        console.warn(`Local pet texture failed for ${petType}, trying mc-heads.net`);
        img.src = `https://mc-heads.net/head/${hash}`;
        return;
      }
    }
    
    // If mc-heads.net also failed, show text fallback
    console.warn(`Failed to load pet texture: ${petType} from ${currentSrc}`);
    img.style.display = 'none';
    const parent = img.parentElement;
    if (parent) {
      const fallback = parent.querySelector('.pet-fallback');
      if (fallback) {
        (fallback as HTMLElement).style.display = 'flex';
      }
    }
  }

  // Scroll to rarity section
  function scrollToRarity(rarity: string) {
    const element = document.getElementById(`rarity-${rarity.toLowerCase()}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }
</script>

<div class="pets-container">
  <!-- Overview Stats -->
  <div class="overview-section">
    <h2>🐾 Pets Collection</h2>
    <div class="stats-row">
      <div class="stat-card total">
        <div class="stat-icon">🎯</div>
        <div class="stat-content">
          <div class="stat-value">{petScore}</div>
          <div class="stat-label">Pet Score</div>
          <div class="stat-sub">Magic Find bonus: +{magicFindBonus}</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📦</div>
        <div class="stat-content">
          <div class="stat-value">{totalPets}</div>
          <div class="stat-label">Total Pets</div>
          <div class="stat-sub">{uniquePetTypes} unique types</div>
        </div>
      </div>

      <div class="stat-card maxed">
        <div class="stat-icon">⭐</div>
        <div class="stat-content">
          <div class="stat-value">{maxLevelPets}</div>
          <div class="stat-label">Max Level Pets</div>
          <div class="stat-sub">{totalPets > 0 ? Math.round((maxLevelPets / totalPets) * 100) : 0}% maxed</div>
        </div>
      </div>
    </div>

    <!-- Rarity Distribution -->
    <div class="rarity-distribution">
      {#each rarityOrder as rarity}
        {@const count = rarityCounts[rarity] || 0}
        {#if count > 0}
          <button 
            class="rarity-chip" 
            style="--rarity-color: {rarityColors[rarity]}"
            on:click={() => scrollToRarity(rarity)}
            title="Click to scroll to {rarityLabels[rarity]} pets"
          >
            <span class="rarity-dot"></span>
            <span class="rarity-name">{rarityLabels[rarity]}</span>
            <span class="rarity-count">{count}</span>
          </button>
        {/if}
      {/each}
    </div>
  </div>

  <!-- Active Pet Highlight -->
  {#if activePet}
    <div class="active-pet-section">
      <div class="active-pet-card" style="--rarity-color: {rarityColors[activePet.tier]}; --rarity-bg: {rarityGradients[activePet.tier]}">
        <div class="active-badge">🌟 Active Pet</div>
        <div class="active-pet-content">
          <div class="active-pet-icon">
            {#if petTextures[activePet.type]}
              <img 
                src={getPetTextureUrl(activePet)} 
                alt={formatPetName(activePet.type)}
                class="pet-texture"
                loading="lazy"
                on:error={handleImageError}
              />
              <span class="pet-fallback" style="display: none;">🐾</span>
            {:else}
              <span class="pet-fallback">🐾</span>
            {/if}
          </div>
          <div class="active-pet-info">
            <div class="active-pet-name">{formatPetName(activePet.type)}</div>
            <div class="active-pet-details">
              <span class="active-pet-rarity" style="color: {rarityColors[activePet.tier]}">{rarityLabels[activePet.tier]}</span>
              <span class="active-pet-level">Level {activePet.level}</span>
            </div>
            <div class="active-pet-xp">
              {formatNumber(activePet.xp)} XP
              {#if activePet.candy_used && activePet.candy_used > 0}
                <span class="candy-badge">🍬 {activePet.candy_used}</span>
              {/if}
            </div>
            {#if activePet.held_item}
              <div class="held-item">
                <span class="held-item-icon">📿</span>
                <span>{activePet.held_item.replace(/_/g, ' ')}</span>
              </div>
            {/if}
          </div>
        </div>
        <div class="active-pet-level-bar">
          <div class="level-fill" style="width: {activePet.level}%"></div>
        </div>
      </div>
    </div>
  {/if}

  <!-- Pets by Rarity -->
  {#each rarityOrder as rarity}
    {@const petsInRarity = petsByRarity[rarity] || []}
    {#if petsInRarity.length > 0}
      <div class="rarity-section" id="rarity-{rarity.toLowerCase()}">
        <div class="rarity-header" style="--rarity-color: {rarityColors[rarity]}">
          <span class="rarity-indicator"></span>
          <h3>{rarityLabels[rarity]}</h3>
          <span class="pet-count">{petsInRarity.length} pets</span>
        </div>

        <div class="pets-grid">
          {#each petsInRarity as pet}
            <div
              class="pet-card"
              class:active={pet.active}
              class:maxed={isPetMaxed(pet)}
              style="--rarity-color: {rarityColors[pet.tier]}; --rarity-bg: {rarityGradients[pet.tier]}"
            >
              <div class="pet-icon-wrapper">
                {#if petTextures[pet.type]}
                  <img 
                    src={getPetTextureUrl(pet)} 
                    alt={formatPetName(pet.type)}
                    class="pet-texture-small"
                    loading="lazy"
                    on:error={handleImageError}
                  />
                  <span class="pet-fallback" style="display: none;">🐾</span>
                {:else}
                  <span class="pet-fallback">🐾</span>
                {/if}
                {#if isPetMaxed(pet)}
                  <span class="max-badge">✨</span>
                {/if}
                {#if pet.active}
                  <span class="active-indicator"></span>
                {/if}
              </div>
              <div class="pet-info">
                <div class="pet-name">{formatPetName(pet.type)}</div>
                <div class="pet-level">
                  <span class="level-text">Lv. {pet.level}</span>
                  {#if pet.skin}
                    <span class="skin-badge" title="Has skin">🎨</span>
                  {/if}
                </div>
                <div class="pet-xp">{formatNumber(pet.xp)} XP</div>
              </div>
              <div class="pet-level-bar">
                <div class="level-fill" style="width: {pet.level}%"></div>
              </div>
              {#if pet.held_item}
                <div class="pet-held-item" title={pet.held_item.replace(/_/g, ' ')}>
                  📿
                </div>
              {/if}
              {#if pet.candy_used && pet.candy_used > 0}
                <div class="candy-indicator" title="{pet.candy_used} candy used">
                  🍬 {pet.candy_used}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/each}

  {#if pets.length === 0}
    <div class="empty-state">
      <span class="empty-icon">🐾</span>
      <p>No pets found in this profile</p>
    </div>
  {/if}
</div>

<style>
  .pets-container {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  h2 {
    margin: 0 0 16px;
    font-size: 1.5rem;
    color: var(--theme-text-primary);
  }

  h3 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 600;
  }

  /* Overview Section */
  .overview-section {
    background: var(--theme-surface-bg);
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    padding: 20px;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 16px;
  }

  .stat-card {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    background: rgba(148, 163, 184, 0.06);
    border: 1px solid var(--theme-surface-border);
    border-radius: 12px;
    padding: 16px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .stat-card.total {
    background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 170, 0, 0.05));
    border-color: rgba(255, 215, 0, 0.3);
  }

  .stat-card.maxed {
    background: linear-gradient(135deg, rgba(255, 215, 0, 0.08), rgba(255, 170, 0, 0.03));
  }

  .stat-icon {
    font-size: 2rem;
    line-height: 1;
  }

  .stat-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .stat-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--theme-text-primary);
    line-height: 1;
  }

  .stat-label {
    font-size: 0.9rem;
    color: var(--theme-text-soft);
    font-weight: 500;
  }

  .stat-sub {
    font-size: 0.8rem;
    color: var(--theme-text-soft);
    opacity: 0.75;
  }

  /* Rarity Distribution */
  .rarity-distribution {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .rarity-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: 20px;
    background: rgba(148, 163, 184, 0.08);
    border: 1px solid var(--rarity-color);
    font-size: 0.85rem;    cursor: pointer;
    transition: all 0.2s ease;
  }

  .rarity-chip:hover {
    background: rgba(148, 163, 184, 0.15);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .rarity-chip:active {
    transform: translateY(0);  }

  .rarity-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--rarity-color);
  }

  .rarity-name {
    color: var(--rarity-color);
    font-weight: 500;
  }

  .rarity-count {
    background: var(--rarity-color);
    color: #000;
    padding: 2px 8px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.75rem;
  }

  /* Active Pet Section */
  .active-pet-section {
    width: 100%;
  }

  .active-pet-card {
    background: var(--rarity-bg);
    border: 2px solid var(--rarity-color);
    border-radius: 20px;
    padding: 24px;
    position: relative;
    overflow: hidden;
  }

  .active-pet-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: var(--rarity-color);
  }

  .active-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 16px;
    background: var(--rarity-color);
    color: #000;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.85rem;
    margin-bottom: 16px;
  }

  .active-pet-content {
    display: flex;
    gap: 24px;
    align-items: center;
  }

  .active-pet-icon {
    width: 100px;
    height: 100px;
    border-radius: 20px;
    background: rgba(0, 0, 0, 0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid var(--rarity-color);
    overflow: hidden;
    position: relative;
  }

  .pet-texture {
    width: 80px;
    height: 80px;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .pet-texture-small {
    width: 48px;
    height: 48px;
    object-fit: contain;
    image-rendering: pixelated;
  }

  .pet-fallback {
    font-size: 2.5rem;
    align-items: center;
    justify-content: center;
  }

  .active-pet-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .active-pet-name {
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--theme-text-primary);
  }

  .active-pet-details {
    display: flex;
    gap: 16px;
    align-items: center;
  }

  .active-pet-rarity {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .active-pet-level {
    font-size: 1.1rem;
    color: var(--theme-text-primary);
    font-weight: 600;
  }

  .active-pet-xp {
    display: flex;
    align-items: center;
    gap: 12px;
    color: var(--theme-text-soft);
  }

  .candy-badge {
    background: rgba(255, 105, 180, 0.2);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.8rem;
    color: #ff69b4;
  }

  .held-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: rgba(148, 163, 184, 0.1);
    border-radius: 12px;
    font-size: 0.9rem;
    color: var(--theme-text-soft);
    width: fit-content;
    text-transform: capitalize;
  }

  .active-pet-level-bar {
    margin-top: 16px;
    height: 8px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 4px;
    overflow: hidden;
  }

  .level-fill {
    height: 100%;
    background: var(--rarity-color);
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  /* Rarity Section */
  .rarity-section {
    background: var(--theme-surface-bg);
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    padding: 20px;
  }

  .rarity-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }

  .rarity-indicator {
    width: 4px;
    height: 24px;
    background: var(--rarity-color);
    border-radius: 2px;
  }

  .rarity-header h3 {
    color: var(--rarity-color);
  }

  .pet-count {
    margin-left: auto;
    font-size: 0.85rem;
    color: var(--theme-text-soft);
    padding: 4px 12px;
    background: rgba(148, 163, 184, 0.08);
    border-radius: 12px;
  }

  /* Pets Grid */
  .pets-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 16px;
  }

  .pet-card {
    position: relative;
    background: var(--rarity-bg);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 16px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    transition: all 0.2s ease;
    cursor: default;
  }

  .pet-card:hover {
    transform: translateY(-4px);
    border-color: var(--rarity-color);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  .pet-card.active {
    border-color: var(--rarity-color);
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
  }

  .pet-card.maxed {
    background: linear-gradient(135deg, var(--rarity-bg), rgba(255, 215, 0, 0.08));
  }

  .pet-icon-wrapper {
    position: relative;
    width: 64px;
    height: 64px;
    border-radius: 16px;
    background: rgba(0, 0, 0, 0.15);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid rgba(148, 163, 184, 0.15);
    overflow: hidden;
  }

  .max-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    font-size: 1rem;
    animation: sparkle 1.5s infinite;
  }

  @keyframes sparkle {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.1); }
  }

  .active-indicator {
    position: absolute;
    bottom: -4px;
    left: 50%;
    transform: translateX(-50%);
    width: 12px;
    height: 12px;
    background: #ffd700;
    border-radius: 50%;
    border: 2px solid var(--theme-surface-bg);
    box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
  }

  .pet-info {
    text-align: center;
    width: 100%;
  }

  .pet-name {
    font-weight: 600;
    color: var(--theme-text-primary);
    font-size: 0.95rem;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .pet-level {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    font-size: 0.85rem;
    color: var(--rarity-color);
    font-weight: 600;
  }

  .skin-badge {
    font-size: 0.75rem;
  }

  .pet-xp {
    font-size: 0.75rem;
    color: var(--theme-text-soft);
  }

  .pet-level-bar {
    width: 100%;
    height: 4px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 2px;
    overflow: hidden;
  }

  .pet-held-item {
    position: absolute;
    top: 8px;
    right: 8px;
    font-size: 0.9rem;
    opacity: 0.8;
  }

  .candy-indicator {
    position: absolute;
    bottom: 8px;
    right: 8px;
    font-size: 0.7rem;
    background: rgba(255, 105, 180, 0.2);
    padding: 2px 6px;
    border-radius: 8px;
    color: #ff69b4;
  }

  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    background: var(--theme-surface-bg);
    border: 1px solid var(--theme-surface-border);
    border-radius: 16px;
    color: var(--theme-text-soft);
  }

  .empty-icon {
    font-size: 4rem;
    opacity: 0.3;
    margin-bottom: 16px;
  }

  .empty-state p {
    margin: 0;
    font-size: 1.1rem;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .active-pet-content {
      flex-direction: column;
      text-align: center;
    }

    .active-pet-info {
      align-items: center;
    }

    .stats-row {
      grid-template-columns: 1fr;
    }

    .pets-grid {
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    }
  }
</style>
