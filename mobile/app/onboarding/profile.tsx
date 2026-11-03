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
  TextInput,
} from "react-native";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { api } from "../../src/api/client";
import { useMe } from "../../src/api/hooks";
import { useAuthStore, UserMe } from "../../src/features/auth/authStore";
import {
  step1Schema,
  step2Schema,
  step3Schema,
} from "../../src/features/onboarding/schemas";

const GENDERS = [
  { key: "female", label: "Women" },
  { key: "male", label: "Men" },
  { key: "unisex", label: "All / Unisex" },
] as const;

const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];

const BUILDS = [
  { key: "slim", label: "Slim", desc: "Lean & slender frame" },
  { key: "athletic", label: "Athletic", desc: "Toned & muscular build" },
  { key: "regular", label: "Regular", desc: "Standard, balanced fit" },
  { key: "broad", label: "Broad", desc: "Broader shoulders & frame" },
] as const;

const HEIGHT_PRESETS = [155, 160, 165, 170, 175, 180];
const WEIGHT_PRESETS = [50, 55, 60, 65, 70, 80];

const BUDGET_PRESETS = [
  { label: "Budget", min: 500, max: 2000, desc: "₹500 - ₹2,000" },
  { label: "Popular", min: 1500, max: 5000, desc: "₹1,500 - ₹5,000" },
  { label: "Premium", min: 3000, max: 10000, desc: "₹3,000 - ₹10,000" },
  { label: "Luxury", min: 8000, max: 25000, desc: "₹8,000 - ₹25,000" },
];

const OCCASIONS = [
  { key: "casual", label: "Casual Wear" },
  { key: "work", label: "Work & Office" },
  { key: "formal", label: "Formal & Evening" },
  { key: "party", label: "Party & Club" },
  { key: "ethnic", label: "Ethnic & Festive" },
  { key: "vacation", label: "Vacation / Resort" },
];

