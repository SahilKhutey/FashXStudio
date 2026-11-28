import React, { useRef, useState } from "react";
import { View, Text, Pressable, StyleSheet, Linking } from "react-native";
import {
  CameraView,
  useCameraPermissions,
  toPermissionState,
} from "../../services/camera.service";

type Props = {
  onCapture: (uri: string) => void;
  onCancel?: () => void;
};

/**
 * Controlled camera capture component for VTO photo acquisition.
 * Requests camera permission only when entered, handles denial/blocked states,
 * and returns a local URI for explicit shopper preview/confirmation without auto-uploading.
 */
export function CameraCapture({ onCapture, onCancel }: Props) {
  const cameraRef = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [capturing, setCapturing] = useState(false);
  const [captureError, setCaptureError] = useState<string | null>(null);

  const permState = toPermissionState(permission);

  if (permState === "UNKNOWN") {
    return (
      <View style={styles.center}>
        <Text style={styles.infoText}>Checking camera permission...</Text>
      </View>
    );
  }

  if (permState !== "GRANTED") {
    return (
      <View style={styles.center}>
        <Text style={styles.infoText}>
          {permState === "BLOCKED"
            ? "Camera access was denied. Enable camera permission in system settings to capture a photo."
            : "Camera access is required when capturing a photo for virtual try-on."}
        </Text>
        <Pressable
          onPress={
            permState === "BLOCKED"
              ? () => {
                  void Linking.openSettings();
                }
              : () => {
                  void requestPermission();
                }
          }
          style={styles.button}
        >
          <Text style={styles.buttonText}>
            {permState === "BLOCKED" ? "Open settings" : "Allow camera"}
          </Text>
        </Pressable>
        {onCancel ? (
          <Pressable onPress={onCancel} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>Cancel</Text>
          </Pressable>
        ) : null}
      </View>
    );
  }

  async function handleCapture() {
    if (!cameraRef.current || capturing) {
      return;
    }

    try {
      setCapturing(true);
      setCaptureError(null);
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.9,
        skipProcessing: false,
      });
      if (photo?.uri) {
        onCapture(photo.uri);
      }
    } catch {
      setCaptureError("Unable to capture photo. Please try again.");
    } finally {
      setCapturing(false);
    }
  }

  return (
    <View style={styles.container}>
      <CameraView ref={cameraRef} style={styles.camera} facing="front" />
      {captureError ? (
        <Text style={styles.errorText}>{captureError}</Text>
      ) : null}
      <View style={styles.controls}>
        <Pressable
          disabled={capturing}
          onPress={() => {
            void handleCapture();
          }}
          style={styles.button}
        >
          <Text style={styles.buttonText}>
            {capturing ? "Capturing..." : "Capture photo"}
          </Text>
        </Pressable>
        {onCancel ? (
          <Pressable onPress={onCancel} style={styles.secondaryButton}>
            <Text style={styles.secondaryButtonText}>Cancel</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#000",
  },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
    gap: 12,
  },
  infoText: {
    textAlign: "center",
    fontSize: 15,
    color: "#111827",
  },
  errorText: {
    color: "#FCA5A5",
    textAlign: "center",
    paddingHorizontal: 16,
    paddingTop: 8,
  },
  camera: {
    flex: 1,
  },
  controls: {
    padding: 20,
    gap: 10,
  },
  button: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: "#222",
    alignItems: "center",
  },
  buttonText: {
    color: "#fff",
    fontWeight: "600",
  },
  secondaryButton: {
    padding: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  secondaryButtonText: {
    color: "#9CA3AF",
    fontWeight: "500",
  },
});
