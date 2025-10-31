import type { PageServerLoad } from './$types';
import { resolveApiBase } from '$lib/api';

type PlayerResponse = { name: string; uuid: string };

export const load: PageServerLoad = async ({ params, fetch, url }) => {
  const apiBase = resolveApiBase({ url });
  const name = params.name;
  const profileId = params.profileId;

  try {
    const playerRes = await fetch(`${apiBase}/api/player/${encodeURIComponent(name)}`);

    if (!playerRes.ok) {
      return {
        player: null,
        summary: null,
        errorMsg: `Failed to resolve player: ${playerRes.status}`
      };
    }

    const player = (await playerRes.json()) as PlayerResponse;

    const summaryRes = await fetch(
      `${apiBase}/api/hypixel/profile/${encodeURIComponent(player.uuid)}/${encodeURIComponent(profileId)}`
    );

    if (!summaryRes.ok) {
      let message = `Failed to load profile summary: ${summaryRes.status}`;
      try {
        const body = await summaryRes.json();
        if (body?.error) message = body.error;
      } catch {
        // ignore json parse errors
      }

      return {
        player,
        summary: null,
        errorMsg: message
      };
    }

    const summary = await summaryRes.json();

    return {
      player,
      summary,
      errorMsg: ''
    };
  } catch (err) {
    return {
      player: null,
      summary: null,
      errorMsg: `Unexpected error: ${(err as Error).message}`
    };
  }
};
