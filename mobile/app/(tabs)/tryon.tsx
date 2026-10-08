import React, { useState } from "react";
import { StyleSheet, Text, View, TouchableOpacity, ActivityIndicator } from "react-native";
import { useTryOnJob } from "@/features/tryon/hooks/useTryOnJob";

export default function TryOnScreen() {
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const { data: jobStatus, isLoading } = useTryOnJob(activeJobId);

  return (
    <View style={styles.container}>
      <View style={styles.canvas}>
        {activeJobId && jobStatus?.status === "processing" ? (
          <View style={styles.statusContainer}>
            <ActivityIndicator size="large" color="#38BDF8" />
            <Text style={styles.statusText}>Rendering Look with AI...</Text>
            <Text style={styles.statusSub}>Generating drape and light consistency</Text>
          </View>
        ) : (
          <View style={styles.placeholder}>
            <Text style={styles.placeholderTitle}>Fitting Canvas Ready</Text>
            <Text style={styles.placeholderSub}>Select a garment from the rail below</Text>
          </View>
        )}
      </View>

      <View style={styles.garmentRail}>
        <Text style={styles.railHeader}>SELECT GARMENT TO TRY</Text>
        <TouchableOpacity
          style={styles.railItem}
          onPress={() => setActiveJobId("mock_job_demo_101")}
        >
          <Text style={styles.railItemTitle}>Olive Overshirt (Size M)</Text>
          <Text style={styles.railItemSub}>Tap to Fit on Reference Photo</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
    padding: 16,
  },
  canvas: {
    flex: 3,
    backgroundColor: "#1E293B",
    borderRadius: 20,
    borderWidth: 1,
    borderColor: "#334155",
    justifyContent: "center",
    alignItems: "center",
    overflow: "hidden",
  },
  placeholder: {
    alignItems: "center",
  },
  placeholderTitle: {
    color: "#F8FAFC",
    fontSize: 18,
    fontWeight: "700",
  },
  placeholderSub: {
    color: "#94A3B8",
    fontSize: 14,
    marginTop: 6,
  },
  statusContainer: {
    alignItems: "center",
  },
  statusText: {
    color: "#F8FAFC",
    fontSize: 16,
    fontWeight: "600",
    marginTop: 16,
  },
  statusSub: {
    color: "#94A3B8",
    fontSize: 13,
    marginTop: 4,
  },
  garmentRail: {
    flex: 1,
    marginTop: 20,
  },
  railHeader: {
    color: "#94A3B8",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
    marginBottom: 10,
  },
  railItem: {
    backgroundColor: "#1E293B",
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  railItemTitle: {
    color: "#38BDF8",
    fontSize: 15,
    fontWeight: "700",
  },
  railItemSub: {
    color: "#94A3B8",
    fontSize: 13,
    marginTop: 2,
  },
});
