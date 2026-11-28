import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { TRYON_DISCLAIMER } from "../constants";

type Props = {
  customText?: string | null;
};

export function VisualSimulationNotice({ customText }: Props) {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>{customText || TRYON_DISCLAIMER}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#F3F4F6",
    borderRadius: 10,
    padding: 12,
  },
  text: {
    fontSize: 12,
    lineHeight: 18,
    color: "#374151",
  },
});
