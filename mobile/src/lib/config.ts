import * as Application from "expo-application";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { api } from "../api/client";

export interface RemoteConfig {
  min_app_version: string;
  maintenance: boolean;
  tryon_supported_categories: string[];
  flags: {
    tryon: boolean;
  };
}

const CONFIG_CACHE_KEY = "fashx_remote_config_cache";

/**
 * Compare two semver strings (e.g. "0.1.0" vs "0.2.0").
 * Returns negative if v1 < v2, 0 if equal, positive if v1 > v2.
 */
export function compareVersions(v1: string, v2: string): number {
  const p1 = v1.split(".").map((x) => parseInt(x, 10) || 0);
  const p2 = v2.split(".").map((x) => parseInt(x, 10) || 0);
  for (let i = 0; i < Math.max(p1.length, p2.length); i++) {
    const num1 = p1[i] ?? 0;
    const num2 = p2[i] ?? 0;
    if (num1 > num2) return 1;
    if (num1 < num2) return -1;
  }
  return 0;
}

export function getAppVersion(): string {
  return Application.nativeApplicationVersion || "0.1.0";
}

export async function fetchRemoteConfig(): Promise<RemoteConfig> {
  try {
    const config = await api<RemoteConfig>("/config", { timeoutMs: 8000 });
    // Cache good config for offline starts
    await AsyncStorage.setItem(CONFIG_CACHE_KEY, JSON.stringify(config));
    return config;
  } catch (err) {
    // Attempt cache read
    const cached = await AsyncStorage.getItem(CONFIG_CACHE_KEY);
    if (cached) {
      try {
        return JSON.parse(cached) as RemoteConfig;
      } catch {
        // Corrupted cache
      }
    }
    // Default safe fallback if network and cache both fail
    return {
      min_app_version: "0.1.0",
      maintenance: false,
      tryon_supported_categories: ["tops", "bottoms", "one-pieces"],
      flags: { tryon: true },
    };
  }
}
