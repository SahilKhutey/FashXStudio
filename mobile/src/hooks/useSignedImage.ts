import { useState, useEffect, useCallback, useMemo } from "react";

export interface UseSignedImageOptions {
  url?: string | null;
  expiresAt?: string | number | Date | null;
  refreshFn?: () => Promise<{ url: string; expiresAt?: string | number | Date | null }>;
  cacheKey?: string;
}

export interface UseSignedImageResult {
  uri: string | null;
  cacheKey: string | null;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

export function getStableCacheKey(url?: string | null, customKey?: string): string | null {
  if (customKey) return customKey;
  if (!url) return null;
  try {
    const base = url.split("?")[0]?.split("#")[0];
    return base || null;
  } catch {
    return url;
  }
}

export function useSignedImage(options: UseSignedImageOptions): UseSignedImageResult {
  const { url, expiresAt, refreshFn, cacheKey: customCacheKey } = options;

  const [currentUrl, setCurrentUrl] = useState<string | null>(url ?? null);
  const [currentExpiresAt, setCurrentExpiresAt] = useState<string | number | Date | null>(
    expiresAt ?? null
  );
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setCurrentUrl(url ?? null);
  }, [url]);

  useEffect(() => {
    setCurrentExpiresAt(expiresAt ?? null);
  }, [expiresAt]);

  const stableCacheKey = useMemo(
    () => getStableCacheKey(currentUrl, customCacheKey),
    [currentUrl, customCacheKey]
  );

  const refresh = useCallback(async () => {
    if (!refreshFn) return;
    try {
      setIsLoading(true);
      const res = await refreshFn();
      if (res?.url) {
        setCurrentUrl(res.url);
        if (res.expiresAt !== undefined) {
          setCurrentExpiresAt(res.expiresAt);
        }
      }
    } catch {
      // Retain existing URL on refresh failure
    } finally {
      setIsLoading(false);
    }
  }, [refreshFn]);

  useEffect(() => {
    if (!currentExpiresAt || !refreshFn) return;

    const expiryMs = new Date(currentExpiresAt).getTime();
    if (isNaN(expiryMs)) return;

    const msUntilRefresh = expiryMs - Date.now() - 60000; // Refresh 60s before expiry

    if (msUntilRefresh <= 0) {
      refresh();
      return;
    }

    const timer = setTimeout(() => {
      refresh();
    }, msUntilRefresh);

    return () => clearTimeout(timer);
  }, [currentExpiresAt, refreshFn, refresh]);

  return {
    uri: currentUrl,
    cacheKey: stableCacheKey,
    isLoading,
    refresh,
  };
}
