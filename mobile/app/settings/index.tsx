import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Platform,
} from "react-native";
import { useRouter } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../../src/features/auth/authStore";
import { useDerivedProfile, UserPhotoItem } from "../../src/api/hooks";
import { api } from "../../src/api/client";

export default function SettingsScreen() {
  const router = useRouter();
  const qc = useQueryClient();
  const { signOut, me } = useAuthStore();
  const userId = me?.user_id;

  const { data: profile, isLoading: isProfileLoading } = useDerivedProfile(userId, Boolean(userId));

  const [isDeletingPhoto, setIsDeletingPhoto] = useState(false);
  const [isRevokingConsent, setIsRevokingConsent] = useState(false);
  const [isErasingAccount, setIsErasingAccount] = useState(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  const activePhoto: UserPhotoItem | undefined = profile?.photos?.find(
    (p) => p.status === "accepted"
  ) || profile?.photos?.[0];

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
          await qc.invalidateQueries({ queryKey: ["derivedProfile", userId] });
          await qc.invalidateQueries({ queryKey: ["me"] });
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
          await qc.invalidateQueries({ queryKey: ["derivedProfile", userId] });
          await qc.invalidateQueries({ queryKey: ["me"] });
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

  return (
    <ScrollView contentContainerStyle={styles.container} testID="settings-screen">
      <Text style={styles.title}>Settings</Text>
      <Text style={styles.subtitle}>Account, Privacy & DPDP Controls</Text>

      {actionNotice && (
        <View style={styles.noticeBanner}>
          <Text style={styles.noticeText}>{actionNotice}</Text>
        </View>
      )}

      {/* 1. User Identity */}
      <View style={styles.card} testID="user-identity-card">
        <Text style={styles.cardHeader}>User Identity</Text>
        <Text style={styles.infoText}>User ID: {userId || "Unknown"}</Text>
        <Text style={styles.infoText}>Roles: {me?.roles?.join(", ") || "user"}</Text>
      </View>

      {/* 2. Reference Photo Card */}
      <View style={styles.card} testID="reference-photo-card">
        <Text style={styles.cardHeader}>Active Reference Photo</Text>
        {isProfileLoading ? (
          <ActivityIndicator size="small" color="#4F46E5" style={{ marginVertical: 12 }} />
        ) : activePhoto ? (
          <View>
            <View style={styles.rowBetween}>
              <Text style={styles.infoText}>Status: {activePhoto.status}</Text>
              <View
                style={[
                  styles.badge,
                  activePhoto.status === "accepted" ? styles.badgeSuccess : styles.badgeWarning,
                ]}
              >
                <Text
                  style={[
                    styles.badgeText,
                    activePhoto.status === "accepted"
                      ? styles.badgeTextSuccess
                      : styles.badgeTextWarning,
                  ]}
                >
                  {activePhoto.status.toUpperCase()}
                </Text>
              </View>
            </View>
            <Text style={styles.secondaryText}>Photo ID: {activePhoto.id}</Text>
            <TouchableOpacity
              style={styles.deletePhotoButton}
              onPress={handleDeletePhoto}
              disabled={isDeletingPhoto}
              accessibilityRole="button"
              accessibilityLabel="Delete reference photo"
              testID="delete-photo-button"
            >
              {isDeletingPhoto ? (
                <ActivityIndicator size="small" color="#DC2626" />
              ) : (
                <Text style={styles.deletePhotoButtonText}>Delete Reference Photo</Text>
              )}
            </TouchableOpacity>
          </View>
        ) : (
          <View>
            <Text style={styles.placeholderText}>
              No active reference photo on file. Upload a portrait to enable virtual try-on.
            </Text>
            <TouchableOpacity
              style={styles.secondaryButton}
              onPress={() => router.push("/onboarding/capture")}
              accessibilityRole="button"
              accessibilityLabel="Upload portrait photo"
            >
              <Text style={styles.secondaryButtonText}>Upload Photo</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>

      {/* 3. DPDP Consent Management */}
      <View style={styles.card} testID="consent-controls-card">
        <Text style={styles.cardHeader}>DPDP Privacy & Consent</Text>
        <View style={styles.consentItem}>
          <Text style={styles.consentLabel}>Body Photo Processing</Text>
          <View
            style={[
              styles.badge,
              profile?.consents?.body_photo ? styles.badgeSuccess : styles.badgeInactive,
            ]}
          >
            <Text
              style={[
                styles.badgeText,
                profile?.consents?.body_photo
                  ? styles.badgeTextSuccess
                  : styles.badgeTextInactive,
              ]}
            >
              {profile?.consents?.body_photo ? "GRANTED" : "NOT GRANTED"}
            </Text>
          </View>
        </View>

        <View style={styles.consentItem}>
          <Text style={styles.consentLabel}>Terms & Privacy Policy</Text>
          <View
            style={[
              styles.badge,
              profile?.consents?.terms_and_privacy ? styles.badgeSuccess : styles.badgeInactive,
            ]}
          >
            <Text
              style={[
                styles.badgeText,
                profile?.consents?.terms_and_privacy
                  ? styles.badgeTextSuccess
                  : styles.badgeTextInactive,
              ]}
            >
              {profile?.consents?.terms_and_privacy ? "GRANTED" : "NOT GRANTED"}
            </Text>
          </View>
        </View>

        <View style={styles.consentItem}>
          <Text style={styles.consentLabel}>Body Measurements</Text>
          <View
            style={[
              styles.badge,
              profile?.consents?.measurements ? styles.badgeSuccess : styles.badgeInactive,
            ]}
          >
            <Text
              style={[
                styles.badgeText,
                profile?.consents?.measurements
                  ? styles.badgeTextSuccess
                  : styles.badgeTextInactive,
              ]}
            >
              {profile?.consents?.measurements ? "GRANTED" : "NOT GRANTED"}
            </Text>
          </View>
        </View>

        {Boolean(profile?.consents?.body_photo) && (
          <TouchableOpacity
            style={styles.revokeConsentButton}
            onPress={handleRevokeConsent}
            disabled={isRevokingConsent}
            accessibilityRole="button"
            accessibilityLabel="Revoke body photo consent"
            testID="revoke-consent-button"
          >
            {isRevokingConsent ? (
              <ActivityIndicator size="small" color="#D97706" />
            ) : (
              <Text style={styles.revokeConsentText}>Revoke Body Photo Consent</Text>
            )}
          </TouchableOpacity>
        )}
      </View>

      {/* 4. Danger Zone: Erase Account */}
      <View style={[styles.card, styles.dangerCard]}>
        <Text style={[styles.cardHeader, styles.dangerHeader]}>
          Account Erasure (Right to be Forgotten)
        </Text>
        <Text style={styles.dangerDescription}>
          Permanently erase your identity, uploaded photos, derived body measurements, and try-on
          records in compliance with DPDP data erasure rights.
        </Text>
        <TouchableOpacity
          style={styles.eraseButton}
          onPress={handleEraseAccount}
          disabled={isErasingAccount}
          accessibilityRole="button"
          accessibilityLabel="Erase account and all data"
          testID="erase-account-button"
        >
          {isErasingAccount ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={styles.eraseButtonText}>Revoke Consent & Erase Account</Text>
          )}
        </TouchableOpacity>
      </View>

      {/* 5. Sign Out */}
      <TouchableOpacity
        style={styles.signOutButton}
        onPress={handleSignOut}
        accessibilityRole="button"
        accessibilityLabel="Sign out"
        testID="sign-out-button"
      >
        <Text style={styles.signOutText}>Sign Out</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    backgroundColor: "#F9FAFB",
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 20,
  },
  noticeBanner: {
    backgroundColor: "#EFF6FF",
    borderWidth: 1,
    borderColor: "#BFDBFE",
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  noticeText: {
    fontSize: 13,
    color: "#1D4ED8",
    textAlign: "center",
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  cardHeader: {
    fontSize: 15,
    fontWeight: "600",
    color: "#1F2937",
    marginBottom: 12,
  },
  infoText: {
    fontSize: 13,
    color: "#4B5563",
    marginBottom: 4,
  },
  secondaryText: {
    fontSize: 11,
    color: "#9CA3AF",
    marginBottom: 12,
  },
  placeholderText: {
    fontSize: 13,
    color: "#6B7280",
    lineHeight: 18,
    marginBottom: 12,
  },
  rowBetween: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  badgeSuccess: {
    backgroundColor: "#DCFCE7",
  },
  badgeWarning: {
    backgroundColor: "#FEF3C7",
  },
  badgeInactive: {
    backgroundColor: "#F3F4F6",
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "600",
  },
  badgeTextSuccess: {
    color: "#15803D",
  },
  badgeTextWarning: {
    color: "#B45309",
  },
  badgeTextInactive: {
    color: "#6B7280",
  },
  consentItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#F3F4F6",
  },
  consentLabel: {
    fontSize: 13,
    color: "#374151",
    fontWeight: "500",
  },
  deletePhotoButton: {
    borderWidth: 1,
    borderColor: "#FECACA",
    backgroundColor: "#FEF2F2",
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 8,
  },
  deletePhotoButtonText: {
    color: "#DC2626",
    fontSize: 13,
    fontWeight: "600",
  },
  secondaryButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
  },
  secondaryButtonText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "600",
  },
  revokeConsentButton: {
    borderWidth: 1,
    borderColor: "#FDE68A",
    backgroundColor: "#FFFBEB",
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: "center",
    marginTop: 12,
  },
  revokeConsentText: {
    color: "#B45309",
    fontSize: 13,
    fontWeight: "600",
  },
  dangerCard: {
    borderColor: "#FECACA",
    borderWidth: 1,
  },
  dangerHeader: {
    color: "#991B1B",
  },
  dangerDescription: {
    fontSize: 12,
    color: "#6B7280",
    lineHeight: 18,
    marginBottom: 14,
  },
  eraseButton: {
    backgroundColor: "#DC2626",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  eraseButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
  signOutButton: {
    backgroundColor: "#4B5563",
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 8,
    marginBottom: 24,
  },
  signOutText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "600",
  },
});
