import { create } from 'zustand';
import { profileApi } from '../services/profileApi';
import {
  CategorySizeItem,
  FeatureCompleteness,
  ShopperProfile,
  ShopperProfileUpdate,
} from '../types/profile.types';

interface ProfileState {
  profile: ShopperProfile | null;
  completeness: FeatureCompleteness | null;
  isLoading: boolean;
  error: string | null;

  fetchProfile: () => Promise<void>;
  updateProfile: (data: ShopperProfileUpdate) => Promise<ShopperProfile>;
  updateCategorySizes: (sizes: CategorySizeItem[]) => Promise<void>;
  clearProfile: () => void;
}

export const useProfileStore = create<ProfileState>((set, get) => ({
  profile: null,
  completeness: null,
  isLoading: false,
  error: null,

  fetchProfile: async () => {
    set({ isLoading: true, error: null });
    try {
      const [profile, completeness] = await Promise.all([
        profileApi.getProfile(),
        profileApi.getCompleteness().catch(() => null),
      ]);
      set({ profile, completeness, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.message || 'Failed to load profile',
        isLoading: false,
      });
    }
  },

  updateProfile: async (data: ShopperProfileUpdate) => {
    set({ isLoading: true, error: null });
    try {
      const current = get().profile;
      const payload: ShopperProfileUpdate = {
        ...data,
        expected_version: current?.version,
      };
      const updated = await profileApi.updateProfile(payload);
      const completeness = await profileApi.getCompleteness().catch(() => null);
      set({ profile: updated, completeness, isLoading: false });
      return updated;
    } catch (err: any) {
      set({
        error: err?.message || 'Failed to update profile',
        isLoading: false,
      });
      throw err;
    }
  },

  updateCategorySizes: async (sizes: CategorySizeItem[]) => {
    set({ isLoading: true, error: null });
    try {
      const updatedSizes = await profileApi.updateCategorySizes(sizes);
      const current = get().profile;
      if (current) {
        set({
          profile: { ...current, category_sizes: updatedSizes },
          isLoading: false,
        });
      } else {
        set({ isLoading: false });
      }
    } catch (err: any) {
      set({
        error: err?.message || 'Failed to update category sizes',
        isLoading: false,
      });
      throw err;
    }
  },

  clearProfile: () => {
    set({
      profile: null,
      completeness: null,
      isLoading: false,
      error: null,
    });
  },
}));
