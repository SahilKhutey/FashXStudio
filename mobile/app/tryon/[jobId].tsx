import React, { useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Dimensions,
} from "react-native";
import { Image } from "expo-image";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { useJob, useTryOnFeedback } from "../../src/features/tryon/useTryOn";
import { useSaveToWardrobe } from "../../src/features/wardrobe/hooks";
import { Chip } from "../../src/components/Chip";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

const LOOKS_WRONG_CHIPS = [
  "Fit looks unnatural",
  "Garment distorted",
  "Color inaccurate",
  "Blurry or artifacts",
];

export default function TryOnJobScreen() {
  const { jobId } = useLocalSearchParams<{ jobId: string }>();
  const { t } = useTranslation();
  const router = useRouter();

  const {
    data: job,
    isLoading,
    isError,
    refetch,
    isTakingLongerThanUsual,
  } = useJob(jobId || null);

  const { mutate: submitFeedback, isPending: isSubmittingFeedback } = useTryOnFeedback();
  const { mutate: saveToWardrobe, isPending: isSavingWardrobe } = useSaveToWardrobe();

  const [showingBefore, setShowingBefore] = useState(false);
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [selectedChips, setSelectedChips] = useState<string[]>([]);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleRating = (rating: number) => {
    if (!jobId || feedbackSent) return;
    setSelectedRating(rating);
    submitFeedback(
      { jobId, rating },
      {
        onSuccess: () => setFeedbackSent(true),
      }
    );
  };

  const toggleChip = (chip: string) => {
    if (selectedChips.includes(chip)) {
      setSelectedChips(selectedChips.filter((c) => c !== chip));
    } else {
      setSelectedChips([...selectedChips, chip]);
    }
  };

  const handleSaveLook = () => {
    if (!job) return;
    // Save to wardrobe with try-on artifact key
    saveToWardrobe(
      {
        garmentId: job.artifact_key ? job.artifact_key.split(":")[0] || job.job_id : job.job_id,
        tryonArtifactId: job.artifact_key,
      },
      {
        onSuccess: () => setSavedSuccess(true),
      }
    );
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={styles.loadingText}>{t("tryon.statusQueued")}</Text>
      </View>
    );
  }

  if (isError || !job) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorTitle}>{t("common.error")}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>{t("common.retry")}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const isCompleted = job.status === "completed";
  const isFailed = job.status === "failed" || job.status === "cancelled";
  const isInProgress = !isCompleted && !isFailed;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Longer than usual notice banner */}
      {isInProgress && isTakingLongerThanUsual && (
        <View style={styles.warningBanner}>
          <Text style={styles.warningBannerText}>
            ⏱️ {t("tryon.takingLonger")}
          </Text>
        </View>
      )}

      {/* In-progress state */}
      {isInProgress && (
        <View style={styles.progressContainer}>
          <View style={styles.animationBox}>
            <ActivityIndicator size="large" color="#4F46E5" />
            <Text style={styles.progressIcon}>✨</Text>
          </View>

          <Text style={styles.progressTitle}>
            {job.status === "queued"
              ? t("tryon.statusQueued")
              : job.status === "quality_check"
              ? t("tryon.statusQuality")
              : t("tryon.statusProcessing")}
          </Text>
          <Text style={styles.progressSubtitle}>
            Pipeline phase: {job.status}
          </Text>
        </View>
      )}

      {/* Failed state */}
      {isFailed && (
        <View style={styles.failedContainer}>
          <Text style={styles.failedIcon}>⚠️</Text>
          <Text style={styles.failedTitle}>{t("tryon.statusFailed")}</Text>
          {job.failure_reason && (
            <Text style={styles.failedReason}>Reason: {job.failure_reason}</Text>
          )}
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
          >
            <Text style={styles.backButtonText}>{t("common.back")}</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Completed State */}
      {isCompleted && (
        <View style={styles.completedSection}>
          {/* Before / After toggle & Image View */}
          <View style={styles.toggleRow}>
            <TouchableOpacity
              style={[styles.toggleButton, !showingBefore ? styles.activeToggle : null]}
              onPress={() => setShowingBefore(false)}
            >
              <Text
                style={[
                  styles.toggleButtonText,
                  !showingBefore ? styles.activeToggleText : null,
                ]}
              >
                {t("tryon.after")}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.toggleButton, showingBefore ? styles.activeToggle : null]}
              onPress={() => setShowingBefore(true)}
            >
              <Text
                style={[
                  styles.toggleButtonText,
                  showingBefore ? styles.activeToggleText : null,
                ]}
              >
                {t("tryon.before")}
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.imageWrapper}>
            {showingBefore ? (
              <View style={styles.beforePlaceholder}>
                <Text style={styles.beforeIcon}>👤</Text>
                <Text style={styles.beforeLabel}>Original Profile Reference</Text>
              </View>
            ) : job.result_url ? (
              <Image
                source={{
                  uri: job.result_url,
                  cacheKey: job.result_url.split("?")[0],
                }}
                style={styles.resultImage}
                contentFit="cover"
                transition={200}
              />
            ) : (
              <View style={styles.beforePlaceholder}>
                <Text style={styles.beforeIcon}>🖼️</Text>
                <Text style={styles.beforeLabel}>Result ready</Text>
              </View>
            )}
          </View>

          {/* Save Look Button */}
          <View style={styles.saveSection}>
            <TouchableOpacity
              style={[styles.saveLookButton, savedSuccess ? styles.savedButton : null]}
              onPress={handleSaveLook}
              disabled={isSavingWardrobe || savedSuccess}
            >
              <Text style={styles.saveLookButtonText}>
                {savedSuccess ? `✓ ${t("tryon.savedLook")}` : `👗 ${t("tryon.saveLook")}`}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Visual Realism Rating 1-5 */}
          <View style={styles.feedbackCard}>
            <Text style={styles.feedbackTitle}>{t("tryon.ratingTitle")}</Text>
            <View style={styles.ratingRow}>
              {[1, 2, 3, 4, 5].map((star) => (
                <TouchableOpacity
                  key={star}
                  style={[
                    styles.starButton,
                    selectedRating !== null && selectedRating >= star
                      ? styles.starSelected
                      : null,
                  ]}
                  onPress={() => handleRating(star)}
                  disabled={isSubmittingFeedback || feedbackSent}
                >
                  <Text style={styles.starText}>★</Text>
                </TouchableOpacity>
              ))}
            </View>

            {feedbackSent && (
              <Text style={styles.thanksText}>✓ {t("tryon.feedbackThanks")}</Text>
            )}

            {/* "Looks wrong" feedback chips */}
            {selectedRating !== null && selectedRating <= 3 && (
              <View style={styles.chipsSection}>
                <Text style={styles.chipsLabel}>What looks off?</Text>
                <View style={styles.chipsContainer}>
                  {LOOKS_WRONG_CHIPS.map((chip) => (
                    <Chip
                      key={chip}
                      label={chip}
                      selected={selectedChips.includes(chip)}
                      onPress={() => toggleChip(chip)}
                    />
                  ))}
                </View>
              </View>
            )}
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: "#F9FAFB",
    paddingBottom: 40,
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 15,
    color: "#6B7280",
  },
  warningBanner: {
    backgroundColor: "#FFFBEB",
    borderColor: "#FDE68A",
    borderWidth: 1,
    padding: 12,
    margin: 16,
    borderRadius: 8,
  },
  warningBannerText: {
    fontSize: 13,
    color: "#92400E",
    fontWeight: "500",
  },
  progressContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingTop: 100,
    paddingHorizontal: 24,
  },
  animationBox: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: "#EEF2FF",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 24,
    position: "relative",
  },
  progressIcon: {
    position: "absolute",
    fontSize: 24,
  },
  progressTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
    textAlign: "center",
  },
  progressSubtitle: {
    fontSize: 13,
    color: "#6B7280",
    textTransform: "capitalize",
  },
  failedContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingTop: 100,
    paddingHorizontal: 24,
  },
  failedIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  failedTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#EF4444",
    marginBottom: 8,
  },
  failedReason: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 20,
  },
  backButton: {
    backgroundColor: "#111827",
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  backButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
  completedSection: {
    padding: 16,
  },
  toggleRow: {
    flexDirection: "row",
    backgroundColor: "#E5E7EB",
    borderRadius: 10,
    padding: 3,
    marginBottom: 16,
  },
  toggleButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: "center",
    borderRadius: 8,
  },
  activeToggle: {
    backgroundColor: "#FFFFFF",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  toggleButtonText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#6B7280",
  },
  activeToggleText: {
    color: "#111827",
  },
  imageWrapper: {
    width: "100%",
    height: SCREEN_WIDTH * 1.3,
    borderRadius: 16,
    overflow: "hidden",
    backgroundColor: "#E5E7EB",
    marginBottom: 16,
  },
  resultImage: {
    width: "100%",
    height: "100%",
  },
  beforePlaceholder: {
    width: "100%",
    height: "100%",
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#F3F4F6",
  },
  beforeIcon: {
    fontSize: 64,
    marginBottom: 8,
  },
  beforeLabel: {
    fontSize: 14,
    color: "#6B7280",
    fontWeight: "500",
  },
  saveSection: {
    marginBottom: 20,
  },
  saveLookButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
  },
  savedButton: {
    backgroundColor: "#10B981",
  },
  saveLookButtonText: {
    color: "#FFFFFF",
    fontSize: 15,
    fontWeight: "700",
  },
  feedbackCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    padding: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  feedbackTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 14,
    textAlign: "center",
  },
  ratingRow: {
    flexDirection: "row",
    justifyContent: "center",
    gap: 12,
    marginBottom: 12,
  },
  starButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#F3F4F6",
    justifyContent: "center",
    alignItems: "center",
  },
  starSelected: {
    backgroundColor: "#FEF3C7",
  },
  starText: {
    fontSize: 24,
    color: "#F59E0B",
  },
  thanksText: {
    fontSize: 13,
    color: "#10B981",
    fontWeight: "600",
    textAlign: "center",
    marginTop: 4,
  },
  chipsSection: {
    marginTop: 16,
    borderTopWidth: 1,
    borderTopColor: "#F3F4F6",
    paddingTop: 14,
  },
  chipsLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: "#4B5563",
    marginBottom: 10,
  },
  chipsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 12,
  },
  retryButton: {
    backgroundColor: "#4F46E5",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
});
