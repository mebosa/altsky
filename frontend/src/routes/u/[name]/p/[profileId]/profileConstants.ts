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
  health: 'Health',
  defense: 'Defense',
  strength: 'Strength',
  intelligence: 'Intelligence',
  speed: 'Speed',
  crit_chance: 'Crit Chance',
  crit_damage: 'Crit Damage',
  attack_speed: 'Attack Speed',
  ferocity: 'Ferocity',
  magic_find: 'Magic Find',
  pet_luck: 'Pet Luck',
  true_defense: 'True Defense'
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
