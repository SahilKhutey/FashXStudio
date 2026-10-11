import { create } from "zustand";
import { Session } from "@supabase/supabase-js";
import { Image } from "expo-image";
import { supabase } from "../../lib/supabase";

export interface UserMe {
  user_id: string;
  roles: string[];
  consent_given?: boolean;
  profile_completed?: boolean;
}

interface AuthState {
  session: Session | null;
  me: UserMe | null;
  isLoading: boolean;
  setSession: (session: Session | null) => void;
  setMe: (me: UserMe | null) => void;
  setIsLoading: (loading: boolean) => void;
  signOut: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  session: null,
  me: null,
  isLoading: true,
  setSession: (session) => set({ session }),
  setMe: (me) => set({ me }),
  setIsLoading: (isLoading) => set({ isLoading }),
  signOut: async () => {
    try {
      await supabase.auth.signOut();
    } catch (e) {
      console.warn("Supabase sign out error:", e);
    }
    try {
      await Image.clearDiskCache();
    } catch (e) {
      console.warn("Image disk cache clear error:", e);
    }
    set({ session: null, me: null, isLoading: false });
  },
}));
