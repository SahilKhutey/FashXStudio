import { useEffect, useState } from "react";

export type NetworkStatus = {
  connected: boolean;
  internetReachable: boolean | null;
  offline: boolean;
};

export function deriveNetworkStatus(
  connected: boolean,
  internetReachable: boolean | null,
): NetworkStatus {
  return {
    connected,
    internetReachable,
    offline: !connected || internetReachable === false,
  };
}

export function useNetworkStatus(): NetworkStatus {
  const initialOnline =
    typeof navigator !== "undefined" && typeof navigator.onLine === "boolean"
      ? navigator.onLine
      : true;

  const [status, setStatus] = useState<NetworkStatus>(() =>
    deriveNetworkStatus(initialOnline, initialOnline ? null : false),
  );

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.addEventListener !== "function") {
      return;
    }

    const handleOnline = () => setStatus(deriveNetworkStatus(true, true));
    const handleOffline = () => setStatus(deriveNetworkStatus(false, false));

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  return status;
}
