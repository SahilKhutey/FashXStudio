import React, { useState, useEffect } from "react";
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
import { useLocalSearchParams, useRouter, useFocusEffect } from "expo-router";
import { useTranslation } from "react-i18next";
import {
  useJob,
  useTryOnFeedback,
  useRetryTryOn,
} from "../../src/features/tryon/useTryOn";
import { useSaveToWardrobe } from "../../src/features/wardrobe/hooks";
import { Chip } from "../../src/components/Chip";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

const ISSUE_CHIP_OPTIONS: { id: string; label: string }[] = [
  { id: "unnatural_fit", label: "Fit looks unnatural" },
  { id: "garment_distorted", label: "Garment distorted" },
  { id: "color_inaccurate", label: "Color inaccurate" },
  { id: "blurry_artifacts", label: "Blurry or artifacts" },
  { id: "person_appearance_changed", label: "Person altered" },
  { id: "wrong_garment", label: "Wrong garment" },
  { id: "occlusion_error", label: "Occlusion error" },
];

export default function TryOnJobScreen() {
  const { jobId } = useLocalSearchParams<{ jobId: string }>();
  const { t } = useTranslation();
  const router = useRouter();
  const [isFocused, setIsFocused] = useState(true);

  useFocusEffect(
    React.useCallback(() => {
      setIsFocused(true);
      return () => {
        setIsFocused(false);
      };
    }, [])
  );

  const {
    data: job,
    isLoading,
    isError,
    refetch,
    isTakingLongerThanUsual,
  } = useJob(jobId || null, isFocused);

  const { mutate: submitFeedback, isPending: isSubmittingFeedback } = useTryOnFeedback();
  const { mutate: saveToWardrobe, isPending: isSavingWardrobe } = useSaveToWardrobe();
  const { mutateAsync: retryTryOn, isPending: isRetrying } = useRetryTryOn();

  const [showingBefore, setShowingBefore] = useState(false);
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [selectedIssueTags, setSelectedIssueTags] = useState<string[]>([]);
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [imageLoadFailed, setImageLoadFailed] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);

  useEffect(() => {
    setImageLoadFailed(false);
  }, [job?.result_url]);

  const handleSelectRating = (rating: number) => {
    if (feedbackSent) return;
    setSelectedRating(rating);
    setFeedbackError(null);
  };

  const toggleIssueTag = (tagId: string) => {
    if (feedbackSent) return;
    if (selectedIssueTags.includes(tagId)) {
      setSelectedIssueTags(selectedIssueTags.filter((t) => t !== tagId));
    } else {
      setSelectedIssueTags([...selectedIssueTags, tagId]);
    }
  };

  const handleSubmitFeedback = () => {
    if (!jobId || selectedRating === null || feedbackSent || isSubmittingFeedback) return;
    setFeedbackError(null);
    submitFeedback(
      {
        jobId,
        rating: selectedRating,
        issueTags: selectedIssueTags,
      },
      {
        onSuccess: () => setFeedbackSent(true),
        onError: (err: unknown) => {
          const msg =
            err instanceof Error ? err.message : "Unable to submit feedback.";
          setFeedbackError(msg);
        },
      }
    );
  };

  const handleSaveLook = () => {
    if (!job || job.status !== "completed" || !job.garment_id) return;

    saveToWardrobe(
      {
        garmentId: job.garment_id,
        tryonArtifactId: job.artifact_id ?? null,
      },
      {
        onSuccess: () => setSavedSuccess(true),
      }
    );
  };

  const handleRetry = async () => {
    if (!job?.garment_id || isRetrying) return;
    setRetryError(null);
    try {
      const result = await retryTryOn({
        garmentId: job.garment_id,
      });
      if (result.job_id) {
        router.replace(`/tryon/${result.job_id}`);
      }
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "Unable to retry virtual try-on. Please try again.";
      setRetryError(message);
    }
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

  const provider = job.provider ?? "unknown";
  const isMockProvider = provider === "mock";

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
          {retryError && <Text style={styles.errorText}>{retryError}</Text>}
          {job.garment_id && (
            <TouchableOpacity
              style={styles.retryActionButton}
              onPress={handleRetry}
              disabled={isRetrying}
            >
              {isRetrying ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.retryButtonText}>Try again</Text>
              )}
            </TouchableOpacity>
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
          {/* Label mock results */}
          {isMockProvider && (
            <View style={styles.mockBanner}>
              <Text style={styles.mockBannerText}>
                ⚠️ Preview only: not a real try-on
              </Text>
            </View>
          )}

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
              job.reference_photo_url ? (
                <View style={styles.resultContainer}>
                  <Image
                    source={{ uri: job.reference_photo_url }}
                    style={styles.resultImage}
                    contentFit="contain"
                    transition={200}
                  />
                </View>
              ) : (
                <View style={styles.beforePlaceholder}>
                  <Text style={styles.beforeIcon}>👤</Text>
                  <Text style={styles.beforeLabel}>Original photo is unavailable</Text>
                </View>
              )
            ) : job.result_url && !imageLoadFailed ? (
              <View style={styles.resultContainer}>
                <Image
                  source={{
                    uri: job.result_url,
                  }}
                  style={styles.resultImage}
                  contentFit="contain"
                  transition={200}
                  cachePolicy="none"
                  onError={() => setImageLoadFailed(true)}
                />
                {isMockProvider && (
                  <View style={styles.watermarkOverlay}>
                    <Text style={styles.watermarkText}>PREVIEW ONLY</Text>
                  </View>
                )}
              </View>
            ) : (
              <View style={styles.beforePlaceholder}>
                <Text style={styles.beforeIcon}>🖼️</Text>
                <Text style={styles.beforeLabel}>
                  {imageLoadFailed
                    ? "Preview link expired or unavailable."
                    : "Result is being prepared."}
                </Text>
                <TouchableOpacity
                  style={styles.refreshButton}
                  onPress={async () => {
                    setImageLoadFailed(false);
                    await refetch();
                  }}
                >
                  <Text style={styles.refreshButtonText}>Refresh preview</Text>
                </TouchableOpacity>
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
                  onPress={() => handleSelectRating(star)}
                  disabled={isSubmittingFeedback || feedbackSent}
                  testID={`star-rating-${star}`}
                >
                  <Text style={styles.starText}>★</Text>
                </TouchableOpacity>
              ))}
            </View>

            {feedbackSent && (
              <Text style={styles.thanksText}>✓ {t("tryon.feedbackThanks")}</Text>
            )}

            {feedbackError && (
              <Text style={styles.feedbackErrorText}>{feedbackError}</Text>
            )}

            {/* "Looks wrong" feedback chips */}
            {!feedbackSent && selectedRating !== null && selectedRating <= 3 && (
              <View style={styles.chipsSection}>
                <Text style={styles.chipsLabel}>What looks off?</Text>
                <View style={styles.chipsContainer}>
                  {ISSUE_CHIP_OPTIONS.map((chip) => (
                    <Chip
                      key={chip.id}
                      label={chip.label}
                      selected={selectedIssueTags.includes(chip.id)}
                      onPress={() => toggleIssueTag(chip.id)}
                    />
                  ))}
                </View>
              </View>
            )}

            {/* Explicit feedback submit button */}
            {!feedbackSent && selectedRating !== null && (
              <TouchableOpacity
                style={[
                  styles.submitFeedbackButton,
                  isSubmittingFeedback ? styles.submitFeedbackDisabled : null,
                ]}
                onPress={handleSubmitFeedback}
                disabled={isSubmittingFeedback}
                testID="submit-feedback-btn"
              >
                {isSubmittingFeedback ? (
                  <ActivityIndicator size="small" color="#FFFFFF" />
                ) : (
                  <Text style={styles.submitFeedbackButtonText}>Submit feedback</Text>
                )}
              </TouchableOpacity>
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
    marginBottom: 16,
  },
  errorText: {
    fontSize: 13,
    color: "#EF4444",
    marginBottom: 12,
    textAlign: "center",
  },
  retryActionButton: {
    backgroundColor: "#4F46E5",
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 12,
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
    padding: 16,
  },
  beforeIcon: {
    fontSize: 64,
    marginBottom: 8,
  },
  beforeLabel: {
    fontSize: 14,
    color: "#6B7280",
    fontWeight: "500",
    marginBottom: 12,
    textAlign: "center",
  },
  refreshButton: {
    backgroundColor: "#4F46E5",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  refreshButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
    fontSize: 14,
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
  submitFeedbackButton: {
    backgroundColor: "#111827",
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 14,
  },
  submitFeedbackDisabled: {
    opacity: 0.6,
  },
  submitFeedbackButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
  },
  feedbackErrorText: {
    color: "#EF4444",
    fontSize: 13,
    textAlign: "center",
    marginTop: 8,
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
  mockBanner: {
    backgroundColor: "#FEF3C7",
    borderColor: "#FCD34D",
    borderWidth: 1,
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  mockBannerText: {
    color: "#92400E",
    fontSize: 13,
    fontWeight: "600",
    textAlign: "center",
  },
  resultContainer: {
    width: "100%",
    height: "100%",
    position: "relative",
  },
  watermarkOverlay: {
    position: "absolute",
    bottom: 20,
    alignSelf: "center",
    backgroundColor: "rgba(0, 0, 0, 0.65)",
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "rgba(255, 255, 255, 0.3)",
  },
  watermarkText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "800",
    letterSpacing: 1.5,
  },
});
