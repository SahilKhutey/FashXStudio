import React, { useState, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ActivityIndicator,
  Linking,
  ScrollView,
  Platform,
} from "react-native";
import { CameraView, CameraType, useCameraPermissions } from "expo-camera";
import * as ImagePicker from "expo-image-picker";
import { manipulateAsync, SaveFormat } from "expo-image-manipulator";
import { useRouter } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useMe } from "../../src/api/hooks";
import { uploadPhoto, UploadPhotoResult } from "../../src/lib/upload";
import { rejectKey } from "../../src/lib/qualityReasons";
import { cleanupFiles } from "../../src/lib/fileCleanup";

type CaptureState = "tips" | "camera" | "uploading" | "result";

export default function CaptureScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const qc = useQueryClient();
  const { data: me } = useMe(true);

  const [state, setState] = useState<CaptureState>("tips");
  const [facing, setFacing] = useState<CameraType>("back");
  const [permission, requestPermission] = useCameraPermissions();
  const [progress, setProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<UploadPhotoResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const cameraRef = useRef<any>(null);

  const processAndUpload = async (rawUri: string) => {
    if (!me?.user_id) {
      setUploadError(t("common.error"));
      setState("result");
      return;
    }

    setState("uploading");
    setProgress(0);
    setUploadError(null);
    setUploadResult(null);

    let preparedUri: string | null = null;
    try {
      const manip = await manipulateAsync(
        rawUri,
        [{ resize: { width: 2048 } }],
        { compress: 0.9, format: SaveFormat.JPEG }
      );
      preparedUri = manip.uri;

      const res = await uploadPhoto(me.user_id, preparedUri, (p) => {
        setProgress(p);
      });

      setUploadResult(res);
      if (res.status === "accepted") {
        await qc.invalidateQueries({ queryKey: ["me"] });
      }
      setState("result");
    } catch (err: any) {
      if (
        err?.code === "consent_required" ||
        err?.status === 403 ||
        String(err?.message || "").toLowerCase().includes("consent")
      ) {
        router.replace("/onboarding/consent");
        return;
      }

      const reason = err?.reject_reason || err?.reason || err?.message;
      setUploadError(reason || "generic");
      setState("result");
    } finally {
      // Fail-closed storage hygiene: strict cleanup of raw and intermediate files
      await cleanupFiles([rawUri, preparedUri]);
    }
  };

  const handleTakePhoto = async () => {
    if (!cameraRef.current) return;
    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.9,
      });
      if (photo?.uri) {
        await processAndUpload(photo.uri);
      }
    } catch {
      // Do not log image URIs or error traces with paths to console
      setUploadError(t("common.error"));
      setState("result");
    }
  };

  const handlePickLibrary = async () => {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        allowsEditing: false,
        quality: 1,
      });
      if (!result.canceled && result.assets && result.assets.length > 0) {
        const uri = result.assets[0]?.uri;
        if (uri) {
          await processAndUpload(uri);
        }
      }
    } catch {
      setUploadError(t("common.error"));
      setState("result");
    }
  };

  const toggleFacing = () => {
    setFacing((current) => (current === "back" ? "front" : "back"));
  };

  // 1. Tips Screen
  if (state === "tips") {
    return (
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title} accessibilityRole="header">
          {t("capture.tipsTitle")}
        </Text>

        <View style={styles.tipCard}>
          <Text style={styles.tipNumber}>1</Text>
          <Text style={styles.tipText}>{t("capture.tip1")}</Text>
        </View>

        <View style={styles.tipCard}>
          <Text style={styles.tipNumber}>2</Text>
          <Text style={styles.tipText}>{t("capture.tip2")}</Text>
        </View>

        <View style={styles.tipCard}>
          <Text style={styles.tipNumber}>3</Text>
          <Text style={styles.tipText}>{t("capture.tip3")}</Text>
        </View>

        <View style={styles.buttonGroup}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("capture.startCamera")}
            onPress={() => setState("camera")}
            style={styles.primaryButton}
          >
            <Text style={styles.primaryButtonText}>{t("capture.startCamera")}</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("capture.uploadFromLibrary")}
            onPress={handlePickLibrary}
            style={styles.secondaryButton}
          >
            <Text style={styles.secondaryButtonText}>{t("capture.uploadFromLibrary")}</Text>
          </Pressable>
        </View>
      </ScrollView>
    );
  }

  // 2. Camera Screen
  if (state === "camera") {
    if (!permission?.granted) {
      return (
        <View style={styles.centerContainer}>
          <Text style={styles.permissionTitle} accessibilityRole="header">
            {t("capture.permissionRequired")}
          </Text>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("capture.grantPermission")}
            onPress={() => requestPermission()}
            style={styles.primaryButton}
          >
            <Text style={styles.primaryButtonText}>{t("capture.grantPermission")}</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("capture.openSettings")}
            onPress={() => Linking.openSettings()}
            style={[styles.secondaryButton, { marginTop: 12 }]}
          >
            <Text style={styles.secondaryButtonText}>{t("capture.openSettings")}</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("capture.uploadFromLibrary")}
            onPress={handlePickLibrary}
            style={[styles.linkButton, { marginTop: 16 }]}
          >
            <Text style={styles.linkText}>{t("capture.uploadFromLibrary")}</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("common.back")}
            onPress={() => setState("tips")}
            style={[styles.linkButton, { marginTop: 8 }]}
          >
            <Text style={styles.linkText}>{t("common.back")}</Text>
          </Pressable>
        </View>
      );
    }

    return (
      <View style={styles.cameraWrapper}>
        <CameraView ref={cameraRef} style={StyleSheet.absoluteFill} facing={facing} />

        {/* Body outline overlay guide */}
        <View style={styles.overlayGuide} pointerEvents="none">
          <View style={styles.outlineFrame}>
            <View style={styles.headGuide} />
            <View style={styles.torsoGuide} />
          </View>
          <Text style={styles.guideText}>Fit full body inside outline</Text>
        </View>

        {/* Top Controls */}
        <View style={styles.topControls}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("common.back")}
            onPress={() => setState("tips")}
            style={styles.circleButton}
          >
            <Text style={styles.circleButtonText}>✕</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Flip camera"
            onPress={toggleFacing}
            style={styles.circleButton}
          >
            <Text style={styles.circleButtonText}>⟲</Text>
          </Pressable>
        </View>

        {/* Bottom Controls */}
        <View style={styles.bottomControls}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("capture.uploadFromLibrary")}
            onPress={handlePickLibrary}
            style={styles.iconButton}
          >
            <Text style={styles.iconButtonText}>📁</Text>
          </Pressable>

          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("capture.takePhoto")}
            onPress={handleTakePhoto}
            style={styles.captureButton}
          >
            <View style={styles.captureInner} />
          </Pressable>

          <View style={{ width: 44 }} />
        </View>
      </View>
    );
  }

  // 3. Uploading Screen
  if (state === "uploading") {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={styles.uploadingText} accessibilityLiveRegion="polite">
          {t("capture.uploading")}
        </Text>
        <View style={styles.progressContainer}>
          <View style={[styles.progressBarFill, { width: `${Math.round(progress * 100)}%` }]} />
        </View>
        <Text style={styles.progressPercent}>{Math.round(progress * 100)}%</Text>
      </View>
    );
  }

  // 4. Result Screen
  const isAccepted = uploadResult?.status === "accepted";
  const rawRejectReason = uploadResult?.reject_reason || uploadError;
  const rejectKeyTranslation = rejectKey(rawRejectReason);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {isAccepted ? (
        <View style={styles.resultBox}>
          <View style={styles.successBadge}>
            <Text style={styles.successBadgeText}>✓</Text>
          </View>
          <Text style={styles.resultTitle} accessibilityRole="header">
            {t("capture.colorProfileReady")}
          </Text>

          {uploadResult?.skin_tone && (
            <View style={styles.skinToneCard}>
              {uploadResult.skin_tone.hex_code && (
                <View
                  style={[
                    styles.colorSwatch,
                    { backgroundColor: uploadResult.skin_tone.hex_code },
                  ]}
                />
              )}
              <View style={styles.skinToneInfo}>
                {uploadResult.skin_tone.monk_scale_index != null && (
                  <Text style={styles.skinToneLabel}>
                    Monk Scale Index: {uploadResult.skin_tone.monk_scale_index}
                  </Text>
                )}
                {uploadResult.skin_tone.undertone && (
                  <Text style={styles.skinToneSub}>
                    Undertone: {uploadResult.skin_tone.undertone}
                  </Text>
                )}
              </View>
            </View>
          )}

          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Continue to Studio"
            onPress={() => router.replace("/")}
            style={[styles.primaryButton, { marginTop: 32 }]}
          >
            <Text style={styles.primaryButtonText}>Continue to Studio</Text>
          </Pressable>
        </View>
      ) : (
        <View style={styles.resultBox}>
          <View style={styles.rejectBadge}>
            <Text style={styles.rejectBadgeText}>✕</Text>
          </View>
          <Text style={styles.resultTitle} accessibilityRole="header">
            Photo Needs Adjustment
          </Text>
          <Text style={styles.rejectMessage}>
            {t(rejectKeyTranslation)}
          </Text>

          <View style={styles.buttonGroup}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t("capture.retake")}
              onPress={() => setState("camera")}
              style={styles.primaryButton}
            >
              <Text style={styles.primaryButtonText}>{t("capture.retake")}</Text>
            </Pressable>

            <Pressable
              accessibilityRole="button"
              accessibilityLabel={t("capture.uploadFromLibrary")}
              onPress={handlePickLibrary}
              style={styles.secondaryButton}
            >
              <Text style={styles.secondaryButtonText}>{t("capture.uploadFromLibrary")}</Text>
            </Pressable>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    padding: 24,
    backgroundColor: "#F9FAFB",
    justifyContent: "center",
  },
  centerContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    backgroundColor: "#F9FAFB",
  },
  cameraWrapper: {
    flex: 1,
    backgroundColor: "#000000",
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 20,
    textAlign: "center",
  },
  tipCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  tipNumber: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: "#EEF2FF",
    color: "#4F46E5",
    fontWeight: "700",
    textAlign: "center",
    lineHeight: 28,
    marginRight: 14,
    fontSize: 14,
  },
  tipText: {
    flex: 1,
    fontSize: 15,
    color: "#374151",
    lineHeight: 20,
  },
  buttonGroup: {
    marginTop: 24,
    gap: 12,
  },
  primaryButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: "center",
  },
  primaryButtonText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
  secondaryButton: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#D1D5DB",
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: "center",
  },
  secondaryButtonText: {
    color: "#374151",
    fontSize: 16,
    fontWeight: "600",
  },
  linkButton: {
    paddingVertical: 8,
    alignItems: "center",
  },
  linkText: {
    color: "#4F46E5",
    fontSize: 15,
    fontWeight: "500",
  },
  permissionTitle: {
    fontSize: 16,
    color: "#374151",
    textAlign: "center",
    marginBottom: 24,
    lineHeight: 24,
  },
  overlayGuide: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    alignItems: "center",
    justifyContent: "center",
  },
  outlineFrame: {
    width: "72%",
    height: "75%",
    borderWidth: 2,
    borderColor: "rgba(255, 255, 255, 0.75)",
    borderStyle: "dashed",
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "flex-start",
    paddingTop: 24,
  },
  headGuide: {
    width: 70,
    height: 85,
    borderRadius: 40,
    borderWidth: 1.5,
    borderColor: "rgba(255, 255, 255, 0.5)",
    marginBottom: 16,
  },
  torsoGuide: {
    width: "70%",
    flex: 1,
    borderWidth: 1.5,
    borderColor: "rgba(255, 255, 255, 0.4)",
    borderRadius: 16,
    marginBottom: 20,
  },
  guideText: {
    marginTop: 12,
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "600",
    textShadowColor: "rgba(0, 0, 0, 0.75)",
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  topControls: {
    position: "absolute",
    top: Platform.OS === "ios" ? 54 : 36,
    left: 20,
    right: 20,
    flexDirection: "row",
    justifyContent: "space-between",
    zIndex: 10,
  },
  circleButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    alignItems: "center",
    justifyContent: "center",
  },
  circleButtonText: {
    color: "#FFFFFF",
    fontSize: 20,
    fontWeight: "600",
  },
  bottomControls: {
    position: "absolute",
    bottom: 40,
    left: 0,
    right: 0,
    flexDirection: "row",
    justifyContent: "space-around",
    alignItems: "center",
    zIndex: 10,
  },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    alignItems: "center",
    justifyContent: "center",
  },
  iconButtonText: {
    fontSize: 20,
  },
  captureButton: {
    width: 74,
    height: 74,
    borderRadius: 37,
    borderWidth: 4,
    borderColor: "#FFFFFF",
    alignItems: "center",
    justifyContent: "center",
  },
  captureInner: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: "#FFFFFF",
  },
  uploadingText: {
    fontSize: 16,
    color: "#111827",
    fontWeight: "600",
    marginTop: 20,
    textAlign: "center",
  },
  progressContainer: {
    width: "80%",
    height: 8,
    backgroundColor: "#E5E7EB",
    borderRadius: 4,
    marginTop: 16,
    overflow: "hidden",
  },
  progressBarFill: {
    height: "100%",
    backgroundColor: "#4F46E5",
    borderRadius: 4,
  },
  progressPercent: {
    marginTop: 8,
    fontSize: 14,
    color: "#6B7280",
    fontWeight: "500",
  },
  resultBox: {
    alignItems: "center",
    padding: 16,
  },
  successBadge: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#DEF7EC",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  successBadgeText: {
    color: "#03543F",
    fontSize: 32,
    fontWeight: "700",
  },
  rejectBadge: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#FDE8E8",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  rejectBadgeText: {
    color: "#9B1C1C",
    fontSize: 32,
    fontWeight: "700",
  },
  resultTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 12,
    textAlign: "center",
  },
  rejectMessage: {
    fontSize: 15,
    color: "#4B5563",
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 24,
    paddingHorizontal: 12,
  },
  skinToneCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    marginTop: 12,
    width: "100%",
  },
  colorSwatch: {
    width: 48,
    height: 48,
    borderRadius: 24,
    borderWidth: 2,
    borderColor: "#E5E7EB",
    marginRight: 16,
  },
  skinToneInfo: {
    flex: 1,
  },
  skinToneLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: "#111827",
  },
  skinToneSub: {
    fontSize: 13,
    color: "#6B7280",
    marginTop: 2,
  },
});
