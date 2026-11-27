import { useCallback, useState } from "react";
import { fetchPersonalizedRanking } from "./rankingApi";
import type {
  RankedProductItem,
  RankingContextPayload,
} from "./ranking.types";

export function usePersonalizedRanking() {
  const [items, setItems] = useState<RankedProductItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (context: RankingContextPayload) => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetchPersonalizedRanking(context);
      setItems(resp.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load ranked products");
    } finally {
      setLoading(false);
    }
  }, []);

  return { items, loading, error, load };
}
