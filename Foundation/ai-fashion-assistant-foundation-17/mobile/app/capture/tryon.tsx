import { CameraView } from "expo-camera";
import { useRef } from "react";
import { ActivityIndicator, Pressable, SafeAreaView, StyleSheet, Text, View } from "react-native";
import { CaptureGuide } from "../../components/capture/CaptureGuide";
import { useTryOnCapture } from "../../features/capture/useTryOnCapture";

export default function TryOnCaptureScreen() {
  const cameraRef = useRef<CameraView>(null);
  const capture = useTryOnCapture();

  if (!capture.permission?.granted) {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.title}>Camera access</Text>
        <Text style={styles.message}>We need camera access to create your try-on reference photo.</Text>
        <Pressable style={styles.primary} onPress={capture.requestCameraPermission}>
          <Text style={styles.primaryText}>Allow Camera</Text>
        </Pressable>
        {capture.error ? <Text style={styles.error}>{capture.error}</Text> : null}
      </SafeAreaView>
    );
  }

  if (capture.state === "uploading" || capture.state === "processing") {
    return (
      <SafeAreaView style={styles.centered}>
        <ActivityIndicator size="large" />
        <Text style={styles.title}>{capture.guidance?.title ?? "Checking your photo"}</Text>
        <Text style={styles.message}>{capture.guidance?.message ?? "Please keep this screen open while we validate the photo."}</Text>
        {capture.guidance?.tips.map((tip) => <Text style={styles.tip} key={tip}>• {tip}</Text>)}
      </SafeAreaView>
    );
  }

  if (capture.state === "ready") {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.success}>✓</Text>
        <Text style={styles.title}>Your photo is ready</Text>
        <Text style={styles.message}>This photo can now be used for virtual try-on.</Text>
        <Pressable style={styles.primary} onPress={capture.retry}>
          <Text style={styles.primaryText}>Retake Photo</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  if (capture.state === "error") {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.title}>We couldn't process that photo</Text>
        <Text style={styles.message}>{capture.error ?? "Please try again."}</Text>
        <Pressable style={styles.primary} onPress={capture.retry}>
          <Text style={styles.primaryText}>Try Again</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  if (capture.state === "retry") {
    return (
      <SafeAreaView style={styles.centered}>
        <Text style={styles.title}>{capture.guidance?.title ?? "Retake your photo"}</Text>
        <Text style={styles.message}>{capture.guidance?.message}</Text>
        {capture.guidance?.tips.map((tip) => <Text style={styles.tip} key={tip}>• {tip}</Text>)}
        <Pressable style={styles.primary} onPress={capture.retry}>
          <Text style={styles.primaryText}>Try Again</Text>
        </Pressable>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.cameraWrap}>
        <CameraView ref={cameraRef} style={styles.camera} facing="front" mode="picture" />
        <View pointerEvents="none" style={styles.overlay}>
          <View style={styles.frame} />
        </View>
      </View>
      <View style={styles.bottom}>
        <CaptureGuide />
        <Pressable
          style={styles.primary}
          onPress={async () => {
            const photo = await cameraRef.current?.takePictureAsync({ quality: 0.9 });
            if (!photo) return;
            await capture.captureAndUpload(photo);
          }}
        >
          <Text style={styles.primaryText}>Capture Try-On Photo</Text>
        </Pressable>
        {capture.error ? <Text style={styles.error}>{capture.error}</Text> : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  cameraWrap: { flex: 1, position: "relative" },
  camera: { flex: 1 },
  overlay: { ...StyleSheet.absoluteFillObject, alignItems: "center", justifyContent: "center" },
  frame: { width: "68%", height: "76%", borderWidth: 2, borderColor: "#fff", borderRadius: 30 },
  bottom: { backgroundColor: "#0b0f19", padding: 16, gap: 12 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 12, backgroundColor: "#f8fafc" },
  title: { fontSize: 24, fontWeight: "800", color: "#111827", textAlign: "center" },
  message: { fontSize: 15, lineHeight: 22, color: "#4b5563", textAlign: "center", maxWidth: 340 },
  tip: { width: "100%", maxWidth: 340, color: "#374151", lineHeight: 21 },
  primary: { width: "100%", minHeight: 52, borderRadius: 14, backgroundColor: "#111827", alignItems: "center", justifyContent: "center", paddingHorizontal: 18 },
  primaryText: { color: "#fff", fontSize: 16, fontWeight: "700" },
  error: { color: "#b91c1c", textAlign: "center" },
  success: { fontSize: 56, color: "#047857" },
});
