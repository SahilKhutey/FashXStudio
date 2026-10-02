import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { PersonalAIPreferencesContract } from "../types";
import { PreferenceSwitch } from "./PreferenceSwitch";

interface AIPreferencesProps {
  settings: PersonalAIPreferencesContract;
  onUpdateSettings: (newSettings: Partial<PersonalAIPreferencesContract>) => void;
  testID?: string;
}

export const AIPreferences: React.FC<AIPreferencesProps> = ({
  settings,
  onUpdateSettings,
  testID = "ai-preferences",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <Text style={styles.header}>AI INTELLIGENCE PRIVACY & CONTEXT</Text>

      <PreferenceSwitch
        testID="ai-rec-switch"
        label="AI Fashion Suggestions"
        description="Allow AI styling models to suggest garment combinations based on active context."
        value={settings.ai_recommendations_enabled}
        onValueChange={(val) => onUpdateSettings({ ai_recommendations_enabled: val })}
      />

      <PreferenceSwitch
        testID="ai-personalization-switch"
        label="AI Personalization"
        description="Permit the styling assistant to reference your saved looks and explicit aesthetic tags."
        value={settings.ai_personalization_enabled}
        onValueChange={(val) => onUpdateSettings({ ai_personalization_enabled: val })}
      />

      <View style={styles.contextBox}>
        <Text style={styles.contextTitle}>PERMITTED CONTEXT DATA</Text>
        <View style={styles.chipsRow}>
          {settings.ai_context_permitted.map((ctx) => (
            <View key={ctx} style={styles.contextChip}>
              <Text style={styles.contextChipText}>✓ {ctx.replace("_", " ").toUpperCase()}</Text>
            </View>
          ))}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    marginVertical: 8,
  },
  header: {
    fontSize: 11,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  contextBox: {
    marginTop: 14,
    padding: 12,
    backgroundColor: "#F2F2F7",
    borderRadius: 6,
  },
  contextTitle: {
    fontSize: 10,
    fontWeight: "700",
    color: "#5856D6",
    letterSpacing: 0.6,
    marginBottom: 8,
  },
  chipsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 6,
  },
  contextChip: {
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E5EA",
  },
  contextChipText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#1C1C1E",
  },
});
