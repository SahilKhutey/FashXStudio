import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { PersonalState } from "../types";

interface PersonalSectionProps {
  title: string;
  actionText?: string;
  onActionPress?: () => void;
  state?: PersonalState;
  errorMessage?: string;
  onRetry?: () => void;
  children: React.ReactNode;
  testID?: string;
}

export const PersonalSection: React.FC<PersonalSectionProps> = ({
  title,
  actionText,
  onActionPress,
  state = "loaded",
  errorMessage,
  onRetry,
  children,
  testID = "personal-section",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>{title}</Text>
        {actionText && (
          <TouchableOpacity
            onPress={onActionPress}
            accessibilityRole="button"
            accessibilityLabel={actionText}
          >
            <Text style={styles.actionText}>{actionText}</Text>
          </TouchableOpacity>
        )}
      </View>

      {state === "error" ? (
        <View testID="section-error-state" style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Section Unavailable</Text>
          <Text style={styles.errorSubtitle}>
            {errorMessage || "Unable to load recommendations. Other sections remain active."}
          </Text>
          {onRetry && (
            <TouchableOpacity style={styles.retryButton} onPress={onRetry}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          )}
        </View>
      ) : state === "loading" ? (
        <View testID="section-skeleton-state" style={styles.skeletonContainer}>
          <View style={[styles.skeletonBlock, { width: "100%", height: 120 }]} />
        </View>
      ) : (
        children
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#FFFFFF",
  },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  title: {
    fontSize: 17,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.4,
  },
  actionText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#007AFF",
  },
  errorContainer: {
    padding: 16,
    backgroundColor: "#FFF5F5",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#FFD6D6",
    alignItems: "center",
  },
  errorTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#D70015",
    marginBottom: 4,
  },
  errorSubtitle: {
    fontSize: 12,
    color: "#636366",
    textAlign: "center",
    marginBottom: 8,
  },
  retryButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: "#D70015",
    borderRadius: 4,
  },
  retryText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "600",
  },
  skeletonContainer: {
    paddingVertical: 8,
  },
  skeletonBlock: {
    backgroundColor: "#E5E5EA",
    borderRadius: 8,
  },
});
