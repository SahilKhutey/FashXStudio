import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";

interface QuantitySelectorProps {
  quantity: number;
  min?: number;
  max?: number;
  onChangeQuantity: (newQuantity: number) => void;
  disabled?: boolean;
  testID?: string;
}

export const QuantitySelector: React.FC<QuantitySelectorProps> = ({
  quantity,
  min = 1,
  max = 10,
  onChangeQuantity,
  disabled = false,
  testID = "quantity-selector",
}) => {
  const canDecrease = !disabled && quantity > min;
  const canIncrease = !disabled && quantity < max;

  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.label}>Quantity</Text>
      <View style={styles.stepperContainer}>
        <TouchableOpacity
          testID={`${testID}-decrement`}
          disabled={!canDecrease}
          onPress={() => canDecrease && onChangeQuantity(quantity - 1)}
          style={[styles.stepButton, !canDecrease && styles.stepButtonDisabled]}
          accessibilityRole="button"
          accessibilityLabel="Decrease quantity"
        >
          <Text style={[styles.stepText, !canDecrease && styles.stepTextDisabled]}>−</Text>
        </TouchableOpacity>

        <View style={styles.valueContainer}>
          <Text testID={`${testID}-value`} style={styles.valueText}>
            {quantity}
          </Text>
        </View>

        <TouchableOpacity
          testID={`${testID}-increment`}
          disabled={!canIncrease}
          onPress={() => canIncrease && onChangeQuantity(quantity + 1)}
          style={[styles.stepButton, !canIncrease && styles.stepButtonDisabled]}
          accessibilityRole="button"
          accessibilityLabel="Increase quantity"
        >
          <Text style={[styles.stepText, !canIncrease && styles.stepTextDisabled]}>+</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    borderTopWidth: 1,
    borderTopColor: "#eeeeee",
  },
  label: {
    fontSize: 14,
    fontWeight: "700",
    color: "#222222",
  },
  stepperContainer: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1.5,
    borderColor: "#dddddd",
    borderRadius: 6,
    overflow: "hidden",
  },
  stepButton: {
    width: 38,
    height: 38,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#ffffff",
  },
  stepButtonDisabled: {
    backgroundColor: "#fafafa",
  },
  stepText: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111111",
  },
  stepTextDisabled: {
    color: "#cccccc",
  },
  valueContainer: {
    minWidth: 40,
    height: 38,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderLeftWidth: 1,
    borderRightWidth: 1,
    borderColor: "#eeeeee",
  },
  valueText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#111111",
  },
});
