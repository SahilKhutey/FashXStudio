/**
 * Zustand Local UI State Store (Rule I13)
 * Manages client UI states (selected tabs, modal visibility, filter selections).
 * Server data is managed exclusively by TanStack Query.
 */

import { create } from "zustand";

interface UiState {
  activeAestheticFilter: string | null;
  isFilterSheetOpen: boolean;
  activeOccasion: string;
  setActiveAestheticFilter: (filter: string | null) => void;
  setFilterSheetOpen: (open: boolean) => void;
  setActiveOccasion: (occasion: string) => void;
}

export const useUiStore = create<UiState>((set) => ({
  activeAestheticFilter: null,
  isFilterSheetOpen: false,
  activeOccasion: "casual",
  setActiveAestheticFilter: (filter) => set({ activeAestheticFilter: filter }),
  setFilterSheetOpen: (open) => set({ isFilterSheetOpen: open }),
  setActiveOccasion: (occasion) => set({ activeOccasion: occasion }),
}));
