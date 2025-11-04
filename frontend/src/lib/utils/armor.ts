import type { ArmorPiece } from '$lib/types/armor';

export function getArmorTexturePath(armorType: string, piece: ArmorPiece, texturePack: string = 'vanilla'): string {
    return `/static/icons/armor/${texturePack}/${armorType}_${piece}.png`;
}