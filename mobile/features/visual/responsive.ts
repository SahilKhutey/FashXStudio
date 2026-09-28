/**
 * FashXStudio — Responsive Layout & Breakpoint Engine
 * Phase 01: Visual Product Architecture
 */

import { BreakpointMetrics, DeviceBreakpoint } from "./types";

export const BREAKPOINTS = {
  xs: 0,
  sm: 480,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const;

export function resolveBreakpoint(width: number): DeviceBreakpoint {
  if (width >= BREAKPOINTS.xl) return "xl";
  if (width >= BREAKPOINTS.lg) return "lg";
  if (width >= BREAKPOINTS.md) return "md";
  if (width >= BREAKPOINTS.sm) return "sm";
  return "xs";
}

export function computeBreakpointMetrics(width: number, height: number): BreakpointMetrics {
  const bp = resolveBreakpoint(width);
  const isMobile = bp === "xs" || bp === "sm";
  const isTablet = bp === "md";
  const isDesktop = bp === "lg" || bp === "xl";

  switch (bp) {
    case "xs":
      return {
        breakpoint: "xs",
        width,
        height,
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        columns: 4,
        gutter: 12,
        margin: 16,
        contentMaxWidth: 479,
      };
    case "sm":
      return {
        breakpoint: "sm",
        width,
        height,
        isMobile: true,
        isTablet: false,
        isDesktop: false,
        columns: 6,
        gutter: 16,
        margin: 20,
        contentMaxWidth: 767,
      };
    case "md":
      return {
        breakpoint: "md",
        width,
        height,
        isMobile: false,
        isTablet: true,
        isDesktop: false,
        columns: 8,
        gutter: 20,
        margin: 24,
        contentMaxWidth: 960,
      };
    case "lg":
      return {
        breakpoint: "lg",
        width,
        height,
        isMobile: false,
        isTablet: false,
        isDesktop: true,
        columns: 12,
        gutter: 24,
        margin: 32,
        contentMaxWidth: 1200,
      };
    case "xl":
      return {
        breakpoint: "xl",
        width,
        height,
        isMobile: false,
        isTablet: false,
        isDesktop: true,
        columns: 12,
        gutter: 32,
        margin: 48,
        contentMaxWidth: 1440,
      };
  }
}

/**
 * Calculates responsive width given a target column span
 */
export function calculateColumnSpanWidth(
  colSpan: number,
  metrics: BreakpointMetrics
): number {
  const effectiveSpan = Math.min(Math.max(1, colSpan), metrics.columns);
  const totalMargin = metrics.margin * 2;
  const availableWidth = (metrics.contentMaxWidth ? Math.min(metrics.width, metrics.contentMaxWidth) : metrics.width) - totalMargin;
  const totalGutter = (metrics.columns - 1) * metrics.gutter;
  const singleColumnWidth = (availableWidth - totalGutter) / metrics.columns;
  return singleColumnWidth * effectiveSpan + metrics.gutter * (effectiveSpan - 1);
}
