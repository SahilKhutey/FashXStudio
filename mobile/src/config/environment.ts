import { z } from "zod";

export const AppEnvSchema = z.enum(["development", "staging", "production"]);
export type AppEnv = z.infer<typeof AppEnvSchema>;

const RawEnvironmentSchema = z.object({
  APP_ENV: AppEnvSchema.default("development"),
  EXPO_PUBLIC_APP_ENV: AppEnvSchema.optional(),
  EXPO_PUBLIC_API_BASE_URL: z.string().url().optional(),
  EXPO_PUBLIC_API_URL: z.string().url().optional(),
  EXPO_PUBLIC_ENABLE_DEV_TOOLS: z.enum(["true", "false"]).default("false"),
});

export interface ParsedEnvironment {
  appEnv: AppEnv;
  apiBaseUrl: string;
  enableDevTools: boolean;
}

export function parseEnvironment(
  raw: Record<string, string | undefined>,
): ParsedEnvironment {
  const normalized = {
    APP_ENV: raw.APP_ENV ?? raw.EXPO_PUBLIC_APP_ENV ?? "development",
    EXPO_PUBLIC_APP_ENV: raw.EXPO_PUBLIC_APP_ENV,
    EXPO_PUBLIC_API_BASE_URL: raw.EXPO_PUBLIC_API_BASE_URL,
    EXPO_PUBLIC_API_URL: raw.EXPO_PUBLIC_API_URL,
    EXPO_PUBLIC_ENABLE_DEV_TOOLS: raw.EXPO_PUBLIC_ENABLE_DEV_TOOLS ?? "false",
  };

  const parsed = RawEnvironmentSchema.safeParse(normalized);
  if (!parsed.success) {
    throw new Error(
      `Invalid application environment configuration: ${parsed.error.message}`,
    );
  }

  if (
    parsed.data.EXPO_PUBLIC_APP_ENV &&
    parsed.data.APP_ENV !== parsed.data.EXPO_PUBLIC_APP_ENV
  ) {
    throw new Error("Application environment mismatch");
  }

  const apiBaseUrl = (
    parsed.data.EXPO_PUBLIC_API_BASE_URL ??
    parsed.data.EXPO_PUBLIC_API_URL ??
    "http://localhost:8000"
  ).replace(/\/+$/, "");

  if (
    (parsed.data.APP_ENV === "production" || parsed.data.APP_ENV === "staging") &&
    apiBaseUrl.startsWith("http://")
  ) {
    throw new Error(`${parsed.data.APP_ENV} API must use HTTPS`);
  }

  return {
    appEnv: parsed.data.APP_ENV,
    apiBaseUrl,
    enableDevTools:
      parsed.data.APP_ENV !== "production" &&
      parsed.data.EXPO_PUBLIC_ENABLE_DEV_TOOLS === "true",
  };
}

export const environment = parseEnvironment({
  APP_ENV: process.env.APP_ENV,
  EXPO_PUBLIC_APP_ENV: process.env.EXPO_PUBLIC_APP_ENV,
  EXPO_PUBLIC_API_BASE_URL: process.env.EXPO_PUBLIC_API_BASE_URL,
  EXPO_PUBLIC_API_URL: process.env.EXPO_PUBLIC_API_URL,
  EXPO_PUBLIC_ENABLE_DEV_TOOLS: process.env.EXPO_PUBLIC_ENABLE_DEV_TOOLS,
});