export default function ProfileScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data: me } = useMe(true);

  const [step, setStep] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Basic Profile (Step 0)
  const [gender, setGender] = useState<"female" | "male" | "unisex">("female");
  const [topSize, setTopSize] = useState("M");
  const [bottomSize, setBottomSize] = useState("M");

  // Measurements (Step 1)
  const [heightText, setHeightText] = useState("165");
  const [weightText, setWeightText] = useState("60");
  const [build, setBuild] = useState<"slim" | "athletic" | "regular" | "broad">("regular");

  // Style & Budget (Step 2)
  const [budgetMinText, setBudgetMinText] = useState("1000");
  const [budgetMaxText, setBudgetMaxText] = useState("5000");
  const [occasions, setOccasions] = useState<string[]>(["casual", "work"]);

  const toggleOccasion = (key: string) => {
    setOccasions((prev) => {
      const exists = prev.includes(key);
      if (exists) {
        return prev.filter((o) => o !== key);
      }
      return [...prev, key];
    });
  };

  const adjustHeight = (delta: number) => {
    const cur = parseInt(heightText, 10) || 165;
    const nextVal = Math.min(230, Math.max(120, cur + delta));
    setHeightText(String(nextVal));
    if (errors.heightCm) {
      setErrors((p) => ({ ...p, heightCm: "" }));
    }
  };

  const adjustWeight = (delta: number) => {
    const cur = parseInt(weightText, 10) || 60;
    const nextVal = Math.min(250, Math.max(30, cur + delta));
    setWeightText(String(nextVal));
    if (errors.weightKg) {
      setErrors((p) => ({ ...p, weightKg: "" }));
    }
  };

  async function handleNext() {
    setErrors({});

    // STEP 0: Validate basic sizing locally, then smoothly advance
    if (step === 0) {
      const parsed = step1Schema.safeParse({
        gender,
        topSize,
        bottomSize,
      });

      if (!parsed.success) {
        const issueMap: Record<string, string> = {};
        for (const issue of parsed.error.issues) {
          const fieldName = String(issue.path[0] || "general");
          issueMap[fieldName] = issue.message;
        }
        setErrors(issueMap);
        return;
      }

      setStep(1);
      return;
    }

    // STEP 1: Validate measurements and save body metrics
    if (step === 1) {
      const heightVal = parseInt(heightText.trim(), 10);
      const weightTrim = weightText.trim();
      const weightVal = weightTrim ? parseInt(weightTrim, 10) : undefined;

      const parsed = step2Schema.safeParse({
        heightCm: heightVal,
        weightKg: weightVal,
        build,
      });

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
        await api("/profile/users", {
          method: "POST",
          body: JSON.stringify({
            height_cm: heightVal,
            weight_kg: weightVal ?? null,
            build,
            consents: [],
          }),
        });
        setStep(2);
      } catch (err: any) {
        setErrors({ general: err?.message || t("common.error") });
      } finally {
        setSubmitting(false);
      }
      return;
    }

    // STEP 2: Validate budget & occasions, update preferences & complete profile
    if (step === 2) {
      const bMin = parseInt(budgetMinText.trim(), 10);
      const bMax = parseInt(budgetMaxText.trim(), 10);

      const parsed = step3Schema.safeParse({
        budgetMin: bMin,
        budgetMax: bMax,
        occasions,
      });

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
        // Ensure body profile is up to date
        const heightVal = parseInt(heightText.trim(), 10) || 165;
        const weightTrim = weightText.trim();
        const weightVal = weightTrim ? parseInt(weightTrim, 10) : null;

        await api("/profile/users", {
          method: "POST",
          body: JSON.stringify({
            height_cm: heightVal,
            weight_kg: weightVal,
            build,
            consents: [],
          }),
        });

        // Save preferences
        await api("/profile/preferences", {
          method: "PUT",
          body: JSON.stringify({
            budget_min: bMin,
            budget_max: bMax,
            categories: occasions,
            colors_favored: [],
            colors_avoided: [],
          }),
        });

        // Refresh Me cache and update auth store
        const updatedMe = await api<UserMe>("/me");
        qc.setQueryData(["me"], updatedMe);
        useAuthStore.getState().setMe(updatedMe);
        await qc.invalidateQueries({ queryKey: ["me"] });

        router.replace("/onboarding/quiz");
      } catch (err: any) {
        setErrors({ general: err?.message || t("common.error") });
      } finally {
        setSubmitting(false);
      }
    }
  }

  const stepMeta = [
    {
      title: t("profile.step1Title", "Basic Profile"),
      sub: t("profile.step1Subtitle", "Tell us about your standard clothing sizes"),
    },
    {
      title: t("profile.step2Title", "Measurements & Build"),
      sub: t("profile.step2Subtitle", "Calibrate 3D fit and drape simulation"),
    },
    {
      title: t("profile.step3Title", "Style & Budget"),
      sub: t("profile.step3Subtitle", "Personalize your recommendations and wardrobe feed"),
    },
  ];

  return (
    <KeyboardAvoidingView
      style={styles.keyboardContainer}
      behavior={Platform.OS === "android" ? "height" : "padding"}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Progress indicator */}
        <View
          style={styles.progressContainer}
          accessibilityRole="header"
          accessibilityLabel={`Step ${step + 1} of 3`}
        >
          <View style={styles.progressRow}>
            <Text style={styles.progressBadge}>Step {step + 1} of 3</Text>
            <Text style={styles.stepNameHeader}>{stepMeta[step]?.title}</Text>
          </View>
          <View style={styles.progressBarBackground}>
            <View style={[styles.progressBarFill, { width: `${((step + 1) / 3) * 100}%` }]} />
          </View>
        </View>

        <Text style={styles.title} accessibilityRole="header">
          {stepMeta[step]?.title}
        </Text>
        <Text style={styles.subtitle}>{stepMeta[step]?.sub}</Text>

        {errors.general ? (
          <View style={styles.errorBanner} accessibilityLiveRegion="polite">
            <Text style={styles.errorBannerText}>{errors.general}</Text>
          </View>
        ) : null}

        {/* STEP 0: Basic Profile (Gender, Top Size, Bottom Size) */}
        {step === 0 && (
          <View style={styles.stepSection}>
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>Department / Gender</Text>
              <Text style={styles.fieldHint}>Choose your primary shopping category</Text>
              <View style={styles.optionsRow}>
                {GENDERS.map((g) => {
                  const isSelected = gender === g.key;
                  return (
                    <Pressable
                      key={g.key}
                      accessibilityRole="button"
                      accessibilityState={{ selected: isSelected }}
                      onPress={() => setGender(g.key)}
                      style={[styles.segmentBtn, isSelected && styles.segmentBtnActive]}
                    >
                      <Text
                        style={[
                          styles.segmentBtnText,
                          isSelected && styles.segmentBtnTextActive,
                        ]}
                      >
                        {g.label}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
              {errors.gender ? <Text style={styles.errorText}>{errors.gender}</Text> : null}
            </View>

            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>{t("profile.topSize", "Top Size")}</Text>
              <Text style={styles.fieldHint}>Standard shirts, tops, jackets</Text>
              <View style={styles.chipGrid}>
                {SIZES.map((s) => {
                  const isSelected = topSize === s;
                  return (
                    <Pressable
                      key={s}
                      accessibilityRole="button"
                      accessibilityState={{ selected: isSelected }}
                      onPress={() => setTopSize(s)}
                      style={[styles.sizeChip, isSelected && styles.sizeChipActive]}
                    >
                      <Text
                        style={[styles.sizeChipText, isSelected && styles.sizeChipTextActive]}
                      >
                        {s}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
              {errors.topSize ? <Text style={styles.errorText}>{errors.topSize}</Text> : null}
            </View>

            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>{t("profile.bottomSize", "Bottom Size")}</Text>
              <Text style={styles.fieldHint}>Standard jeans, trousers, skirts</Text>
              <View style={styles.chipGrid}>
                {SIZES.map((s) => {
                  const isSelected = bottomSize === s;
                  return (
                    <Pressable
                      key={s}
                      accessibilityRole="button"
                      accessibilityState={{ selected: isSelected }}
                      onPress={() => setBottomSize(s)}
                      style={[styles.sizeChip, isSelected && styles.sizeChipActive]}
                    >
                      <Text
                        style={[styles.sizeChipText, isSelected && styles.sizeChipTextActive]}
                      >
                        {s}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
              {errors.bottomSize ? <Text style={styles.errorText}>{errors.bottomSize}</Text> : null}
            </View>
          </View>
        )}

        {/* STEP 1: Measurements (Height, Weight, Silhouette Build) */}
        {step === 1 && (
          <View style={styles.stepSection}>
            {/* Height Card */}
            <View style={styles.measureCard}>
              <View style={styles.measureHeader}>
                <View>
                  <Text style={styles.fieldLabel}>Height</Text>
                  <Text style={styles.fieldHint}>Recommended: 120 – 230 cm</Text>
                </View>
                <View style={styles.unitBadge}>
                  <Text style={styles.unitBadgeText}>cm</Text>
                </View>
              </View>

              <View style={styles.stepperContainer}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Decrease height by 1 cm"
                  onPress={() => adjustHeight(-1)}
                  style={styles.stepperBtn}
                >
                  <Text style={styles.stepperBtnText}>−</Text>
                </Pressable>

                <View style={styles.measureInputWrapper}>
                  <TextInput
                    keyboardType="number-pad"
                    value={heightText}
                    onChangeText={(val) => {
                      setHeightText(val.replace(/[^0-9]/g, ""));
                      if (errors.heightCm) {
                        setErrors((p) => ({ ...p, heightCm: "" }));
                      }
                    }}
                    style={[styles.measureInput, Boolean(errors.heightCm) && styles.inputError]}
                    accessibilityLabel="Height in centimeters"
                    maxLength={3}
                  />
                  <Text style={styles.measureUnitSuffix}>cm</Text>
                </View>

                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Increase height by 1 cm"
                  onPress={() => adjustHeight(1)}
                  style={styles.stepperBtn}
                >
                  <Text style={styles.stepperBtnText}>+</Text>
                </Pressable>
              </View>

              {/* Quick height presets */}
              <View style={styles.presetRow}>
                {HEIGHT_PRESETS.map((h) => (
                  <Pressable
                    key={h}
                    onPress={() => {
                      setHeightText(String(h));
                      if (errors.heightCm) setErrors((p) => ({ ...p, heightCm: "" }));
                    }}
                    style={[
                      styles.presetChip,
                      heightText === String(h) && styles.presetChipActive,
                    ]}
                  >
                    <Text
                      style={[
                        styles.presetChipText,
                        heightText === String(h) && styles.presetChipTextActive,
                      ]}
                    >
                      {h}
                    </Text>
                  </Pressable>
                ))}
              </View>
              {errors.heightCm ? <Text style={styles.errorText}>{errors.heightCm}</Text> : null}
            </View>

            {/* Weight Card */}
            <View style={styles.measureCard}>
              <View style={styles.measureHeader}>
                <View>
                  <Text style={styles.fieldLabel}>Weight (Optional)</Text>
                  <Text style={styles.fieldHint}>Recommended: 30 – 250 kg</Text>
                </View>
                <View style={styles.unitBadge}>
                  <Text style={styles.unitBadgeText}>kg</Text>
                </View>
              </View>

              <View style={styles.stepperContainer}>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Decrease weight by 1 kg"
                  onPress={() => adjustWeight(-1)}
                  style={styles.stepperBtn}
                >
                  <Text style={styles.stepperBtnText}>−</Text>
                </Pressable>

                <View style={styles.measureInputWrapper}>
                  <TextInput
                    keyboardType="number-pad"
                    value={weightText}
                    placeholder="Optional"
                    placeholderTextColor="#9CA3AF"
                    onChangeText={(val) => {
                      setWeightText(val.replace(/[^0-9]/g, ""));
                      if (errors.weightKg) {
                        setErrors((p) => ({ ...p, weightKg: "" }));
                      }
                    }}
                    style={[styles.measureInput, Boolean(errors.weightKg) && styles.inputError]}
                    accessibilityLabel="Weight in kilograms"
                    maxLength={3}
                  />
                  <Text style={styles.measureUnitSuffix}>kg</Text>
                </View>

                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel="Increase weight by 1 kg"
                  onPress={() => adjustWeight(1)}
                  style={styles.stepperBtn}
                >
                  <Text style={styles.stepperBtnText}>+</Text>
                </Pressable>
              </View>

              {/* Quick weight presets */}
              <View style={styles.presetRow}>
                {WEIGHT_PRESETS.map((w) => (
                  <Pressable
                    key={w}
                    onPress={() => {
                      setWeightText(String(w));
                      if (errors.weightKg) setErrors((p) => ({ ...p, weightKg: "" }));
                    }}
                    style={[
                      styles.presetChip,
                      weightText === String(w) && styles.presetChipActive,
                    ]}
                  >
                    <Text
                      style={[
                        styles.presetChipText,
                        weightText === String(w) && styles.presetChipTextActive,
                      ]}
                    >
                      {w}
                    </Text>
                  </Pressable>
                ))}
              </View>
              {errors.weightKg ? <Text style={styles.errorText}>{errors.weightKg}</Text> : null}
            </View>

            {/* Build Selector Grid */}
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>Body Silhouette & Build</Text>
              <Text style={styles.fieldHint}>Select the profile that closest mirrors your body</Text>
              <View style={styles.buildGrid}>
                {BUILDS.map((b) => {
                  const isSelected = build === b.key;
                  return (
                    <Pressable
                      key={b.key}
                      accessibilityRole="button"
                      accessibilityState={{ selected: isSelected }}
                      onPress={() => setBuild(b.key)}
                      style={[styles.buildCard, isSelected && styles.buildCardActive]}
                    >
                      <View style={styles.buildCardTop}>
                        <Text
                          style={[
                            styles.buildCardTitle,
                            isSelected && styles.buildCardTitleActive,
                          ]}
                        >
                          {b.label}
                        </Text>
                        {isSelected && <Text style={styles.checkIcon}>✓</Text>}
                      </View>
                      <Text style={styles.buildCardDesc}>{b.desc}</Text>
                    </Pressable>
                  );
                })}
              </View>
              {errors.build ? <Text style={styles.errorText}>{errors.build}</Text> : null}
            </View>
          </View>
        )}

        {/* STEP 2: Style & Budget (Budget Range, Occasions) */}
        {step === 2 && (
          <View style={styles.stepSection}>
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>Budget per Garment (₹ INR)</Text>
              <Text style={styles.fieldHint}>Set the price window for your daily recommendations</Text>

              {/* Preset Budget Ranges */}
              <View style={styles.budgetPresetsGrid}>
                {BUDGET_PRESETS.map((bp) => {
                  const isSelected =
                    budgetMinText === String(bp.min) && budgetMaxText === String(bp.max);
                  return (
                    <Pressable
                      key={bp.label}
                      onPress={() => {
                        setBudgetMinText(String(bp.min));
                        setBudgetMaxText(String(bp.max));
                        setErrors((p) => ({ ...p, budgetMin: "", budgetMax: "" }));
                      }}
                      style={[
                        styles.budgetPresetCard,
                        isSelected && styles.budgetPresetCardActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.budgetPresetTitle,
                          isSelected && styles.budgetPresetTitleActive,
                        ]}
                      >
                        {bp.label}
                      </Text>
                      <Text style={styles.budgetPresetDesc}>{bp.desc}</Text>
                    </Pressable>
                  );
                })}
              </View>

              {/* Custom Min / Max inputs */}
              <View style={styles.budgetInputsRow}>
                <View style={styles.budgetInputCol}>
                  <Text style={styles.inputSubLabel}>Minimum (₹)</Text>
                  <View style={styles.currencyInputWrapper}>
                    <Text style={styles.currencyPrefix}>₹</Text>
                    <TextInput
                      keyboardType="number-pad"
                      value={budgetMinText}
                      onChangeText={(val) => {
                        setBudgetMinText(val.replace(/[^0-9]/g, ""));
                        setErrors((p) => ({ ...p, budgetMin: "" }));
                      }}
                      style={[
                        styles.currencyInput,
                        Boolean(errors.budgetMin) && styles.inputError,
                      ]}
                      placeholder="0"
                      placeholderTextColor="#9CA3AF"
                    />
                  </View>
                  {errors.budgetMin ? (
                    <Text style={styles.errorText}>{errors.budgetMin}</Text>
                  ) : null}
                </View>

                <View style={styles.budgetInputCol}>
                  <Text style={styles.inputSubLabel}>Maximum (₹)</Text>
                  <View style={styles.currencyInputWrapper}>
                    <Text style={styles.currencyPrefix}>₹</Text>
                    <TextInput
                      keyboardType="number-pad"
                      value={budgetMaxText}
                      onChangeText={(val) => {
                        setBudgetMaxText(val.replace(/[^0-9]/g, ""));
                        setErrors((p) => ({ ...p, budgetMax: "" }));
                      }}
                      style={[
                        styles.currencyInput,
                        Boolean(errors.budgetMax) && styles.inputError,
                      ]}
                      placeholder="5000"
                      placeholderTextColor="#9CA3AF"
                    />
                  </View>
                  {errors.budgetMax ? (
                    <Text style={styles.errorText}>{errors.budgetMax}</Text>
                  ) : null}
                </View>
              </View>
            </View>

            {/* Occasions Multi-Select */}
            <View style={styles.fieldGroup}>
              <Text style={styles.fieldLabel}>Frequent Occasions</Text>
              <Text style={styles.fieldHint}>Select one or more occasions you dress for</Text>
              <View style={styles.occasionsGrid}>
                {OCCASIONS.map((occ) => {
                  const isSelected = occasions.includes(occ.key);
                  return (
                    <Pressable
                      key={occ.key}
                      accessibilityRole="checkbox"
                      accessibilityState={{ selected: isSelected }}
                      onPress={() => {
                        toggleOccasion(occ.key);
                        if (errors.occasions) {
                          setErrors((p) => ({ ...p, occasions: "" }));
                        }
                      }}
                      style={[styles.occasionCard, isSelected && styles.occasionCardActive]}
                    >
                      <Text
                        style={[
                          styles.occasionCardText,
                          isSelected && styles.occasionCardTextActive,
                        ]}
                      >
                        {occ.label}
                      </Text>
                      {isSelected ? <Text style={styles.checkIconSmall}>✓</Text> : null}
                    </Pressable>
                  );
                })}
              </View>
              {errors.occasions ? (
                <Text style={styles.errorText}>{errors.occasions}</Text>
              ) : null}
            </View>
          </View>
        )}

        {/* Action Buttons */}
        <View style={styles.buttonRow}>
          {step > 0 && (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t("common.back", "Back")}
              onPress={() => setStep(step - 1)}
              style={styles.backButton}
              disabled={submitting}
            >
              <Text style={styles.backButtonText}>{t("common.back", "Back")}</Text>
            </Pressable>
          )}

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={
              step === 2
                ? t("profile.completeButton", "Continue to Style Quiz")
                : t("common.continue", "Continue")
            }
            onPress={handleNext}
            disabled={submitting}
            style={[styles.continueButton, step > 0 && { flex: 1 }]}
          >
            {submitting ? (
              <ActivityIndicator color="#FFFFFF" size="small" />
            ) : (
              <Text style={styles.continueButtonText}>
                {step === 2 ? "Continue to Style Quiz →" : t("common.continue", "Continue")}
              </Text>
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
    backgroundColor: "#FAFAFA",
  },
  container: {
    padding: 24,
    paddingTop: 36,
    paddingBottom: 40,
    flexGrow: 1,
  },
  progressContainer: {
    marginBottom: 20,
  },
  progressRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  progressBadge: {
    fontSize: 12,
    fontWeight: "700",
    color: "#4F46E5",
    textTransform: "uppercase",
    letterSpacing: 0.8,
  },
  stepNameHeader: {
    fontSize: 12,
    fontWeight: "500",
    color: "#6B7280",
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
    fontSize: 26,
    fontWeight: "800",
    color: "#111827",
    marginBottom: 6,
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 14,
    color: "#4B5563",
    marginBottom: 24,
    lineHeight: 20,
  },
  errorBanner: {
    backgroundColor: "#FEF2F2",
    borderColor: "#FCA5A5",
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorBannerText: {
    color: "#DC2626",
    fontSize: 14,
    fontWeight: "500",
  },
  stepSection: {
    marginBottom: 12,
  },
  fieldGroup: {
    marginBottom: 24,
  },
  fieldLabel: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 2,
  },
  fieldHint: {
    fontSize: 13,
    color: "#6B7280",
    marginBottom: 10,
  },
  errorText: {
    color: "#DC2626",
    fontSize: 12,
    fontWeight: "500",
    marginTop: 6,
  },

  // Options & Segment buttons
  optionsRow: {
    flexDirection: "row",
    gap: 8,
  },
  segmentBtn: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 10,
    backgroundColor: "#FFFFFF",
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
    alignItems: "center",
  },
  segmentBtnActive: {
    borderColor: "#4F46E5",
    backgroundColor: "#EEF2FF",
  },
  segmentBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#4B5563",
  },
  segmentBtnTextActive: {
    color: "#4F46E5",
    fontWeight: "700",
  },

  // Size Chips
  chipGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  sizeChip: {
    minWidth: 48,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: "#FFFFFF",
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
    alignItems: "center",
    justifyContent: "center",
  },
  sizeChipActive: {
    borderColor: "#4F46E5",
    backgroundColor: "#EEF2FF",
  },
  sizeChipText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#374151",
  },
  sizeChipTextActive: {
    color: "#4F46E5",
    fontWeight: "700",
  },

  // Measurements card
  measureCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    padding: 18,
    marginBottom: 20,
    shadowColor: "#000000",
    shadowOpacity: 0.03,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  measureHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 14,
  },
  unitBadge: {
    backgroundColor: "#EEF2FF",
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#C7D2FE",
  },
  unitBadgeText: {
    fontSize: 12,
    fontWeight: "700",
    color: "#4F46E5",
  },
  stepperContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 14,
    marginBottom: 14,
  },
  stepperBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#F3F4F6",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  stepperBtnText: {
    fontSize: 22,
    fontWeight: "600",
    color: "#374151",
    lineHeight: 24,
  },
  measureInputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#F9FAFB",
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: "#D1D5DB",
    paddingHorizontal: 16,
    paddingVertical: 4,
    minWidth: 140,
  },
  measureInput: {
    fontSize: 26,
    fontWeight: "800",
    color: "#111827",
    textAlign: "center",
    paddingVertical: 6,
    minWidth: 70,
  },
  measureUnitSuffix: {
    fontSize: 16,
    fontWeight: "600",
    color: "#6B7280",
    marginLeft: 4,
  },
  inputError: {
    borderColor: "#DC2626",
    backgroundColor: "#FEF2F2",
  },
  presetRow: {
    flexDirection: "row",
    justifyContent: "center",
    flexWrap: "wrap",
    gap: 6,
    marginTop: 4,
  },
  presetChip: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: "#F3F4F6",
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  presetChipActive: {
    backgroundColor: "#EEF2FF",
    borderColor: "#818CF8",
  },
  presetChipText: {
    fontSize: 13,
    fontWeight: "500",
    color: "#4B5563",
  },
  presetChipTextActive: {
    color: "#4F46E5",
    fontWeight: "700",
  },

  // Build Grid
  buildGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    marginTop: 4,
  },
  buildCard: {
    width: "48%",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
    padding: 14,
  },
  buildCardActive: {
    borderColor: "#4F46E5",
    backgroundColor: "#EEF2FF",
  },
  buildCardTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 4,
  },
  buildCardTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1F2937",
  },
  buildCardTitleActive: {
    color: "#4F46E5",
  },
  buildCardDesc: {
    fontSize: 12,
    color: "#6B7280",
    lineHeight: 16,
  },
  checkIcon: {
    fontSize: 15,
    fontWeight: "800",
    color: "#4F46E5",
  },
  checkIconSmall: {
    fontSize: 14,
    fontWeight: "700",
    color: "#4F46E5",
    marginLeft: 6,
  },

  // Budget Presets
  budgetPresetsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginBottom: 16,
  },
  budgetPresetCard: {
    width: "48%",
    backgroundColor: "#FFFFFF",
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
    padding: 12,
  },
  budgetPresetCardActive: {
    borderColor: "#4F46E5",
    backgroundColor: "#EEF2FF",
  },
  budgetPresetTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#1F2937",
    marginBottom: 2,
  },
  budgetPresetTitleActive: {
    color: "#4F46E5",
  },
  budgetPresetDesc: {
    fontSize: 12,
    color: "#6B7280",
  },
  budgetInputsRow: {
    flexDirection: "row",
    gap: 12,
  },
  budgetInputCol: {
    flex: 1,
  },
  inputSubLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "#4B5563",
    marginBottom: 6,
  },
  currencyInputWrapper: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    paddingHorizontal: 12,
  },
  currencyPrefix: {
    fontSize: 16,
    fontWeight: "700",
    color: "#6B7280",
    marginRight: 6,
  },
  currencyInput: {
    flex: 1,
    paddingVertical: 10,
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
  },

  // Occasions
  occasionsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 4,
  },
  occasionCard: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
  },
  occasionCardActive: {
    borderColor: "#4F46E5",
    backgroundColor: "#EEF2FF",
  },
  occasionCardText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#374151",
  },
  occasionCardTextActive: {
    color: "#4F46E5",
  },

  // Action Buttons
  buttonRow: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 24,
    marginBottom: 20,
    gap: 12,
  },
  backButton: {
    paddingVertical: 14,
    paddingHorizontal: 22,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: "#D1D5DB",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
  },
  backButtonText: {
    color: "#374151",
    fontSize: 15,
    fontWeight: "600",
  },
  continueButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    width: "100%",
    shadowColor: "#4F46E5",
    shadowOpacity: 0.25,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 3 },
    elevation: 3,
  },
  continueButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "700",
  },
});
