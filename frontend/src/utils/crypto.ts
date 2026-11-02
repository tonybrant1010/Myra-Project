import { authedFetch } from "@/src/auth/AuthContext";


export async function startLeaderboardSession(
  token: string | null,
  gameType: "match" | "snake" | "sudoku",
  boardSize: 4 | 6 | 9 = 4,
): Promise<GameChallenge | null> {
  if (!token) return null;
  try {
    const res = await authedFetch(token, "/api/leaderboard/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ game_type: gameType, board_size: boardSize }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return typeof data?.session_token === "string" && data?.challenge ? data as GameChallenge : null;
  } catch {
    return null;
  }
}

type GameChallenge = {
  session_token: string;
  challenge: { seed: number; board_size: 4 | 6 | 9; puzzle?: number[][] };
};

export function seededRandom(seed: number): () => number {
  let state = seed || 1;
  return () => {
    state ^= state << 13;
    state ^= state >>> 17;
    state ^= state << 5;
    return (state >>> 0) / 4294967296;
  };
}
