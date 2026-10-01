/**
 * CheckoutTemplate Component — Phase 07 (Section 7.41 - 7.44).
 *
 * Progressive checkout layout with:
 * - Step indicator (Contact -> Address -> Delivery -> Payment -> Review)
 * - Address selection / display
 * - Delivery speed method selection
 * - Payment option selection
 * - Order summary & Place Order CTA
 */

import React from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { CheckoutTemplateSpec } from "../types";
import { CheckoutStepsIndicator } from "../checkout/CheckoutStepsIndicator";
import { Button } from "../../components/Button";

export interface CheckoutTemplateProps {
  spec: CheckoutTemplateSpec;
  onSelectAddress: (addressId: string) => void;
  onSelectDeliveryMethod: (methodId: string) => void;
  onSelectPaymentMethod: (paymentId: string) => void;
  onProceedToReview: () => void;
  isProcessing?: boolean;
}

export const CheckoutTemplate: React.FC<CheckoutTemplateProps> = ({
  spec,
  onSelectAddress,
  onSelectDeliveryMethod,
  onSelectPaymentMethod,
  onProceedToReview,
  isProcessing,
}) => {
  const { checkoutState, availableAddresses, availableDeliveryMethods, availablePaymentMethods } = spec;

  const selectedAddress = checkoutState.deliveryAddress || availableAddresses[0];
  const selectedDelivery = checkoutState.deliveryMethod || availableDeliveryMethods[0];
  const selectedPayment = checkoutState.paymentMethod || availablePaymentMethods[0];

  return (
    <ScrollView contentContainerStyle={styles.container} showsVerticalScrollIndicator={false}>
      {/* Progressive Step Breadcrumbs */}
      <CheckoutStepsIndicator currentStep={checkoutState.currentStep} />

      {/* Delivery Address Section */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>📍 Delivery Address</Text>
          <TouchableOpacity accessibilityLabel="Change delivery address">
            <Text style={styles.changeLink}>Change</Text>
          </TouchableOpacity>
        </View>

        {selectedAddress ? (
          <View style={styles.addressBox}>
            <Text style={styles.addressName}>{selectedAddress.fullName}</Text>
            <Text style={styles.addressText}>{selectedAddress.addressLine1}</Text>
            {selectedAddress.addressLine2 ? (
              <Text style={styles.addressText}>{selectedAddress.addressLine2}</Text>
            ) : null}
            <Text style={styles.addressText}>
              {selectedAddress.city}, {selectedAddress.state} - {selectedAddress.postalCode}
            </Text>
            <Text style={styles.addressPhone}>Phone: {selectedAddress.phone}</Text>
          </View>
        ) : null}
      </View>

      {/* Shipping Method Section */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>📦 Shipping Speed</Text>
        <View style={styles.methodsList}>
          {availableDeliveryMethods.map((method) => {
            const isSelected = method.id === selectedDelivery?.id;
            return (
              <TouchableOpacity
                key={method.id}
                accessibilityLabel={`Select ${method.name}`}
                style={[styles.methodItem, isSelected && styles.methodSelected]}
                onPress={() => onSelectDeliveryMethod(method.id)}
              >
                <View style={styles.methodInfo}>
                  <Text style={styles.methodName}>{method.name}</Text>
                  <Text style={styles.methodEst}>{method.estimatedTime}</Text>
                </View>
                <Text style={styles.methodFee}>
                  {method.fee === 0 ? "FREE" : `₹${method.fee}`}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Payment Options Section */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>💳 Payment Method</Text>
        <View style={styles.methodsList}>
          {availablePaymentMethods.map((method) => {
            const isSelected = method.id === selectedPayment?.id;
            return (
              <TouchableOpacity
                key={method.id}
                accessibilityLabel={`Select ${method.title}`}
                style={[styles.methodItem, isSelected && styles.methodSelected]}
                onPress={() => onSelectPaymentMethod(method.id)}
              >
                <Text style={styles.methodName}>{method.title}</Text>
                <View style={[styles.radioCircle, isSelected && styles.radioCircleSelected]} />
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Financial Summary */}
      <View style={styles.summaryCard}>
        <View style={styles.summaryRow}>
          <Text style={styles.summaryLabel}>Total Payable</Text>
          <Text style={styles.summaryValue}>
            {checkoutState.cart.summary.currencySymbol}
            {checkoutState.cart.summary.total.toLocaleString()}
          </Text>
        </View>

        <Button
          label="Review Order & Pay"
          variant="primary"
          size="lg"
          fullWidth
          loading={isProcessing}
          onPress={onProceedToReview}
        />
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 16,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
  },
  card: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: defaultDesignTokens.surfaces.surfaceLight,
    borderWidth: 1,
    borderColor: defaultDesignTokens.neutral.neutral200,
    gap: 12,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
  changeLink: {
    fontSize: 13,
    fontWeight: "600",
    color: defaultDesignTokens.brand.primary,
  },
  addressBox: {
    gap: 2,
  },
  addressName: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.neutral.neutral900,
  },
  addressText: {
    fontSize: 13,
    color: defaultDesignTokens.neutral.neutral700,
  },
  addressPhone: {
    fontSize: 13,
    color: defaultDesignTokens.neutral.neutral500,
    marginTop: 4,
  },
  methodsList: {
    gap: 8,
  },
  methodItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 12,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: defaultDesignTokens.neutral.neutral200,
  },
  methodSelected: {
    borderColor: defaultDesignTokens.brand.primary,
    backgroundColor: defaultDesignTokens.neutral.neutral50,
  },
  methodInfo: {
    gap: 2,
  },
  methodName: {
    fontSize: 14,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral900,
  },
  methodEst: {
    fontSize: 12,
    color: defaultDesignTokens.neutral.neutral500,
  },
  methodFee: {
    fontSize: 14,
    fontWeight: "700",
    color: defaultDesignTokens.status.success,
  },
  radioCircle: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: defaultDesignTokens.neutral.neutral400,
  },
  radioCircleSelected: {
    borderColor: defaultDesignTokens.brand.primary,
    backgroundColor: defaultDesignTokens.brand.primary,
  },
  summaryCard: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    gap: 12,
    marginTop: 8,
  },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  summaryLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: defaultDesignTokens.neutral.neutral700,
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: "800",
    color: defaultDesignTokens.neutral.neutral900,
  },
});
