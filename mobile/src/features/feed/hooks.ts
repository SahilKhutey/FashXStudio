import { useState, useRef, useEffect, useCallback } from "react";
import { AppState, AppStateStatus } from "react-native";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { components } from "../../api/schema";

export type FeedResponse = components["schemas"]["FeedResponse"];
export type FeedItem = components["schemas"]["FeedItemResponse"];
export type FeedSignalResponse = components["schemas"]["FeedSignalResponse"];
export type SignalAction = "like" | "hide" | "not_interested";

export function useFeed() {
  return useInfiniteQuery<FeedResponse, Error>({
    queryKey: ["feed"],
    initialPageParam: null as string | null,
    queryFn: async ({ pageParam }) => {
      const cursorParam = pageParam ? `?cursor=${encodeURIComponent(pageParam as string)}` : "";
      return api<FeedResponse>(`/feed${cursorParam}`);
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    staleTime: 60 * 1000,
  });
}

export interface PendingSignal {
  garmentId: string;
  action: SignalAction;
  timerId: any;
}

export function useSignal() {
  const queryClient = useQueryClient();
  const [pendingSignal, setPendingSignal] = useState<PendingSignal | null>(null);
  const pendingRef = useRef<PendingSignal | null>(null);

  const mutation = useMutation({
    mutationFn: async ({ garmentId, action }: { garmentId: string; action: SignalAction }) => {
      return api<FeedSignalResponse>("/feed/signals", {
        method: "POST",
        body: JSON.stringify({
          garment_id: garmentId,
          action,
        }),
      });
    },
    onSuccess: () => {
      // Invalidate feed when hide or not_interested was recorded
      queryClient.invalidateQueries({ queryKey: ["feed"] });
    },
  });

  const flushPending = useCallback(() => {
    if (pendingRef.current) {
      const { garmentId, action, timerId } = pendingRef.current;
      clearTimeout(timerId);
      mutation.mutate({ garmentId, action });
      pendingRef.current = null;
      setPendingSignal(null);
    }
  }, [mutation]);

  const sendSignal = useCallback(
    (garmentId: string, action: SignalAction, undoDelayMs = 5000) => {
      // If there's an ongoing pending signal, flush it immediately first
      if (pendingRef.current) {
        flushPending();
      }

      if (undoDelayMs <= 0) {
        mutation.mutate({ garmentId, action });
        return;
      }

      const timerId = setTimeout(() => {
        if (pendingRef.current && pendingRef.current.garmentId === garmentId) {
          mutation.mutate({ garmentId, action });
          pendingRef.current = null;
          setPendingSignal(null);
        }
      }, undoDelayMs);

      const pending: PendingSignal = { garmentId, action, timerId };
      pendingRef.current = pending;
      setPendingSignal(pending);
    },
    [flushPending, mutation]
  );

  const undoSignal = useCallback(() => {
    if (pendingRef.current) {
      clearTimeout(pendingRef.current.timerId);
      pendingRef.current = null;
      setPendingSignal(null);
    }
  }, []);

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (nextState: AppStateStatus) => {
      if (nextState === "background" || nextState === "inactive") {
        flushPending();
      }
    });

    return () => {
      subscription.remove();
      flushPending();
    };
  }, [flushPending]);

  return {
    sendSignal,
    undoSignal,
    pendingSignal,
    isPending: mutation.isPending,
  };
}

export function useImpressionTracker() {
  const seenGarmentsRef = useRef<Set<string>>(new Set());
  const pendingQueueRef = useRef<string[]>([]);
  const isFlushingRef = useRef<boolean>(false);

  const flushImpressions = useCallback(async () => {
    if (pendingQueueRef.current.length === 0 || isFlushingRef.current) {
      return;
    }

    const batch = [...pendingQueueRef.current];
    pendingQueueRef.current = [];
    isFlushingRef.current = true;

    try {
      await api<{ status: string; count: number }>("/analytics/session-events", {
        method: "POST",
        body: JSON.stringify({
          events: batch.map((garmentId) => ({
            event_type: "impression",
            garment_id: garmentId,
            timestamp: new Date().toISOString(),
          })),
        }),
      });
    } catch {
      // On failure, re-queue items that failed to be sent
      pendingQueueRef.current = [...batch, ...pendingQueueRef.current];
    } finally {
      isFlushingRef.current = false;
    }
  }, []);

  const recordImpression = useCallback((garmentId: string) => {
    if (!garmentId) return;
    if (seenGarmentsRef.current.has(garmentId)) return;

    seenGarmentsRef.current.add(garmentId);
    pendingQueueRef.current.push(garmentId);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      flushImpressions();
    }, 5000);

    const subscription = AppState.addEventListener("change", (nextState: AppStateStatus) => {
      if (nextState === "background" || nextState === "inactive") {
        flushImpressions();
      }
    });

    return () => {
      clearInterval(interval);
      subscription.remove();
      flushImpressions();
    };
  }, [flushImpressions]);

  return {
    recordImpression,
    flushImpressions,
  };
}
