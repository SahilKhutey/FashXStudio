import { createClient } from "@supabase/supabase-js";
import { env } from "./env";
import { LargeSecureStore } from "./storage";

export const supabase = createClient(env.supabaseUrl, env.supabaseAnonKey, {
  auth: {
    storage: LargeSecureStore,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});
