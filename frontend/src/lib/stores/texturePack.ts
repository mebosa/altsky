import { derived, type Readable } from 'svelte/store';
import { iconPack, type IconPackDefinition } from '$lib/iconPack';

export type TexturePack = 'vanilla' | 'furfsky';

const ICON_TO_TEXTURE: Record<string, TexturePack> = {
	vanilla: 'vanilla',
	furfsky: 'furfsky'
};

const DEFAULT_TEXTURE: TexturePack = 'furfsky';

const iconPackReadable: Readable<IconPackDefinition> = iconPack;

export const texturePackStore = derived(iconPackReadable, ($iconPack) => {
	return ICON_TO_TEXTURE[$iconPack.id] ?? DEFAULT_TEXTURE;
});