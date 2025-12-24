import type { PageServerLoad } from './$types';
import { resolveApiBase } from '$lib/api';

type PlayerResponse = { name: string; uuid: string };
type ProfileSummaryResponse = {
  ok: boolean;
  player: PlayerResponse;
  profile?: unknown;
  [key: string]: unknown;
};

export const load: PageServerLoad = async ({ params, fetch, url }) => {
  const apiBase = resolveApiBase({ url });
  const name = params.name;
  const profileId = params.profileId;

  try {
    // 단일 API 호출로 player + profile summary를 한 번에 가져옴
    // skip_stats=1, skip_museum=1로 SSR에서는 무거운 호출 생략 (빠른 초기 렌더링)
    // 클라이언트에서 필요할 때 추가 로드
    const summaryRes = await fetch(
      `${apiBase}/api/hypixel/profile-by-name/${encodeURIComponent(name)}/${encodeURIComponent(profileId)}?skip_stats=1&skip_museum=1`
    );

    if (!summaryRes.ok) {
      let message = `Failed to load profile: ${summaryRes.status}`;
      try {
        const body = (await summaryRes.json()) as {
          message?: unknown;
          detail?: unknown;
          error?: unknown;
          player?: PlayerResponse;
        };
        if (typeof body?.message === 'string' && body.message) {
          message = body.message;
        } else if (typeof body?.detail === 'string' && body.detail) {
          message = body.detail;
        } else if (typeof body?.error === 'string' && body.error) {
          message = body.error;
        }
        // player 정보가 있으면 포함
        if (body?.player) {
          return {
            player: body.player,
            summary: null,
            errorMsg: message
          };
        }
      } catch {
        // ignore json parse errors
      }

      return {
        player: null,
        summary: null,
        errorMsg: message
      };
    }

    const summary = (await summaryRes.json()) as ProfileSummaryResponse;
    const player = summary.player;

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
