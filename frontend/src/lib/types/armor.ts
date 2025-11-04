export type ArmorPiece = 'helmet' | 'chestplate' | 'leggings' | 'boots';

export interface ArmorSet {
    type: string;
    pieces: {
        [key in ArmorPiece]: string;
    };
}