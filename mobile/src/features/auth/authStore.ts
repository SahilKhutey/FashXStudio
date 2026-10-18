import { create } from "zustand";
import { Session } from "@supabase/supabase-js";
import { Image } from "expo-image";
import { supabase } from "../../lib/supabase";
import { setDevToken } from "../../lib/token";

export interface UserMe {
  user_id: string;
  roles: string[];
  onboarding?: {
    complete: boolean;
    missing: string[];
    consent_version_required: string;
    consented_version: string | null;
  };
}

interface AuthState {
  session: Session | null;
  devSession: boolean;
  hasSession: boolean;
  me: UserMe | null;
  isLoading: boolean;
  setSession: (session: Session | null) => void;
  setDevSession: (devSession: boolean) => void;
  setHasSession: (hasSession: boolean) => void;
  setMe: (me: UserMe | null) => void;
  setIsLoading: (loading: boolean) => void;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  devSession: false,
  hasSession: false,
  me: null,
  isLoading: true,
  setSession: (session) =>
    set((state) => ({
      session,
      hasSession: Boolean(session || state.devSession),
    })),
  setDevSession: (devSession) =>
    set((state) => ({
      devSession,
      hasSession: Boolean(state.session || devSession),
    })),
  setHasSession: (hasSession) => set({ hasSession }),
  setMe: (me) => set({ me }),
  setIsLoading: (isLoading) => set({ isLoading }),
  signOut: async () => {
    try {
      await supabase.auth.signOut();
    } catch (e) {
      console.warn("Supabase sign out error:", e);
    }
    setDevToken(null);
    try {
      await Image.clearDiskCache();
    } catch (e) {
      console.warn("Image disk cache clear error:", e);
    }
    set({
      session: null,
      devSession: false,
      hasSession: false,
      me: null,
      isLoading: false,
    });
  },
}));
