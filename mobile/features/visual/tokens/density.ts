/**
 * FashXStudio Design System — Density Engine (Phase 02)
 *
 * Implements Section 2.39 Visual Density Modes:
 * - comfortable (1.0x): standard consumer discovery
 * - compact (0.8x): dense shopping, multi-merchant comparison, data tables
 * - spacious (1.25x): editorial lookbooks, fashion campaigns
 */

export type DensityMode = 'comfortable' | 'compact' | 'spacious';

export const densityMultipliers: Record<DensityMode, number> = {
  compact: 0.8,
  comfortable: 1.0,
  spacious: 1.25,
};

/**
 * Calculates a scaled spacing or padding pixel value given the active density mode.
 */
export function applyDensity(basePixels: number, mode: DensityMode = 'comfortable'): number {
  const multiplier = densityMultipliers[mode] ?? 1.0;
  return Math.round(basePixels * multiplier);
}
