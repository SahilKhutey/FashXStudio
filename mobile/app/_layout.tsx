import React, { useEffect, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Slot, useRouter, useSegments } from "expo-router";
import { useTranslation } from "react-i18next";
import "../src/i18n";
import { supabase } from "../src/lib/supabase";
import { useAuthStore, UserMe } from "../src/features/auth/authStore";
import { getDevToken } from "../src/lib/token";
import { api } from "../src/api/client";
import {
  fetchRemoteConfig,
  compareVersions,
  getAppVersion,
  RemoteConfig,
} from "../src/lib/config";
import { getRouteDecision } from "../src/navigation/route-policy";
import { AppProviders } from "../src/app-shell";
import { LoadingState } from "../src/components/states";

function AuthAndConfigGate({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const router = useRouter();
  const segments = useSegments();

  const { session, setSession, setMe, setIsLoading, isLoading, hasSession, setHasSession, me } =
    useAuthStore();
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
      const devTok = getDevToken();
      if (devTok) {
        setHasSession(true);
        try {
          const me = await api<UserMe>("/me");
          if (isMounted) setMe(me);
        } catch {
          // Token error handled by api client
        }
        if (isMounted) setIsLoading(false);
        return;
      }

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
      if (getDevToken()) {
        return;
      }
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
  }, [setSession, setMe, setIsLoading, setHasSession]);

  // 3. Centralized route policy decision
  useEffect(() => {
    const decision = getRouteDecision({
      authLoading: isLoading,
      configLoading,
      hasSession,
      segments: segments as string[],
      onboarding: me?.onboarding,
    });

    if (decision.type === "replace") {
      router.replace(decision.href as any);
    }
  }, [hasSession, segments, isLoading, configLoading, me?.onboarding, router]);

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
    return <LoadingState />;
  }

  return <>{children}</>;
}

export default function RootLayout() {
  return (
    <AppProviders>
      <AuthAndConfigGate>
        <Slot />
      </AuthAndConfigGate>
    </AppProviders>
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
