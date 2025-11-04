import type { PageServerLoad } from './$types';
import { resolveApiBase } from '$lib/api';

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

export const load: PageServerLoad = async ({ params, fetch, url }) => {
  const apiBase = resolveApiBase({ url });
  const encodedName = encodeURIComponent(params.name).replace(/%20/g, '+');
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

  return {
    player,
    fetchError,
  };
};
