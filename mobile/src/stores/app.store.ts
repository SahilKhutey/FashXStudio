import { create } from "zustand";

export type AppUiState = {
  selectedCategory: string | null;
  searchQuery: string;
  selectedColors: string[];
  setSelectedCategory: (category: string | null) => void;
  setSearchQuery: (query: string) => void;
  setSelectedColors: (colors: string[]) => void;
  reset: () => void;
};

const initialState = {
  selectedCategory: null as string | null,
  searchQuery: "",
  selectedColors: [] as string[],
};

/**
 * Lightweight Zustand store for transient shopper UI preferences and filters.
 * Server state (catalog, profile, fit, VTO jobs) belongs in TanStack Query;
 * authentication tokens belong exclusively in SecureStore.
 */
export const useAppStore = create<AppUiState>((set) => ({
  ...initialState,
  setSelectedCategory: (category) => set({ selectedCategory: category }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setSelectedColors: (colors) => set({ selectedColors: colors }),
  reset: () => set(initialState),
}));
