import type { TryOnJobStatusResponse } from "./useTryOn";

export type TryOnStatus = TryOnJobStatusResponse["status"];

export function isTerminalTryOnStatus(status?: TryOnStatus): boolean {
  return (
    status === "completed" ||
    status === "failed" ||
    status === "cancelled"
  );
}

export function getTryOnPollInterval(
  elapsedMs: number,
  status?: TryOnStatus,
): number | false {
  if (isTerminalTryOnStatus(status)) return false;

  return elapsedMs >= 10 * 60 * 1000 ? 15_000 : 3_000;
}
