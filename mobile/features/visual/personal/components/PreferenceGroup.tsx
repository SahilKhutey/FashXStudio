import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface PreferenceGroupProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  testID?: string;
}

export const PreferenceGroup: React.FC<PreferenceGroupProps> = ({
  title,
  subtitle,
  children,
  testID = "preference-group",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      <View style={styles.content}>{children}</View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.2,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 12,
    color: "#636366",
    marginBottom: 12,
    lineHeight: 16,
  },
  content: {
    paddingTop: 4,
  },
});
