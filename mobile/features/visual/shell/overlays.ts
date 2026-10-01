/**
 * FashXStudio — Overlay & Toast Manager (Phase 03)
 *
 * Centralized global overlay stack and toast queue management
 * (Sections 3.21, 3.22). Prevents z-index conflicts, duplicated focus
 * trapping, and inconsistent transition behavior.
 */

import type { Overlay, OverlayRegistry, OverlayType, Toast, ToastType } from './types';

// ---------------------------------------------------------------------------
// Factory Helpers
// ---------------------------------------------------------------------------

export function createOverlay(
  overlayId: string,
  overlayType: OverlayType,
  title?: string,
  isDismissible: boolean = true,
  hasFocusTrap: boolean = true,
): Overlay {
  return { overlayId, overlayType, title, isDismissible, hasFocusTrap };
}

export function createToast(
  toastId: string,
  message: string,
  toastType: ToastType = 'info',
  autoDismissMs: number = 4000,
  actionLabel?: string,
  isPersistent: boolean = false,
): Toast {
  return { toastId, toastType, message, actionLabel, autoDismissMs, isPersistent };
}

// ---------------------------------------------------------------------------
// Immutable State Operations (functional)
// ---------------------------------------------------------------------------

export const emptyRegistry: OverlayRegistry = {
  activeOverlays: [],
  toastQueue: [],
};

export function pushOverlay(registry: OverlayRegistry, overlay: Overlay): OverlayRegistry {
  return { ...registry, activeOverlays: [...registry.activeOverlays, overlay] };
}

export function popOverlay(registry: OverlayRegistry): OverlayRegistry {
  return { ...registry, activeOverlays: registry.activeOverlays.slice(0, -1) };
}

export function removeOverlay(registry: OverlayRegistry, overlayId: string): OverlayRegistry {
  return {
    ...registry,
    activeOverlays: registry.activeOverlays.filter((o) => o.overlayId !== overlayId),
  };
}

export function pushToast(registry: OverlayRegistry, toast: Toast): OverlayRegistry {
  return { ...registry, toastQueue: [...registry.toastQueue, toast] };
}

export function dismissToast(registry: OverlayRegistry, toastId: string): OverlayRegistry {
  return {
    ...registry,
    toastQueue: registry.toastQueue.filter((t) => t.toastId !== toastId),
  };
}

export function getTopOverlay(registry: OverlayRegistry): Overlay | undefined {
  return registry.activeOverlays[registry.activeOverlays.length - 1];
}

export function hasActiveOverlay(registry: OverlayRegistry): boolean {
  return registry.activeOverlays.length > 0;
}
