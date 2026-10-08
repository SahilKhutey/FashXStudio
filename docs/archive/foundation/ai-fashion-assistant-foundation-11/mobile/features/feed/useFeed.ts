import { useInfiniteQuery } from "@tanstack/react-query";

import { getFeed, type FeedParams } from "../../api/feed";

export function useFeed(params: Omit<FeedParams, "cursor"> = {}) {
  return useInfiniteQuery({
    queryKey: ["feed", params],
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) => getFeed({ ...params, cursor: pageParam, limit: params.limit ?? 20 }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    staleTime: 30_000,
  });
}
