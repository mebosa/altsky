import { writable, type Writable } from 'svelte/store';

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

const PACK_ID_ALIASES: Record<string, string> = {
	flufsky: 'furfsky'
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
		id: 'furfsky',
		label: 'Furfsky',
		paths: {
			skills: '/icons/skills/furfsky',
			slayer: '/icons/slayer/furfsky',
			dungeons: '/icons/dungeons/furfsky'
		},
		description: 'Furfsky Reborn-inspired UI set'
	}
];

const STORAGE_KEY = 'altsky_icon_pack';

type IconPackStore = {
	subscribe: Writable<IconPackDefinition>['subscribe'];
	init: () => void;
	select: (id: string) => void;
};

function createIconPackStore(): IconPackStore {
	const { subscribe, set } = writable<IconPackDefinition>(iconPackOptions[0]);
	let initialized = false;

	function resolvePack(id: string | null): IconPackDefinition | undefined {
		if (!id) return undefined;
		const normalized = PACK_ID_ALIASES[id] ?? id;
		return iconPackOptions.find((pack) => pack.id === normalized);
	}

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
		const storedPack = resolvePack(storedId);
		if (storedPack) {
			apply(storedPack, false);
			return;
		}

		apply(iconPackOptions[0], false);
	}

	function select(id: string) {
		const pack = resolvePack(id);
		if (!pack) return;
		apply(pack, true);
	}

	return { subscribe, init, select };
}

export const iconPack = createIconPackStore();

export function iconPath(pack: IconPackDefinition, key: string, category: IconCategory = 'skills') {
	return `${pack.paths[category]}/${key}.png`;
}
