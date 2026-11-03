import { create } from "zustand";
import { Session } from "@supabase/supabase-js";
import { Image } from "expo-image";
import { supabase } from "../../lib/supabase";
import { setDevToken } from "../../lib/token";
import { queryClient } from "../../app-shell/queryClient";

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
  setDevSession: (value: boolean) => void;
  setHasSession: (value: boolean) => void;
  setMe: (me: UserMe | null) => void;
  setIsLoading: (value: boolean) => void;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  devSession: false,
  hasSession: false,
  me: null,
  isLoading: true,
  setSession: (session) => {
    set((state) => ({
      session,
      hasSession: Boolean(session || state.devSession),
    }));
  },
  setDevSession: (devSession) => {
    set((state) => ({
      devSession,
      hasSession: Boolean(state.session || devSession),
    }));
  },
  setHasSession: (hasSession) => set({ hasSession }),
  setMe: (me) => {
    const previousUserId = useAuthStore.getState().me?.user_id;
    const nextUserId = me?.user_id;
    if (previousUserId !== nextUserId) {
      queryClient.clear();
    }
    set({ me });
  },
  setIsLoading: (isLoading) => set({ isLoading }),
  signOut: async () => {
    // Clear sensitive cached data immediately.
    queryClient.clear();
    try {
      await supabase.auth.signOut();
    } catch {
      // Local logout must still complete.
    }
    setDevToken(null);
    try {
      await Image.clearDiskCache();
    } catch {
      // Cache cleanup must not prevent logout.
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
