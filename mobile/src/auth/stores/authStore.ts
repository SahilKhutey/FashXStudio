/**
 * Lightweight Zustand Store for UI Authentication State.
 * Holds non-sensitive rendering state only. Zero tokens or secrets are stored here.
 */

import { create } from "zustand";

export interface AuthUIState {
  isAuthenticated: boolean;
  isLoading: boolean;
  userId: string | null;
  authError: string | null;
  setAuthenticated: (userId: string) => void;
  setUnauthenticated: (error?: string) => void;
  setLoading: (loading: boolean) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthUIState>((set) => ({
  isAuthenticated: false,
  isLoading: true,
  userId: null,
  authError: null,
  setAuthenticated: (userId: string) =>
    set({
      isAuthenticated: true,
      isLoading: false,
      userId,
      authError: null,
    }),
  setUnauthenticated: (error?: string) =>
    set({
      isAuthenticated: false,
      isLoading: false,
      userId: null,
      authError: error ?? null,
    }),
  setLoading: (loading: boolean) => set({ isLoading: loading }),
  clearError: () => set({ authError: null }),
}));
