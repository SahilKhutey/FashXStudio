import { api } from '../../../api/client';
import {
  CategorySizeItem,
  FeatureCompleteness,
  ShopperProfile,
  ShopperProfileCreate,
  ShopperProfileUpdate,
} from '../types/profile.types';

export const profileApi = {
  getProfile: async (): Promise<ShopperProfile> => {
    return api<ShopperProfile>('/profile/me');
  },

  createOrReplaceProfile: async (
    payload: ShopperProfileCreate,
  ): Promise<ShopperProfile> => {
    return api<ShopperProfile>('/profile/me', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },

  updateProfile: async (
    payload: ShopperProfileUpdate,
  ): Promise<ShopperProfile> => {
    return api<ShopperProfile>('/profile/me', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  getCompleteness: async (): Promise<FeatureCompleteness> => {
    return api<FeatureCompleteness>('/profile/me/completeness');
  },

  getCategorySizes: async (): Promise<CategorySizeItem[]> => {
    return api<CategorySizeItem[]>('/profile/me/category-sizes');
  },

  updateCategorySizes: async (
    sizes: CategorySizeItem[],
  ): Promise<CategorySizeItem[]> => {
    return api<CategorySizeItem[]>('/profile/me/category-sizes', {
      method: 'PUT',
      body: JSON.stringify({ sizes }),
    });
  },
};
