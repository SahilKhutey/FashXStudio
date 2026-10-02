import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { RegionBreadcrumbContract } from "../types";

interface RegionBreadcrumbProps {
  breadcrumbs: RegionBreadcrumbContract[];
  onSelectCrumb?: (crumbId: string) => void;
  testID?: string;
}

export const RegionBreadcrumb: React.FC<RegionBreadcrumbProps> = ({
  breadcrumbs,
  onSelectCrumb,
  testID = "region-breadcrumbs",
}) => {
  if (!breadcrumbs || breadcrumbs.length === 0) return null;

  return (
    <View testID={testID} style={styles.container} accessibilityRole="navigation">
      <TouchableOpacity
        onPress={() => onSelectCrumb?.("world")}
        style={styles.crumbTouch}
        accessibilityLabel="Navigate to World map"
      >
        <Text style={styles.crumbText}>World</Text>
      </TouchableOpacity>
      <Text style={styles.separator}> / </Text>

      {breadcrumbs.map((crumb, idx) => {
        const isLast = idx === breadcrumbs.length - 1;
        return (
          <React.Fragment key={crumb.id}>
            <TouchableOpacity
              testID={`crumb-${crumb.id}`}
              disabled={crumb.is_current}
              onPress={() => onSelectCrumb?.(crumb.id)}
              style={styles.crumbTouch}
              accessibilityRole="link"
              accessibilityState={{ selected: crumb.is_current }}
            >
              <Text
                style={[
                  styles.crumbText,
                  (crumb.is_current || isLast) && styles.currentText,
                ]}
                numberOfLines={1}
              >
                {crumb.name}
              </Text>
            </TouchableOpacity>
            {!isLast && <Text style={styles.separator}> / </Text>}
          </React.Fragment>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    flexWrap: "wrap",
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: "#ffffff",
    borderBottomWidth: 1,
    borderBottomColor: "#f3f4f6",
  },
  crumbTouch: {
    paddingVertical: 2,
  },
  crumbText: {
    fontSize: 12,
    color: "#6b7280",
    fontWeight: "500",
  },
  currentText: {
    color: "#111111",
    fontWeight: "700",
  },
  separator: {
    fontSize: 12,
    color: "#9ca3af",
  },
});
