import { writable } from 'svelte/store';

export type IconCategoryPaths = {
	skills: string;
	slayer: string;
	dungeons: string;
};

export type IconCategory = keyof IconCategoryPaths;

export type IconPackDefinition = {
	id: string;
	label: string;
	paths: IconCategoryPaths;
	description?: string;
};

export const iconPackOptions: IconPackDefinition[] = [
	{
		id: 'vanilla',
		label: 'Vanilla',
		paths: {
			skills: '/icons/skills/vanilla',
			slayer: '/icons/slayer/vanilla',
			dungeons: '/icons/dungeons/vanilla'
		},
		description: 'Classic Minecraft look'
	},
	{
		id: 'flufsky',
		label: 'Flufsky',
		paths: {
			skills: '/icons/skills/flufsky',
			slayer: '/icons/slayer/flufsky',
			dungeons: '/icons/dungeons/flufsky'
		},
		description: 'Soft SkyBlock-style tint'
	}
];

const STORAGE_KEY = 'altsky_icon_pack';

type IconPackStore = {
	subscribe: typeof writable<IconPackDefinition>['subscribe'];
	init: () => void;
	select: (id: string) => void;
};

function createIconPackStore(): IconPackStore {
	const { subscribe, set } = writable<IconPackDefinition>(iconPackOptions[0]);
	let initialized = false;

	function apply(pack: IconPackDefinition, persist = true) {
		set(pack);
		if (persist && typeof window !== 'undefined') {
			window.localStorage.setItem(STORAGE_KEY, pack.id);
		}
	}

	function init() {
		if (initialized || typeof window === 'undefined') return;
		initialized = true;

		const storedId = window.localStorage.getItem(STORAGE_KEY);
		if (storedId) {
			const storedPack = iconPackOptions.find((pack) => pack.id === storedId);
			if (storedPack) {
				apply(storedPack, false);
				return;
			}
		}

		apply(iconPackOptions[0], false);
	}

	function select(id: string) {
		const pack = iconPackOptions.find((item) => item.id === id);
		if (!pack) return;
		apply(pack, true);
	}

	return { subscribe, init, select };
}

export const iconPack = createIconPackStore();

export function iconPath(pack: IconPackDefinition, key: string, category: IconCategory = 'skills') {
	return `${pack.paths[category]}/${key}.png`;
}
