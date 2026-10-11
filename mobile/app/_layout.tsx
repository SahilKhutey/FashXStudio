import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity } from "react-native";
import { Slot, useRouter, useSegments } from "expo-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import "../src/i18n";
import { supabase } from "../src/lib/supabase";
import { useAuthStore, UserMe } from "../src/features/auth/authStore";
import { api } from "../src/api/client";
import {
  fetchRemoteConfig,
  compareVersions,
  getAppVersion,
  RemoteConfig,
} from "../src/lib/config";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error: any) => {
        // Automatically retry up to 2 times for network or 5xx errors on idempotent GETs
        if (failureCount >= 2) return false;
        if (error?.status && error.status >= 400 && error.status < 500) {
          return false;
        }
        return true;
      },
    },
  },
});

function AuthAndConfigGate({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const router = useRouter();
  const segments = useSegments();

  const { session, setSession, setMe, setIsLoading, isLoading } = useAuthStore();
  const [remoteConfig, setRemoteConfig] = useState<RemoteConfig | null>(null);
  const [configLoading, setConfigLoading] = useState(true);

  // 1. Fetch remote config & evaluate version / maintenance gates
  useEffect(() => {
    let isMounted = true;
    fetchRemoteConfig()
      .then((cfg) => {
        if (isMounted) {
          setRemoteConfig(cfg);
          setConfigLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) setConfigLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Listen to Supabase auth state changes and sync backend /me
  useEffect(() => {
    let isMounted = true;

    const checkSession = async () => {
      const {
        data: { session: currentSession },
      } = await supabase.auth.getSession();

      if (isMounted) {
        setSession(currentSession);
        if (currentSession) {
          try {
            const me = await api<UserMe>("/me");
            if (isMounted) setMe(me);
          } catch {
            // Backend /me may fail if token is invalid or server is unreachable
          }
        } else {
          setMe(null);
        }
        setIsLoading(false);
      }
    };

    checkSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, newSession) => {
      if (isMounted) {
        setSession(newSession);
        if (newSession) {
          try {
            const me = await api<UserMe>("/me");
            if (isMounted) setMe(me);
          } catch {
            // Token error handled by api client
          }
        } else {
          setMe(null);
        }
        setIsLoading(false);
      }
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, [setSession, setMe, setIsLoading]);

  // 3. Navigation routing based on auth state
  useEffect(() => {
    if (isLoading || configLoading) return;

    const inAuthGroup = segments[0] === "(auth)";

    if (!session && !inAuthGroup) {
      // Redirect to sign in if unauthenticated
      router.replace("/(auth)/sign-in");
    } else if (session && inAuthGroup) {
      // Redirect to root if authenticated
      router.replace("/");
    }
  }, [session, segments, isLoading, configLoading, router]);

  // Handle Maintenance Mode
  if (remoteConfig?.maintenance) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.gateTitle} accessibilityRole="header">
          {t("config.maintenanceTitle")}
        </Text>
        <Text style={styles.gateMessage}>
          {t("config.maintenanceMessage")}
        </Text>
      </View>
    );
  }

  // Handle Min App Version Gate
  if (
    remoteConfig?.min_app_version &&
    compareVersions(getAppVersion(), remoteConfig.min_app_version) < 0
  ) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.gateTitle} accessibilityRole="header">
          {t("config.updateRequired")}
        </Text>
        <Text style={styles.gateMessage}>{t("config.updateMessage")}</Text>
        <TouchableOpacity
          style={styles.gateButton}
          accessibilityRole="button"
          accessibilityLabel={t("config.updateButton")}
        >
          <Text style={styles.gateButtonText}>{t("config.updateButton")}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // Loading spinner while checking initial auth and remote config
  if (isLoading || configLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  return <>{children}</>;
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthAndConfigGate>
        <Slot />
      </AuthAndConfigGate>
    </QueryClientProvider>
  );
}

const styles = StyleSheet.create({
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    backgroundColor: "#F9FAFB",
  },
  gateTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
    textAlign: "center",
  },
  gateMessage: {
    fontSize: 15,
    color: "#4B5563",
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 20,
  },
  gateButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  gateButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
});
