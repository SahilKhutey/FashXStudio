/**
 * Environment configuration for the mobile client.
 */

export interface MobileEnv {
  apiUrl: string;
  supabaseUrl: string;
  supabaseAnonKey: string;
  devTokenLogin: boolean;
}

export interface RuntimeConfig {
  apiBaseUrl: string;
  allowDevAuth: boolean;
  supabaseUrl?: string;
  supabaseAnonKey?: string;
}

export function validateRuntimeConfig(
  config: RuntimeConfig,
  isProduction: boolean,
): RuntimeConfig {
  if (isProduction && !config.apiBaseUrl.startsWith("https://")) {
    throw new Error("Production API must use HTTPS");
  }
  if (isProduction && config.allowDevAuth) {
    throw new Error("Development authentication is disabled in production");
  }
  return config;
}

const isProd =
  typeof __DEV__ !== "undefined"
    ? !__DEV__
    : process.env.NODE_ENV === "production";

const rawApiUrl = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";
const rawDevTokenLogin =
  (typeof __DEV__ !== "undefined" ? Boolean(__DEV__) : process.env.NODE_ENV !== "production") &&
  process.env.EXPO_PUBLIC_DEV_TOKEN_LOGIN === "1";

// Validate on module load (fail closed)
if (isProd) {
  validateRuntimeConfig(
    {
      apiBaseUrl: rawApiUrl,
      allowDevAuth: rawDevTokenLogin,
    },
    true,
  );
}

export const env: MobileEnv = {
  apiUrl: rawApiUrl,
  supabaseUrl: process.env.EXPO_PUBLIC_SUPABASE_URL || "https://dummy-fashx.supabase.co",
  supabaseAnonKey: process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY || "dummy-anon-key",
  devTokenLogin: rawDevTokenLogin,
};

export function isDevTokenEnabled(): boolean {
  return env.devTokenLogin;
}
