import React, { useState } from "react";
import {
  View,
  Text,
  ScrollView,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { api } from "../../src/api/client";
import { useMe } from "../../src/api/hooks";
import { Chip, Input, FormField } from "../../src/components";
import {
  step1Schema,
  step2Schema,
  step3Schema,
  Step1Values,
  Step2Values,
  Step3Values,
} from "../../src/features/onboarding/schemas";

const GENDERS = ["female", "male", "unisex"] as const;
const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];
const BUILDS = ["slim", "athletic", "regular", "broad"] as const;
const OCCASIONS = ["casual", "formal", "party", "ethnic", "work"];

export default function ProfileScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: me } = useMe(true);

  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [v, setV] = useState({
    gender: "female" as "female" | "male" | "unisex",
    topSize: "M",
    bottomSize: "M",
    heightCm: 165,
    weightKg: 60,
    build: "regular" as "slim" | "athletic" | "regular" | "broad",
    budgetMin: 1000,
    budgetMax: 5000,
    occasions: ["casual", "work"] as string[],
  });

  const schemas = [step1Schema, step2Schema, step3Schema];

  const toggleOccasion = (occ: string) => {
    setV((prev) => {
      const exists = prev.occasions.includes(occ);
      const nextOccs = exists
        ? prev.occasions.filter((o) => o !== occ)
        : [...prev.occasions, occ];
      return { ...prev, occasions: nextOccs };
    });
  };

  async function next() {
    setErrors({});
    let parsed: any;

    if (step === 0) {
      parsed = step1Schema.safeParse({
        gender: v.gender,
        topSize: v.topSize,
        bottomSize: v.bottomSize,
      });
    } else if (step === 1) {
      parsed = step2Schema.safeParse({
        heightCm: v.heightCm,
        weightKg: v.weightKg,
        build: v.build,
      });
    } else {
      parsed = step3Schema.safeParse({
        budgetMin: v.budgetMin,
        budgetMax: v.budgetMax,
        occasions: v.occasions,
      });
    }

    if (!parsed.success) {
      const issueMap: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const fieldName = String(issue.path[0] || "general");
        issueMap[fieldName] = issue.message;
      }
      setErrors(issueMap);
      return;
    }

    setSubmitting(true);
    try {
      if (step === 0 || step === 1) {
        // Save profile creation/updates
        await api("/profile/users", {
          method: "POST",
          body: JSON.stringify({
            height_cm: v.heightCm,
            weight_kg: v.weightKg,
            build: v.build,
            consents: [],
          }),
        });
      } else {
        // Save fashion preferences
        if (me?.user_id) {
          await api(`/profile/${me.user_id}/preferences`, {
            method: "PUT",
            body: JSON.stringify({
              budget_min: v.budgetMin,
              budget_max: v.budgetMax,
              categories: v.occasions,
              colors_favored: [],
              colors_avoided: [],
            }),
          });
        }
      }

      if (step < 2) {
        setStep(step + 1);
      } else {
        await qc.invalidateQueries({ queryKey: ["me"] });
        router.push("/onboarding/quiz");
      }
    } catch (e: any) {
      setErrors({ general: e?.message || t("common.error") });
    } finally {
      setSubmitting(false);
    }
  }

  const stepTitles = [
    { title: t("profile.step1Title"), sub: t("profile.step1Subtitle") },
    { title: t("profile.step2Title"), sub: t("profile.step2Subtitle") },
    { title: t("profile.step3Title"), sub: t("profile.step3Subtitle") },
  ];

  return (
    <KeyboardAvoidingView
      style={styles.keyboardContainer}
      behavior={Platform.OS === "android" ? "height" : "padding"}
    >
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        {/* Progress indicator */}
        <View
          style={styles.progressContainer}
          accessibilityRole="header"
          accessibilityLabel={t("profile.stepIndicator", { current: step + 1, total: 3 })}
        >
          <Text style={styles.progressText}>
            {t("profile.stepIndicator", { current: step + 1, total: 3 })}
          </Text>
          <View style={styles.progressBarBackground}>
            <View style={[styles.progressBarFill, { width: `${((step + 1) / 3) * 100}%` }]} />
          </View>
        </View>

        <Text style={styles.title} accessibilityRole="header">
          {stepTitles[step]?.title}
        </Text>
        <Text style={styles.subtitle}>{stepTitles[step]?.sub}</Text>

        {errors.general ? (
          <Text style={styles.generalError} accessibilityLiveRegion="polite">
            {errors.general}
          </Text>
        ) : null}

        {/* STEP 1: Gender, Top Size, Bottom Size */}
        {step === 0 && (
          <View>
            <FormField label={t("profile.gender")} error={errors.gender}>
              <View style={styles.chipRow}>
                {GENDERS.map((g) => (
                  <Chip
                    key={g}
                    label={g.charAt(0).toUpperCase() + g.slice(1)}
                    selected={v.gender === g}
                    onPress={() => setV((p) => ({ ...p, gender: g }))}
                  />
                ))}
              </View>
            </FormField>

            <FormField label={t("profile.topSize")} error={errors.topSize}>
              <View style={styles.chipRow}>
                {SIZES.map((s) => (
                  <Chip
                    key={s}
                    label={s}
                    selected={v.topSize === s}
                    onPress={() => setV((p) => ({ ...p, topSize: s }))}
                  />
                ))}
              </View>
            </FormField>

            <FormField label={t("profile.bottomSize")} error={errors.bottomSize}>
              <View style={styles.chipRow}>
                {SIZES.map((s) => (
                  <Chip
                    key={s}
                    label={s}
                    selected={v.bottomSize === s}
                    onPress={() => setV((p) => ({ ...p, bottomSize: s }))}
                  />
                ))}
              </View>
            </FormField>
          </View>
        )}

        {/* STEP 2: Height, Weight, Build */}
        {step === 1 && (
          <View>
            <FormField label={t("profile.height")} error={errors.heightCm}>
              <Input
                keyboardType="number-pad"
                value={String(v.heightCm || "")}
                onChangeText={(val) =>
                  setV((p) => ({ ...p, heightCm: parseInt(val, 10) || 0 }))
                }
                hasError={Boolean(errors.heightCm)}
                accessibilityLabel={t("profile.height")}
              />
            </FormField>

            <FormField label={t("profile.weight")} error={errors.weightKg}>
              <Input
                keyboardType="number-pad"
                value={String(v.weightKg || "")}
                onChangeText={(val) =>
                  setV((p) => ({ ...p, weightKg: parseInt(val, 10) || 0 }))
                }
                hasError={Boolean(errors.weightKg)}
                accessibilityLabel={t("profile.weight")}
              />
            </FormField>

            <FormField label="Build Type" error={errors.build}>
              <View style={styles.chipRow}>
                {BUILDS.map((b) => (
                  <Chip
                    key={b}
                    label={b.charAt(0).toUpperCase() + b.slice(1)}
                    selected={v.build === b}
                    onPress={() => setV((p) => ({ ...p, build: b }))}
                  />
                ))}
              </View>
            </FormField>
          </View>
        )}

        {/* STEP 3: Budget & Occasions */}
        {step === 2 && (
          <View>
            <FormField label={t("profile.budgetMin")} error={errors.budgetMin}>
              <Input
                keyboardType="number-pad"
                value={String(v.budgetMin || "")}
                onChangeText={(val) =>
                  setV((p) => ({ ...p, budgetMin: parseInt(val, 10) || 0 }))
                }
                hasError={Boolean(errors.budgetMin)}
                accessibilityLabel={t("profile.budgetMin")}
              />
            </FormField>

            <FormField label={t("profile.budgetMax")} error={errors.budgetMax}>
              <Input
                keyboardType="number-pad"
                value={String(v.budgetMax || "")}
                onChangeText={(val) =>
                  setV((p) => ({ ...p, budgetMax: parseInt(val, 10) || 0 }))
                }
                hasError={Boolean(errors.budgetMax)}
                accessibilityLabel={t("profile.budgetMax")}
              />
            </FormField>

            <FormField label={t("profile.occasions")} error={errors.occasions}>
              <View style={styles.chipRow}>
                {OCCASIONS.map((occ) => (
                  <Chip
                    key={occ}
                    label={occ.charAt(0).toUpperCase() + occ.slice(1)}
                    selected={v.occasions.includes(occ)}
                    onPress={() => toggleOccasion(occ)}
                    accessibilityRole="checkbox"
                  />
                ))}
              </View>
            </FormField>
          </View>
        )}

        <View style={styles.buttonRow}>
          {step > 0 && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t("common.back")}
              onPress={() => setStep(step - 1)}
              style={styles.backButton}
              disabled={submitting}
            >
              <Text style={styles.backButtonText}>{t("common.back")}</Text>
            </Pressable>
          )}

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("common.continue")}
            onPress={next}
            disabled={submitting}
            style={[styles.continueButton, step > 0 && { flex: 1 }]}
          >
            {submitting ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.continueButtonText}>{t("common.continue")}</Text>
            )}
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  keyboardContainer: {
    flex: 1,
    backgroundColor: "#FFFFFF",
  },
  container: {
    padding: 24,
    flexGrow: 1,
    justifyContent: "center",
  },
  progressContainer: {
    marginBottom: 20,
  },
  progressText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#6B7280",
    marginBottom: 6,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  progressBarBackground: {
    height: 6,
    backgroundColor: "#E5E7EB",
    borderRadius: 3,
    overflow: "hidden",
  },
  progressBarFill: {
    height: "100%",
    backgroundColor: "#4F46E5",
    borderRadius: 3,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 24,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: 4,
  },
  buttonRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 32,
    gap: 12,
  },
  backButton: {
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    alignItems: "center",
  },
  backButtonText: {
    color: "#374151",
    fontSize: 15,
    fontWeight: "600",
  },
  continueButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
    width: "100%",
  },
  continueButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
  generalError: {
    color: "#DC2626",
    fontSize: 14,
    marginBottom: 16,
  },
});
