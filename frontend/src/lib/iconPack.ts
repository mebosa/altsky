import { writable } from 'svelte/store';

export type IconPackDefinition = {
	id: string;
	label: string;
	basePath: string;
	description?: string;
};

export const iconPackOptions: IconPackDefinition[] = [
	{
		id: 'vanilla',
		label: 'Vanilla',
		basePath: '/skills/vanilla',
		description: 'Classic Minecraft look'
	},
	{
		id: 'flufsky',
		label: 'Flufsky',
		basePath: '/skills/flufsky',
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

export function iconPath(pack: IconPackDefinition, key: string) {
	return `${pack.basePath}/${key}.png`;
}
