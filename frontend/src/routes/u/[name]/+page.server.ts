import type { PageServerLoad } from './$types';
import { resolveApiBase } from '$lib/api';
import { Buffer } from 'node:buffer';
import { env } from '$env/dynamic/private';

type PlayerResponse = {
  name: string;
  uuid: string;
  profiles?: any[];
  last_updated?: string;
  error?: string;
  error_detail?: unknown;
  message?: string;
};

function deriveErrorMessage(body: unknown, status: number) {
  if (!body) return `Failed to load player: ${status}`;

  if (typeof body === 'string') {
    return body;
  }

  if (typeof body === 'object' && body !== null) {
    const message =
      typeof (body as { message?: unknown }).message === 'string'
        ? (body as { message?: string }).message
        : null;
    if (message) {
      return message;
    }

    const error =
      typeof (body as { error?: unknown }).error === 'string'
        ? (body as { error?: string }).error
        : null;
    if (error) {
      return error;
    }
  }

  return `Failed to load player: ${status}`;
}

function encodePreviewPayload(player: PlayerResponse | null): string | null {
  if (!player) return null;
  const payload = {
    name: player.name,
    uuid: player.uuid,
    last_updated: player.last_updated,
    profiles: (player.profiles ?? [])
      .slice(0, 3)
      .map((raw) => {
        const safe = raw ?? {};
        const membersCount =
          typeof safe?.member_count === 'number'
            ? safe.member_count
            : safe?.members
              ? Object.keys(safe.members as Record<string, unknown>).length
              : null;
        return {
          cute_name: safe?.cute_name ?? null,
          name: safe?.name ?? null,
          game_mode: safe?.game_mode ?? null,
          member_count: membersCount,
          last_save: safe?.last_save ?? safe?.last_save_iso ?? null,
        };
      }),
  };
  try {
    return Buffer.from(JSON.stringify(payload), 'utf8').toString('base64url');
  } catch (error) {
    console.error('Failed to serialize OG payload', error);
    return null;
  }
}

export const load: PageServerLoad = async ({ params, fetch, url }) => {
  const apiBase = resolveApiBase({ url });
  const encodedName = encodeURIComponent(params.name).replace(/%20/g, '+');
  const ogSafeName = encodeURIComponent(params.name);
  const trimmedBase = apiBase.replace(/\/+$/, '');
  const targetUrl = trimmedBase ? `${trimmedBase}/api/player/${encodedName}` : `/api/player/${encodedName}`;

  let player: PlayerResponse | null = null;
  let fetchError = '';

  try {
    const response = await fetch(targetUrl);
    let body: unknown = null;

    try {
      body = await response.json();
    } catch {
      body = null;
    }

    if (!response.ok) {
      fetchError = deriveErrorMessage(body, response.status);
      player = body && typeof body === 'object' ? (body as PlayerResponse) : null;
    } else {
      player = (body as PlayerResponse) ?? null;
    }
  } catch (err) {
    fetchError = `Failed to load player: ${(err as Error).message}`;
  }

  const previewPayload = encodePreviewPayload(player);
  const versionToken = player?.last_updated ?? Date.now().toString();
  const query = new URLSearchParams();
  if (previewPayload) {
    query.set('payload', previewPayload);
  }
  query.set('v', String(versionToken));
  const configuredOrigin = env.SITE_BASE?.trim();
  const requestOrigin = url.origin;
  const normalizedOrigin =
    configuredOrigin ||
    (requestOrigin.startsWith('http://altsky.') ? requestOrigin.replace('http://', 'https://') : requestOrigin);
  const ogImageUrl = `${normalizedOrigin}/api/og/player/${ogSafeName}.png?${query.toString()}`;

  return {
    player,
    fetchError,
    ogImageUrl,
    canonicalUrl: `${normalizedOrigin}/u/${ogSafeName}`,
  };
};
