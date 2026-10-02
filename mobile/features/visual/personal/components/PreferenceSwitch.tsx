import React from "react";
import { View, Text, StyleSheet, Switch } from "react-native";

interface PreferenceSwitchProps {
  label: string;
  description?: string;
  value: boolean;
  onValueChange: (val: boolean) => void;
  testID?: string;
}

export const PreferenceSwitch: React.FC<PreferenceSwitchProps> = ({
  label,
  description,
  value,
  onValueChange,
  testID = "preference-switch",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.textCol}>
        <Text style={styles.label}>{label}</Text>
        {description && <Text style={styles.description}>{description}</Text>}
      </View>
      <Switch
        testID={`${testID}-toggle`}
        value={value}
        onValueChange={onValueChange}
        accessibilityRole="switch"
        accessibilityLabel={label}
        accessibilityState={{ checked: value }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  textCol: {
    flex: 1,
    marginRight: 16,
  },
  label: {
    fontSize: 15,
    fontWeight: "600",
    color: "#1C1C1E",
    marginBottom: 2,
  },
  description: {
    fontSize: 12,
    color: "#636366",
    lineHeight: 16,
  },
});
