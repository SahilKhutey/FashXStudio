import React, { useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { SpecificationSectionContract } from "../types";

interface ProductSpecificationsProps {
  description?: string;
  specifications: SpecificationSectionContract[];
  testID?: string;
}

export const ProductSpecifications: React.FC<ProductSpecificationsProps> = ({
  description,
  specifications = [],
  testID = "product-specifications",
}) => {
  const [isDescriptionExpanded, setIsDescriptionExpanded] = useState(false);

  return (
    <View testID={testID} style={styles.container}>
      {/* Description with progressive disclosure (Section 9.18) */}
      {description && (
        <View style={styles.sectionBlock}>
          <Text style={styles.sectionHeading}>Product Overview</Text>
          <Text
            numberOfLines={isDescriptionExpanded ? undefined : 3}
            style={styles.descriptionText}
          >
            {description}
          </Text>
          <TouchableOpacity
            testID={`${testID}-toggle-description`}
            onPress={() => setIsDescriptionExpanded(!isDescriptionExpanded)}
            style={styles.readMoreButton}
            accessibilityRole="button"
          >
            <Text style={styles.readMoreText}>
              {isDescriptionExpanded ? "Show Less ▲" : "Read More ▼"}
            </Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Structured Technical Specifications (Section 9.19 & 9.20) */}
      {specifications.length > 0 && (
        <View style={styles.sectionBlock}>
          <Text style={styles.sectionHeading}>Specifications & Craft</Text>
          {specifications.map((section, sIdx) => (
            <View key={`spec-sec-${sIdx}`} style={styles.specGroup}>
              <Text style={styles.groupHeading}>{section.group_name}</Text>
              <View style={styles.tableWrapper}>
                {section.items.map((item, iIdx) => (
                  <View
                    key={`spec-item-${iIdx}`}
                    style={[
                      styles.tableRow,
                      iIdx % 2 === 1 && styles.tableRowAlternate,
                    ]}
                  >
                    <Text style={styles.tableLabel}>{item.label}</Text>
                    <Text style={styles.tableValue}>{item.value}</Text>
                  </View>
                ))}
              </View>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
    backgroundColor: "#ffffff",
  },
  sectionBlock: {
    marginBottom: 20,
  },
  sectionHeading: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
    marginBottom: 10,
  },
  descriptionText: {
    fontSize: 14,
    color: "#444444",
    lineHeight: 22,
  },
  readMoreButton: {
    marginTop: 6,
    alignSelf: "flex-start",
  },
  readMoreText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1a56db",
  },
  specGroup: {
    marginTop: 10,
  },
  groupHeading: {
    fontSize: 13,
    fontWeight: "700",
    color: "#666666",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  tableWrapper: {
    borderWidth: 1,
    borderColor: "#eeeeee",
    borderRadius: 6,
    overflow: "hidden",
  },
  tableRow: {
    flexDirection: "row",
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: "#ffffff",
  },
  tableRowAlternate: {
    backgroundColor: "#fafafa",
  },
  tableLabel: {
    flex: 1,
    fontSize: 13,
    color: "#666666",
    fontWeight: "500",
  },
  tableValue: {
    flex: 1.5,
    fontSize: 13,
    color: "#111111",
    fontWeight: "600",
  },
});
