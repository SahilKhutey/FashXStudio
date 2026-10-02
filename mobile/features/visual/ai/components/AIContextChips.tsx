import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from "react-native";
import { AIContextItemContract } from "../types";

interface AIContextChipsProps {
  contextItems: AIContextItemContract[];
  onRemoveItem?: (key: string) => void;
  onEditContext?: () => void;
  testID?: string;
}

export const AIContextChips: React.FC<AIContextChipsProps> = ({
  contextItems,
  onRemoveItem,
  onEditContext,
  testID = "ai-context-chips-component",
}) => {
  if (contextItems.length === 0) return null;

  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.label}>CONTEXT:</Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.scrollRail}
      >
        {contextItems.map((item) => (
          <View key={item.key} style={styles.chip}>
            <Text style={styles.chipText}>
              {item.label}: <Text style={styles.chipValue}>{item.value}</Text>
            </Text>
            {item.is_removable && onRemoveItem && (
              <TouchableOpacity
                testID={`remove-context-${item.key}`}
                onPress={() => onRemoveItem(item.key)}
                style={styles.closeBtn}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Text style={styles.closeText}>×</Text>
              </TouchableOpacity>
            )}
          </View>
        ))}

        {onEditContext && (
          <TouchableOpacity
            testID="edit-context-button"
            onPress={onEditContext}
            style={styles.editBtn}
          >
            <Text style={styles.editText}>Edit Context</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: "#F9F9FB",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  label: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginRight: 8,
  },
  scrollRail: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#E5E5EA",
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  chipText: {
    fontSize: 11,
    color: "#3A3A3C",
  },
  chipValue: {
    fontWeight: "600",
    color: "#1C1C1E",
  },
  closeBtn: {
    marginLeft: 6,
  },
  closeText: {
    fontSize: 13,
    color: "#636366",
    fontWeight: "700",
  },
  editBtn: {
    paddingHorizontal: 6,
    paddingVertical: 4,
  },
  editText: {
    fontSize: 11,
    color: "#007AFF",
    fontWeight: "600",
  },
});
