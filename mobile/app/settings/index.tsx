import React, { useState } from "react";
import {
  StyleSheet,
  View,
  ScrollView,
  ActivityIndicator,
  Alert,
  Platform,
  Pressable,
} from "react-native";
import { useRouter } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../../src/features/auth/authStore";
import { useDerivedProfile, type UserPhotoItem } from "../../src/api/hooks";
import { api } from "../../src/api/client";
import { queryKeys } from "../../src/app-shell/queryKeys";
import { useDesignTokens } from "../../src/design-system/useDesignTokens";
import { AppText } from "../../src/design-system/components/AppText";
import { Button } from "../../src/design-system/components/Button";
import { Badge } from "../../src/design-system/components/Badge";
import { SectionHeader } from "../../src/design-system/components/SectionHeader";

export default function SettingsScreen() {
  const router = useRouter();
  const qc = useQueryClient();
  const { signOut, me } = useAuthStore();
  const userId = me?.user_id;

  const { colors, spacing, radius } = useDesignTokens();

  const { data: profile, isLoading: isProfileLoading } = useDerivedProfile(
    userId,
    Boolean(userId)
  );

  const [isDeletingPhoto, setIsDeletingPhoto] = useState(false);
  const [isRevokingConsent, setIsRevokingConsent] = useState(false);
  const [isErasingAccount, setIsErasingAccount] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  const activePhoto: UserPhotoItem | undefined =
    profile?.photos?.find((p) => p.status === "accepted") || profile?.photos?.[0];

  const confirmAction = (title: string, message: string, onConfirm: () => void) => {
    if (Platform.OS === "web") {
      if (typeof window !== "undefined" && window.confirm) {
        if (window.confirm(`${title}\n\n${message}`)) {
          onConfirm();
        }
      } else {
        onConfirm();
      }
    } else {
      Alert.alert(title, message, [
        { text: "Cancel", style: "cancel" },
        { text: "Confirm", style: "destructive", onPress: onConfirm },
      ]);
    }
  };

  const handleDeletePhoto = () => {
    if (!activePhoto || !userId) return;
    confirmAction(
      "Delete Reference Photo",
      "Are you sure you want to delete your active try-on reference photo? Virtual try-on will require capturing a new photo.",
      async () => {
        setIsDeletingPhoto(true);
        setActionNotice(null);
        try {
          await api(`/profile/${userId}/photos/${activePhoto.id}`, {
            method: "DELETE",
          });
          await qc.invalidateQueries({ queryKey: queryKeys.derivedProfile(userId) });
          await qc.invalidateQueries({ queryKey: queryKeys.me(userId) });
          setActionNotice("Photo deleted successfully.");
        } catch (e: any) {
          setActionNotice(e?.message || "Failed to delete photo.");
        } finally {
          setIsDeletingPhoto(false);
        }
      }
    );
  };

  const handleRevokeConsent = () => {
    if (!userId) return;
    confirmAction(
      "Revoke Body Photo Consent",
      "Revoking consent will immediately purge all your stored photos and cancel any pending try-on jobs per DPDP regulations.",
      async () => {
        setIsRevokingConsent(true);
        setActionNotice(null);
        try {
          await api(`/profile/${userId}/consent/revoke`, {
            method: "POST",
            body: JSON.stringify({ data_type: "body_photo" }),
          });
          await qc.invalidateQueries({ queryKey: queryKeys.derivedProfile(userId) });
          await qc.invalidateQueries({ queryKey: queryKeys.me(userId) });
          setActionNotice("Consent revoked and photos purged.");
        } catch (e: any) {
          setActionNotice(e?.message || "Failed to revoke consent.");
        } finally {
          setIsRevokingConsent(false);
        }
      }
    );
  };

  const handleEraseAccount = () => {
    if (!userId) return;
    confirmAction(
      "Erase Account Permanently",
      "This action is permanent and irreversible. All your profile data, measurements, photos, try-on history, and taste preferences will be deleted.",
      async () => {
        setIsErasingAccount(true);
        setActionNotice(null);
        try {
          await api("/me", {
            method: "DELETE",
          });
          await signOut();
          router.replace("/(auth)/sign-in");
        } catch (e: any) {
          setActionNotice(e?.message || "Failed to erase account.");
          setIsErasingAccount(false);
        }
      }
    );
  };

  const handleSignOut = async () => {
    await signOut();
    router.replace("/(auth)/sign-in");
  };

  const maskedUserId = userId ? `${userId.slice(0, 8)}...${userId.slice(-4)}` : "Guest";

  return (
    <ScrollView
      contentContainerStyle={[styles.container, { backgroundColor: colors.background }]}
      testID="settings-screen"
    >
      <View style={styles.header}>
        <AppText variant="heading1">Settings & Profile</AppText>
        <AppText variant="caption" color="textSecondary" style={{ marginTop: 4 }}>
          Account controls, DPDP privacy, and personalization preferences
        </AppText>
      </View>

      {actionNotice && (
        <View
          style={[
            styles.noticeBanner,
            { backgroundColor: colors.surfaceSecondary, borderColor: colors.brand },
          ]}
        >
          <AppText variant="body" style={{ color: colors.brand }}>
            {actionNotice}
          </AppText>
        </View>
      )}

      {/* 1. User Identity & Membership Card */}
      <View
        style={[
          styles.card,
          {
            backgroundColor: colors.surface,
            borderRadius: radius.lg,
            borderColor: colors.border,
          },
        ]}
        testID="user-identity-card"
      >
        <View style={styles.profileRow}>
          <View
            style={[
              styles.avatarCircle,
              { backgroundColor: colors.surfaceSecondary, borderRadius: radius.pill },
            ]}
          >
            <AppText variant="heading2">👤</AppText>
          </View>
          <View style={styles.profileDetails}>
            <View style={styles.nameRow}>
              <AppText variant="heading3">FashX Member</AppText>
              <Badge label="VERIFIED" variant="brand" />
            </View>
            <AppText variant="caption" color="textSecondary" style={{ marginTop: 2 }}>
              Account Ref: {maskedUserId}
            </AppText>
            <AppText variant="caption" color="textSecondary">
              Roles: {me?.roles?.join(", ") || "user"}
            </AppText>
          </View>
        </View>
      </View>

      {/* 2. Reference Photo Card */}
      <View
        style={[
          styles.card,
          {
            backgroundColor: colors.surface,
            borderRadius: radius.lg,
            borderColor: colors.border,
          },
        ]}
        testID="reference-photo-card"
      >
        <SectionHeader
          title="Active Try-On Reference Portrait"
          subtitle="Portrait reference used for synthetic dressing room generation"
        />

        {isProfileLoading ? (
          <ActivityIndicator
            size="small"
            color={colors.brand}
            style={{ marginVertical: spacing[4] }}
          />
        ) : activePhoto ? (
          <View style={styles.photoContainer}>
            <View style={styles.rowBetween}>
              <View style={styles.photoStatusGroup}>
                <AppText variant="body" style={styles.boldLabel}>
                  Portrait Status
                </AppText>
                <AppText variant="caption" color="textSecondary">
                  Stored securely in private encrypted vault
                </AppText>
              </View>
              <Badge
                label={activePhoto.status.toUpperCase()}
                variant={activePhoto.status === "accepted" ? "success" : "warning"}
              />
            </View>

            <View style={styles.photoActionsRow}>
              <Button
                title="Retake Portrait"
                variant="outline"
                onPress={() => router.push("/onboarding/capture")}
                style={{ flex: 1 }}
              />
              <Button
                title="Delete Photo"
                variant="danger"
                onPress={handleDeletePhoto}
                loading={isDeletingPhoto}
                accessibilityLabel="Delete reference photo"
                style={{ flex: 1 }}
              />
            </View>
          </View>
        ) : (
          <View style={styles.placeholderBox}>
            <AppText variant="body" color="textSecondary" style={{ marginBottom: spacing[3] }}>
              No active portrait reference on file. Capture a portrait to enable virtual try-on.
            </AppText>
            <Button
              title="Upload Reference Portrait"
              variant="primary"
              onPress={() => router.push("/onboarding/capture")}
            />
          </View>
        )}
      </View>

      {/* 3. DPDP Privacy & Consent Controls */}
      <View
        style={[
          styles.card,
          {
            backgroundColor: colors.surface,
            borderRadius: radius.lg,
            borderColor: colors.border,
          },
        ]}
        testID="consent-controls-card"
      >
        <SectionHeader
          title="DPDP Privacy & Consent"
          subtitle="Digital Personal Data Protection Act compliance"
        />

        <View style={[styles.consentItem, { borderBottomColor: colors.border }]}>
          <View style={styles.consentTextGroup}>
            <AppText variant="body" style={styles.boldLabel}>
              Body Photo Processing
            </AppText>
            <AppText variant="caption" color="textSecondary">
              Permits try-on synthetic dressing inference
            </AppText>
          </View>
          <Badge
            label={profile?.consents?.body_photo ? "GRANTED" : "NOT GRANTED"}
            variant={profile?.consents?.body_photo ? "success" : "neutral"}
          />
        </View>

        <View style={[styles.consentItem, { borderBottomColor: colors.border }]}>
          <View style={styles.consentTextGroup}>
            <AppText variant="body" style={styles.boldLabel}>
              Terms & Privacy Policy
            </AppText>
            <AppText variant="caption" color="textSecondary">
              Platform terms and privacy agreement
            </AppText>
          </View>
          <Badge
            label={profile?.consents?.terms_and_privacy ? "GRANTED" : "NOT GRANTED"}
            variant={profile?.consents?.terms_and_privacy ? "success" : "neutral"}
          />
        </View>

        <View style={[styles.consentItem, { borderBottomColor: colors.border }]}>
          <View style={styles.consentTextGroup}>
            <AppText variant="body" style={styles.boldLabel}>
              Body Measurements
            </AppText>
            <AppText variant="caption" color="textSecondary">
              Height, weight, and sizing parameters
            </AppText>
          </View>
          <Badge
            label={profile?.consents?.measurements ? "GRANTED" : "NOT GRANTED"}
            variant={profile?.consents?.measurements ? "success" : "neutral"}
          />
        </View>

        {Boolean(profile?.consents?.body_photo) && (
          <Button
            title="Revoke Body Photo Consent"
            variant="outline"
            onPress={handleRevokeConsent}
            loading={isRevokingConsent}
            accessibilityLabel="Revoke body photo consent"
            style={{ marginTop: spacing[3] }}
          />
        )}
      </View>

      {/* 4. Danger Zone: Right to be Forgotten */}
      <View
        style={[
          styles.card,
          styles.dangerCard,
          {
            backgroundColor: colors.surface,
            borderColor: colors.danger,
            borderRadius: radius.lg,
          },
        ]}
      >
        <SectionHeader
          title="Account Erasure"
          subtitle="Irreversible erasure under DPDP Section 12"
        />
        <AppText variant="caption" color="textSecondary" style={{ marginBottom: spacing[3] }}>
          Permanently delete all user profile data, photos, try-on history, and taste preferences.
          This action cannot be undone.
        </AppText>
        <Button
          title="Revoke Consent & Erase Account"
          variant="danger"
          onPress={handleEraseAccount}
          loading={isErasingAccount}
          accessibilityLabel="Erase account and all data"
        />
      </View>

      {/* 5. Sign Out Button */}
      <Button
        title="Sign Out"
        variant="secondary"
        onPress={handleSignOut}
        accessibilityLabel="Sign out"
        style={{ marginTop: spacing[2], marginBottom: spacing[4] }}
      />

      {/* 6. Discreet System Diagnostics */}
      <Pressable
        onPress={() => setShowDiagnostics((prev) => !prev)}
        style={styles.diagnosticsToggle}
      >
        <AppText variant="caption" color="textSecondary">
          {showDiagnostics ? "▼ Hide System Diagnostics" : "▶ Show System Diagnostics"}
        </AppText>
      </Pressable>

      {showDiagnostics && (
        <View
          style={[
            styles.diagnosticsCard,
            {
              backgroundColor: colors.surfaceSecondary,
              borderRadius: radius.md,
              borderColor: colors.border,
            },
          ]}
        >
          <AppText variant="caption" style={styles.diagRow}>
            Application Version: 0.1.0 (Build 2026.1)
          </AppText>
          <AppText variant="caption" style={styles.diagRow}>
            API Endpoint: {process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000"}
          </AppText>
          <AppText variant="caption" style={styles.diagRow}>
            Session Subject: {userId || "None"}
          </AppText>
          <AppText variant="caption" style={styles.diagRow}>
            Reference Photo Key: {activePhoto?.storage_key || "None"}
          </AppText>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 20,
  },
  header: {
    marginBottom: 20,
  },
  noticeBanner: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  card: {
    borderWidth: 1,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 1,
  },
  profileRow: {
    flexDirection: "row",
    alignItems: "center",
  },
  avatarCircle: {
    width: 52,
    height: 52,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 14,
  },
  profileDetails: {
    flex: 1,
  },
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  photoContainer: {
    marginTop: 4,
  },
  rowBetween: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  photoStatusGroup: {
    flex: 1,
  },
  boldLabel: {
    fontWeight: "600",
  },
  photoActionsRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 16,
  },
  placeholderBox: {
    paddingVertical: 12,
  },
  consentItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  consentTextGroup: {
    flex: 1,
    marginRight: 12,
  },
  dangerCard: {
    borderWidth: 1,
  },
  diagnosticsToggle: {
    alignItems: "center",
    paddingVertical: 12,
  },
  diagnosticsCard: {
    borderWidth: 1,
    padding: 14,
    marginTop: 8,
    marginBottom: 24,
  },
  diagRow: {
    marginBottom: 4,
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
  },
});
