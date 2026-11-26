import { create } from "zustand";

import type {
  MeasurementDefinition,
  MeasurementHistoryItem,
  ShopperFitProfile,
} from "../types";

interface FitProfileState {
  profile: ShopperFitProfile | null;
  definitions: MeasurementDefinition[];
  history: MeasurementHistoryItem[];
  loading: boolean;
  error: string | null;
  setProfile: (profile: ShopperFitProfile | null) => void;
  setDefinitions: (definitions: MeasurementDefinition[]) => void;
  setHistory: (history: MeasurementHistoryItem[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearProfile: () => void;
}

/**
 * Ephemeral in-memory Zustand store for Shopper Fit Profile.
 * Must NEVER persist body measurements to unsecured local storage and
 * must call clearProfile() on logout, account deletion, or consent withdrawal.
 */
export const useFitProfileStore = create<FitProfileState>((set) => ({
  profile: null,
  definitions: [],
  history: [],
  loading: false,
  error: null,

  setProfile: (profile) => set({ profile, error: null }),
  setDefinitions: (definitions) => set({ definitions }),
  setHistory: (history) => set({ history }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearProfile: () =>
    set({
      profile: null,
      history: [],
      loading: false,
      error: null,
    }),
}));
