import React from "react";
import { StyleSheet, Text, View } from "react-native";

import type { FitEvidenceSummary } from "../types/fit";

export interface FitEvidenceListProps {
  evidence: FitEvidenceSummary;
}

export function FitEvidenceList({ evidence }: FitEvidenceListProps) {
  const items = evidence.evidence_items ?? [];
  return (
    <View style={styles.container} testID="fit-evidence-list">
      <Text style={styles.title}>Evidence used</Text>
      {items.map((item, idx) => (
        <View key={`${item.label}-${idx}`} style={styles.row}>
          <Text style={styles.label}>{item.label}</Text>
          <Text style={styles.status}>{item.status}</Text>
        </View>
      ))}
      <Text style={styles.meta}>
        Chart revision: {evidence.size_chart_revision ?? "Unavailable"} · Basis:{" "}
        {evidence.measurement_basis} · Policy v{evidence.category_policy_version ?? "—"}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: 10,
    backgroundColor: "#F9FAFB",
    borderRadius: 8,
    padding: 10,
  },
  title: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 6,
  },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 3,
  },
  label: {
    fontSize: 12,
    color: "#374151",
  },
  status: {
    fontSize: 12,
    fontWeight: "500",
    color: "#1F2937",
  },
  meta: {
    marginTop: 6,
    fontSize: 11,
    color: "#6B7280",
  },
});
