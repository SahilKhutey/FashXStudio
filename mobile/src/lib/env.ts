/**
 * Environment configuration for the mobile client.
 */

export interface MobileEnv {
  apiUrl: string;
  supabaseUrl: string;
  supabaseAnonKey: string;
}

export const env: MobileEnv = {
  apiUrl: process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000",
  supabaseUrl: process.env.EXPO_PUBLIC_SUPABASE_URL || "https://dummy-fashx.supabase.co",
  supabaseAnonKey: process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "dummy-anon-key",
};
