/**
 * FashXStudio Release Gate & Verification Hook.
 * Phase 16: VD-16 — FINAL.
 */

import { useState, useCallback } from 'react';
import type {
  ProductionReleaseReportContract,
  ReleaseGateResultContract,
  ReleaseGateStatus,
  TokenValidationReportContract,
  VisualTrackStatusContract,
} from '../types';

export interface UseReleaseGateOptions {
  apiBaseUrl?: string;
}

export function useReleaseGate(options: UseReleaseGateOptions = {}) {
  const { apiBaseUrl = '/api/v1/visual/release' } = options;
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ProductionReleaseReportContract | null>(null);
  const [trackStatus, setTrackStatus] = useState<VisualTrackStatusContract | null>(null);

  const fetchTrackStatus = useCallback(async (): Promise<VisualTrackStatusContract | null> => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/status`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data: VisualTrackStatusContract = await res.json();
      setTrackStatus(data);
      return data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch visual track status';
      setError(msg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [apiBaseUrl]);

  const auditReleaseGates = useCallback(
    async (version: string = 'v1.0.0-rc1'): Promise<ProductionReleaseReportContract | null> => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch(`${apiBaseUrl}/gate-audit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ release_version: version }),
        });
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data: ProductionReleaseReportContract = await res.json();
        setReport(data);
        return data;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to audit release gates';
        setError(msg);
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [apiBaseUrl]
  );

  const validateToken = useCallback(
    async (
      tokenName: string,
      primitiveRef: string,
      category: string = 'color'
    ): Promise<TokenValidationReportContract | null> => {
      try {
        const res = await fetch(`${apiBaseUrl}/token-validation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            token_name: tokenName,
            token_category: category,
            primitive_ref: primitiveRef,
            semantic_usage: 'Release Verification Test',
          }),
        });
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return await res.json();
      } catch {
        return null;
      }
    },
    [apiBaseUrl]
  );

  return {
    isLoading,
    error,
    report,
    trackStatus,
    fetchTrackStatus,
    auditReleaseGates,
    validateToken,
  };
}
