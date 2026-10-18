import { useState } from "react";
import { View, Text, Switch, Pressable, ScrollView, StyleSheet } from "react-native";
import { useTranslation } from "react-i18next";
import * as WebBrowser from "expo-web-browser";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { api } from "../../src/api/client";
import { useConfig, useMe } from "../../src/api/hooks";
import { errorKey } from "../../src/lib/errors";

export default function Consent() {
  const router = useRouter();
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: cfg } = useConfig();
  const { data: me } = useMe(true);
  const [terms, setTerms] = useState(false);
  const [photo, setPhoto] = useState(false);
  const [adult, setAdult] = useState(false);
  const [blocked, setBlocked] = useState(false);

  const grant = useMutation({
    mutationFn: () =>
      api(`/profile/${me!.user_id}/consent`, {
        method: "POST",
        body: JSON.stringify({
          consent_version: cfg!.consent_version,
          accepts_terms: terms,
          accepts_body_photo: photo,
          is_18_or_older: adult,
        }),
      }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
      router.push("/onboarding/profile");
    },
    onError: (e: any) => {
      if (e?.code === "age_requirement") {
        setBlocked(true);
      } else if (e?.code === "consent_version_outdated") {
        qc.invalidateQueries({ queryKey: ["config"] });
      }
    },
  });

  if (blocked) {
    return (
      <View style={styles.blockedContainer}>
        <Text style={styles.blockedTitle} accessibilityRole="header">
          {t("consent.adultsOnlyTitle")}
        </Text>
        <Text style={styles.blockedBody}>{t("consent.adultsOnlyBody")}</Text>
      </View>
    );
  }

  const ready = terms && photo && adult && Boolean(cfg?.consent_version) && !grant.isPending;

  const row = (label: string, v: boolean, set: (b: boolean) => void) => (
    <View style={styles.row}>
      <Switch value={v} onValueChange={set} accessibilityLabel={label} />
      <Text style={styles.rowLabel}>{label}</Text>
    </View>
  );

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title} accessibilityRole="header">
        {t("consent.title")}
      </Text>
      <Text style={styles.summary}>{t("consent.summary")}</Text>

      {Boolean(cfg?.legal?.privacy_url) && (
        <Pressable
          accessibilityRole="link"
          onPress={() => cfg?.legal?.privacy_url && WebBrowser.openBrowserAsync(cfg.legal.privacy_url)}
          style={styles.linkButton}
        >
          <Text style={styles.linkText}>{t("consent.readPolicy")}</Text>
        </Pressable>
      )}

      <View style={styles.switchGroup}>
        {row(t("consent.acceptTerms"), terms, setTerms)}
        {row(t("consent.acceptBodyPhoto"), photo, setPhoto)}
        {row(t("consent.adult"), adult, setAdult)}
      </View>

      {grant.isError && !blocked && (
        <Text style={styles.errorText} accessibilityLiveRegion="polite">
          {t(errorKey(grant.error))}
        </Text>
      )}

      <Pressable
        accessibilityRole="button"
        accessibilityState={{ disabled: !ready }}
        disabled={!ready}
        onPress={() => grant.mutate()}
        style={[styles.continueButton, !ready && styles.buttonDisabled]}
      >
        <Text style={styles.continueText}>{t("common.continue")}</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 24,
    backgroundColor: "#FFFFFF",
    flexGrow: 1,
    justifyContent: "center",
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
  },
  summary: {
    fontSize: 15,
    color: "#4B5563",
    lineHeight: 22,
    marginBottom: 16,
  },
  linkButton: {
    marginBottom: 20,
  },
  linkText: {
    color: "#4F46E5",
    fontSize: 14,
    fontWeight: "600",
    textDecorationLine: "underline",
  },
  switchGroup: {
    marginVertical: 12,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  rowLabel: {
    flex: 1,
    marginLeft: 12,
    fontSize: 14,
    color: "#1F2937",
    lineHeight: 20,
  },
  continueButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 28,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  continueText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
  errorText: {
    color: "#DC2626",
    fontSize: 14,
    marginTop: 12,
  },
  blockedContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
    backgroundColor: "#FEF2F2",
  },
  blockedTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#991B1B",
    marginBottom: 12,
    textAlign: "center",
  },
  blockedBody: {
    fontSize: 15,
    color: "#7F1D1D",
    textAlign: "center",
    lineHeight: 22,
  },
});
