declare global {
	interface Window {
		skinview3d?: {
			SkinViewer: new (options: {
				canvas?: HTMLCanvasElement;
				width?: number;
				height?: number;
				skin?: string;
				model?: 'default' | 'slim' | 'auto-detect';
				zoom?: number;
				fov?: number;
				enableControls?: boolean;
			}) => {
				setSize: (width: number, height: number) => void;
				loadSkin: (skin: string | HTMLImageElement, options?: { model?: 'default' | 'slim' | 'auto-detect' }) => Promise<void> | void;
				loadCape: (cape: string | HTMLImageElement | null) => Promise<void> | void;
				dispose: () => void;
				controls: {
					enableZoom: boolean;
					enablePan: boolean;
					enableRotate: boolean;
				};
				autoRotate: boolean;
				autoRotateSpeed: number;
				zoom: number;
				fov: number;
			};
		};
	}
}

export type Skinview3d = NonNullable<Window['skinview3d']>;

let loadPromise: Promise<Skinview3d> | null = null;

export function loadSkinview3d(): Promise<Skinview3d> {
	if (typeof window === 'undefined') {
		return Promise.reject(new Error('skinview3d can only be loaded in the browser'));
	}

	if (window.skinview3d) return Promise.resolve(window.skinview3d);
	if (loadPromise) return loadPromise;

	loadPromise = new Promise<Skinview3d>((resolve, reject) => {
		const existing = document.querySelector<HTMLScriptElement>('script[data-skinview3d]');
		if (existing) {
			existing.addEventListener('load', () => {
				if (window.skinview3d) resolve(window.skinview3d);
				else reject(new Error('skinview3d script loaded but global not found'));
			});
			existing.addEventListener('error', () => reject(new Error('Failed to load skinview3d script')));
			return;
		}

		const script = document.createElement('script');
		script.dataset.skinview3d = '1';
		script.async = true;
		script.src = 'https://cdn.jsdelivr.net/npm/skinview3d@3.4.1/bundles/skinview3d.bundle.js';
		script.onload = () => {
			if (window.skinview3d) resolve(window.skinview3d);
			else reject(new Error('skinview3d script loaded but global not found'));
		};
		script.onerror = () => reject(new Error('Failed to load skinview3d script'));
		document.head.appendChild(script);
	});

	return loadPromise;
}
