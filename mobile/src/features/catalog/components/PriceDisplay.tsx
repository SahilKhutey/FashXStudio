import React from "react";
import { Text, View, StyleSheet } from "react-native";

export type PriceDisplayProps = {
  price: {
    amount: string | number;
    currency: string;
    original_amount?: string | number | null;
  } | null;
};

export function formatCurrencyPrice(
  amountInput: string | number,
  currency: string,
): string {
  const amount = typeof amountInput === "number" ? amountInput : Number(amountInput);
  if (!Number.isFinite(amount) || amount < 0) {
    return "Price unavailable";
  }

  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toFixed(2)}`;
  }
}

export function PriceDisplay({ price }: PriceDisplayProps) {
  if (!price) {
    return <Text style={styles.unavailable}>Price unavailable</Text>;
  }

  const currentAmount = Number(price.amount);
  const originalAmount =
    price.original_amount !== undefined && price.original_amount !== null
      ? Number(price.original_amount)
      : null;

  return (
    <View style={styles.container}>
      <Text style={styles.current}>
        {formatCurrencyPrice(price.amount, price.currency)}
      </Text>
      {originalAmount !== null &&
      Number.isFinite(originalAmount) &&
      Number.isFinite(currentAmount) &&
      originalAmount > currentAmount ? (
        <Text style={styles.original}>
          {formatCurrencyPrice(originalAmount, price.currency)}
        </Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flexDirection: "row", gap: 7, alignItems: "center" },
  current: { fontSize: 14, fontWeight: "700", color: "#111827" },
  original: { fontSize: 11, textDecorationLine: "line-through", color: "#6B7280" },
  unavailable: { fontSize: 13, color: "#6B7280" },
});
