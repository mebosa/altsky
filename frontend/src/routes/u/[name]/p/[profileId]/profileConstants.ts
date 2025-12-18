export const skillOrder = [
  { key: 'farming', label: 'Farming' },
  { key: 'mining', label: 'Mining' },
  { key: 'combat', label: 'Combat' },
  { key: 'foraging', label: 'Foraging' },
  { key: 'fishing', label: 'Fishing' },
  { key: 'enchanting', label: 'Enchanting' },
  { key: 'alchemy', label: 'Alchemy' },
  { key: 'taming', label: 'Taming' },
  { key: 'carpentry', label: 'Carpentry' },
  { key: 'runecrafting', label: 'Runecrafting' },
  { key: 'social', label: 'Social' }
] as const;

export const statLabels: Record<string, string> = {
  speed: 'Speed',
  strength: 'Strength',
  defense: 'Defense',
  crit_damage: 'Crit Damage',
  crit_chance: 'Crit Chance',
  health: 'Health',
  intelligence: 'Intelligence',
  bonus_attack_speed: 'Attack Speed',
  ferocity: 'Ferocity',
  magic_find: 'Magic Find',
  pet_luck: 'Pet Luck',
  true_defense: 'True Defense',
  sea_creature_chance: 'Sea Creature Chance',
  ability_damage: 'Ability Damage',
  mining_speed: 'Mining Speed',
  mining_fortune: 'Mining Fortune',
  farming_fortune: 'Farming Fortune',
  foraging_fortune: 'Foraging Fortune',
  pristine: 'Pristine',
  fishing_speed: 'Fishing Speed',
  health_regen: 'Health Regen',
  vitality: 'Vitality',
  mending: 'Mending',
  mana_regen: 'Mana Regen',
  alchemy_wisdom: 'Alchemy Wisdom',
  carpentry_wisdom: 'Carpentry Wisdom',
  combat_wisdom: 'Combat Wisdom',
  enchanting_wisdom: 'Enchanting Wisdom',
  farming_wisdom: 'Farming Wisdom',
  fishing_wisdom: 'Fishing Wisdom',
  foraging_wisdom: 'Foraging Wisdom',
  mining_wisdom: 'Mining Wisdom',
  runecrafting_wisdom: 'Runecrafting Wisdom',
  social_wisdom: 'Social Wisdom',
  taming_wisdom: 'Taming Wisdom',
  rift_time: 'Rift Time'
};

export const slayerLabels: Record<string, string> = {
  zombie: 'Revenant Horror',
  spider: 'Tarantula Broodfather',
  wolf: 'Sven Packmaster',
  enderman: 'Voidgloom Seraph',
  blaze: 'Inferno Demonlord',
  vampire: 'Riftstalker Bloodfiend'
};

export const dungeonClassLabels: Record<string, string> = {
  healer: 'Healer',
  mage: 'Mage',
  berserk: 'Berserk',
  archer: 'Archer',
  tank: 'Tank'
};
