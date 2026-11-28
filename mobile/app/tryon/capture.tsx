import React, { useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, router } from "expo-router";
import { PhotoInstructions } from "../../src/features/tryon/components/PhotoInstructions";
import { GalleryPicker } from "../../src/features/tryon/components/GalleryPicker";
import { PhotoPreview } from "../../src/features/tryon/components/PhotoPreview";
import { CameraCapture } from "../../src/features/tryon/CameraCapture";
import { validateLocalImage } from "../../src/features/tryon/imageValidation";
import { mapTryOnErrorCode } from "../../src/features/tryon/errors";
import { useStartTryOn } from "../../src/features/tryon/useTryOn";

export default function TryOnCaptureRoute() {
  const { garmentId } = useLocalSearchParams<{ garmentId?: string }>();
  const startTryOn = useStartTryOn();

  const [mode, setMode] = useState<"instructions" | "camera" | "preview">(
    "instructions",
  );
  const [selectedUri, setSelectedUri] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handlePhotoSelected(uri: string) {
    setError(null);
    try {
      await validateLocalImage(uri);
      setSelectedUri(uri);
      setMode("preview");
    } catch (err) {
      const code = err instanceof Error ? err.message : undefined;
      setError(mapTryOnErrorCode(code));
      setMode("instructions");
    }
  }

  async function handleConfirm() {
    if (!garmentId || startTryOn.isPending) return;
    setError(null);
    try {
      const job = await startTryOn.mutateAsync({ garmentId });
      router.replace(`/tryon/${job.job_id}`);
    } catch (err) {
      const code =
        typeof err === "object" && err !== null && "code" in err
          ? String((err as { code?: unknown }).code ?? "")
          : undefined;
      setError(mapTryOnErrorCode(code));
    }
  }

  if (mode === "camera") {
    return (
      <CameraCapture
        onCapture={(uri) => {
          void handlePhotoSelected(uri);
        }}
        onCancel={() => setMode("instructions")}
      />
    );
  }

  if (mode === "preview" && selectedUri) {
    return (
      <PhotoPreview
        uri={selectedUri}
        submitting={startTryOn.isPending}
        onRetake={() => {
          setSelectedUri(null);
          setMode("instructions");
        }}
        onConfirm={() => {
          void handleConfirm();
        }}
      />
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <PhotoInstructions />
      {error ? (
        <Text accessibilityRole="alert" style={styles.error}>
          {error}
        </Text>
      ) : null}
      <View style={styles.actions}>
        <Pressable
          onPress={() => setMode("camera")}
          accessibilityRole="button"
          style={styles.primaryButton}
        >
          <Text style={styles.primaryText}>Take a photo</Text>
        </Pressable>
        <GalleryPicker
          onSelected={(uri) => {
            void handlePhotoSelected(uri);
          }}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { paddingBottom: 32 },
  actions: { paddingHorizontal: 20, gap: 12 },
  error: { color: "#B42318", paddingHorizontal: 20, paddingBottom: 8 },
  primaryButton: {
    backgroundColor: "#111827",
    padding: 16,
    borderRadius: 12,
    alignItems: "center",
  },
  primaryText: { color: "#FFFFFF", fontWeight: "600" },
});
