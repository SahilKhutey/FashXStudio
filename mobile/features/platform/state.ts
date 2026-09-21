import type { FeatureUiState } from "./types";

export const loadingState = <T>(): FeatureUiState<T> => ({ status: "loading" });

export const uninitializedState = <T>(): FeatureUiState<T> => ({ status: "uninitialized" });

export const initializingState = <T>(): FeatureUiState<T> => ({ status: "initializing" });

export const successState = <T>(data: T): FeatureUiState<T> => ({ status: "success", data });

export const emptyState = <T>(message: string, actionLabel?: string): FeatureUiState<T> => ({
  status: "empty",
  message,
  actionLabel,
});

export const errorState = <T>(message: string, retryable = true): FeatureUiState<T> => ({
  status: "error",
  message,
  retryable,
});

export const disabledState = <T>(message: string): FeatureUiState<T> => ({
  status: "disabled",
  message,
});
