import React from "react";
import { StyleSheet, Text, View, ScrollView } from "react-native";

export default function ProfileScreen() {
  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.title}>Fashion Identity</Text>
        <Text style={styles.subTitle}>Calibrated Body & Fit Preferences</Text>
      </View>

      <View style={styles.metricCard}>
        <Text style={styles.metricHeader}>BODY PROPORTIONS</Text>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Height</Text>
          <Text style={styles.metricValue}>178 cm</Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Chest</Text>
          <Text style={styles.metricValue}>101.5 cm</Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Waist</Text>
          <Text style={styles.metricValue}>81 cm</Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Silhouette</Text>
          <Text style={styles.metricValue}>Athletic V-Taper</Text>
        </View>
      </View>

      <View style={styles.metricCard}>
        <Text style={styles.metricHeader}>STYLE & FIT PREFERENCES</Text>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Topwear Fit</Text>
          <Text style={styles.metricValueHighlight}>Relaxed</Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Bottomwear Fit</Text>
          <Text style={styles.metricValueHighlight}>Straight</Text>
        </View>
        <View style={styles.metricRow}>
          <Text style={styles.metricLabel}>Undertone</Text>
          <Text style={styles.metricValue}>Warm Golden</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
  content: {
    padding: 16,
  },
  header: {
    marginBottom: 20,
  },
  title: {
    color: "#F8FAFC",
    fontSize: 22,
    fontWeight: "700",
  },
  subTitle: {
    color: "#94A3B8",
    fontSize: 14,
    marginTop: 4,
  },
  metricCard: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: "#334155",
  },
  metricHeader: {
    color: "#38BDF8",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
    marginBottom: 12,
  },
  metricRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#334155",
  },
  metricLabel: {
    color: "#94A3B8",
    fontSize: 15,
  },
  metricValue: {
    color: "#F8FAFC",
    fontSize: 15,
    fontWeight: "600",
  },
  metricValueHighlight: {
    color: "#38BDF8",
    fontSize: 15,
    fontWeight: "700",
  },
});
