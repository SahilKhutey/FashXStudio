/**
 * FashXStudio — Interaction & UI State Machine Engine
 * Phase 01: Visual Product Architecture
 */

import { InteractionState, UiStateEnvelope } from "./types";

export const INTERACTION_STATES: InteractionState[] = [
  "default",
  "hover",
  "focus",
  "active",
  "selected",
  "disabled",
  "loading",
  "success",
  "warning",
  "error",
  "empty",
  "offline",
];

export function createInitialState<T>(initialData: T | null = null): UiStateEnvelope<T> {
  return {
    state: "default",
    data: initialData,
    errorMessage: null,
    errorTraceId: null,
    isRetryable: false,
  };
}

export function createLoadingState<T>(previousData: T | null = null): UiStateEnvelope<T> {
  return {
    state: "loading",
    data: previousData,
    errorMessage: null,
    errorTraceId: null,
    isRetryable: false,
  };
}

export function createSuccessState<T>(data: T): UiStateEnvelope<T> {
  return {
    state: "success",
    data,
    errorMessage: null,
    errorTraceId: null,
    isRetryable: false,
  };
}

export function createEmptyState<T>(title = "No items discovered", actionLabel?: string): UiStateEnvelope<T> {
  return {
    state: "empty",
    data: null,
    errorMessage: null,
    errorTraceId: null,
    isRetryable: false,
    emptyTitle: title,
    emptyActionLabel: actionLabel,
  };
}

export function createErrorState<T>(
  error: Error | string | { detail?: string; trace_id?: string },
  isRetryable = true,
  fallbackData: T | null = null
): UiStateEnvelope<T> {
  let message = "An unexpected error occurred.";
  let traceId: string | null = null;

  if (typeof error === "string") {
    message = error;
  } else if (error instanceof Error) {
    message = error.message;
  } else if (error && typeof error === "object") {
    message = error.detail || message;
    traceId = error.trace_id || null;
  }

  return {
    state: "error",
    data: fallbackData,
    errorMessage: message,
    errorTraceId: traceId,
    isRetryable,
  };
}

export function createOfflineState<T>(cachedData: T | null = null): UiStateEnvelope<T> {
  return {
    state: "offline",
    data: cachedData,
    errorMessage: "Device is currently offline. Viewing cached items.",
    errorTraceId: null,
    isRetryable: true,
  };
}

export function isValidStateTransition(fromState: InteractionState, toState: InteractionState): boolean {
  if (fromState === toState) return true;
  if (fromState === "disabled") {
    return toState === "default";
  }
  return true;
}
