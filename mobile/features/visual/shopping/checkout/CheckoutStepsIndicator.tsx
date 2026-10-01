/**
 * CheckoutStepsIndicator Component — Phase 07 (Section 7.43).
 *
 * Renders progressive step breadcrumbs:
 * Contact -> Address -> Delivery -> Payment -> Review.
 */

import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { CheckoutStep } from "../types";

export interface CheckoutStepsIndicatorProps {
  currentStep: CheckoutStep;
}

const STEPS: Array<{ key: CheckoutStep; label: string }> = [
  { key: "contact", label: "Contact" },
  { key: "address", label: "Address" },
  { key: "delivery", label: "Delivery" },
  { key: "payment", label: "Payment" },
  { key: "review", label: "Review" },
];

export const CheckoutStepsIndicator: React.FC<CheckoutStepsIndicatorProps> = ({ currentStep }) => {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <View style={styles.container}>
      {STEPS.map((step, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = index === currentIndex;

        return (
          <React.Fragment key={step.key}>
            <View style={styles.stepItem}>
              <View
                style={[
                  styles.circle,
                  isCompleted && styles.circleCompleted,
                  isCurrent && styles.circleCurrent,
                ]}
              >
                <Text
                  style={[
                    styles.circleText,
                    isCompleted && styles.circleTextCompleted,
                    isCurrent && styles.circleTextCurrent,
                  ]}
                >
                  {isCompleted ? "✓" : index + 1}
                </Text>
              </View>
              <Text
                style={[
                  styles.stepLabel,
                  isCurrent && styles.stepLabelCurrent,
                  isCompleted && styles.stepLabelCompleted,
                ]}
              >
                {step.label}
              </Text>
            </View>

            {index < STEPS.length - 1 ? (
              <View style={[styles.connector, isCompleted && styles.connectorCompleted]} />
            ) : null}
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
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: 8,
  },
  stepItem: {
    alignItems: "center",
    gap: 4,
  },
  circle: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: defaultDesignTokens.neutral.neutral300,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    justifyContent: "center",
    alignItems: "center",
  },
  circleCurrent: {
    borderColor: defaultDesignTokens.brand.primary,
    backgroundColor: defaultDesignTokens.brand.primary,
  },
  circleCompleted: {
    borderColor: defaultDesignTokens.status.success,
    backgroundColor: defaultDesignTokens.status.success,
  },
  circleText: {
    fontSize: 12,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral500,
  },
  circleTextCurrent: {
    color: defaultDesignTokens.surfaces.surfaceLight,
  },
  circleTextCompleted: {
    color: defaultDesignTokens.surfaces.surfaceLight,
  },
  stepLabel: {
    fontSize: 11,
    color: defaultDesignTokens.neutral.neutral500,
    fontWeight: "500",
  },
  stepLabelCurrent: {
    color: defaultDesignTokens.brand.primary,
    fontWeight: "700",
  },
  stepLabelCompleted: {
    color: defaultDesignTokens.neutral.neutral800,
  },
  connector: {
    flex: 1,
    height: 2,
    backgroundColor: defaultDesignTokens.neutral.neutral200,
    marginHorizontal: 4,
    marginBottom: 16,
  },
  connectorCompleted: {
    backgroundColor: defaultDesignTokens.status.success,
  },
});
