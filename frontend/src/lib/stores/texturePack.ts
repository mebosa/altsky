import { writable } from 'svelte/store';

export type TexturePack = 'vanilla' | 'furfsky';

export const texturePackStore = writable<TexturePack>('furfsky');