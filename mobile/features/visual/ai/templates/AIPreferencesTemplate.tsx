import React, { useState } from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch } from "react-native";
import { AIPreferencesContract, AIPreferencesTemplateSpecContract } from "../types";

interface AIPreferencesTemplateProps {
  data: AIPreferencesTemplateSpecContract;
  onSavePreferences?: (prefs: AIPreferencesContract) => void;
  testID?: string;
}

export const AIPreferencesTemplate: React.FC<AIPreferencesTemplateProps> = ({
  data,
  onSavePreferences,
  testID = "ai-preferences-screen",
}) => {
  const { preferences, available_styles = [], available_occasions = [], budget_tiers = [] } = data;

  const [selectedStyles, setSelectedStyles] = useState<string[]>(preferences.preferred_styles || []);
  const [selectedOccasions, setSelectedOccasions] = useState<string[]>(preferences.preferred_occasions || []);
  const [selectedBudget, setSelectedBudget] = useState<string>(preferences.budget_tier || "medium");
  const [allowPersonalization, setAllowPersonalization] = useState<boolean>(preferences.allow_ai_personalization ?? true);
  const [autoSuggest, setAutoSuggest] = useState<boolean>(preferences.auto_suggest_outfits ?? true);

  const toggleStyle = (st: string) => {
    setSelectedStyles((prev) =>
      prev.includes(st) ? prev.filter((s) => s !== st) : [...prev, st]
    );
  };

  const toggleOccasion = (occ: string) => {
    setSelectedOccasions((prev) =>
      prev.includes(occ) ? prev.filter((o) => o !== occ) : [...prev, occ]
    );
  };

  const handleSave = () => {
    if (onSavePreferences) {
      onSavePreferences({
        ...preferences,
        preferred_styles: selectedStyles,
        preferred_occasions: selectedOccasions,
        budget_tier: selectedBudget,
        allow_ai_personalization: allowPersonalization,
        auto_suggest_outfits: autoSuggest,
      });
    }
  };

  return (
    <View testID={testID} style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.headerTag}>AI CONTROLS & TUNING</Text>
          <Text style={styles.title}>AI Intelligence Preferences</Text>
          <Text style={styles.subtitle}>
            Control recommendation boundaries and transparency. AI never modifies these without your permission.
          </Text>
        </View>

        {/* Style Directions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>PREFERRED AESTHETICS</Text>
          <View style={styles.chipsRow}>
            {available_styles.map((st) => {
              const active = selectedStyles.includes(st);
              return (
                <TouchableOpacity
                  key={st}
                  testID={`pref-style-${st}`}
                  style={[styles.chip, active && styles.chipActive]}
                  onPress={() => toggleStyle(st)}
                >
                  <Text style={[styles.chipText, active && styles.chipTextActive]}>{st}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Occasions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>OCCASION CONTEXTS</Text>
          <View style={styles.chipsRow}>
            {available_occasions.map((occ) => {
              const active = selectedOccasions.includes(occ);
              return (
                <TouchableOpacity
                  key={occ}
                  testID={`pref-occasion-${occ}`}
                  style={[styles.chip, active && styles.chipActive]}
                  onPress={() => toggleOccasion(occ)}
                >
                  <Text style={[styles.chipText, active && styles.chipTextActive]}>{occ}</Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Budget Tier */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>BUDGET TIER</Text>
          <View style={styles.chipsRow}>
            {budget_tiers.map((tier) => {
              const active = selectedBudget === tier;
              return (
                <TouchableOpacity
                  key={tier}
                  testID={`pref-budget-${tier}`}
                  style={[styles.chip, active && styles.chipActive]}
                  onPress={() => setSelectedBudget(tier)}
                >
                  <Text style={[styles.chipText, active && styles.chipTextActive]}>
                    {tier.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        {/* Permissions & Controls */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>PRIVACY & TRANSPARENCY CONTROLS</Text>
          <View style={styles.toggleRow}>
            <View style={styles.toggleInfo}>
              <Text style={styles.toggleLabel}>Allow AI Personalization</Text>
              <Text style={styles.toggleDesc}>Use wardrobe interactions to tune styling models.</Text>
            </View>
            <Switch
              testID="toggle-ai-personalization"
              value={allowPersonalization}
              onValueChange={setAllowPersonalization}
            />
          </View>

          <View style={styles.toggleRow}>
            <View style={styles.toggleInfo}>
              <Text style={styles.toggleLabel}>Automatic Outfit Suggestions</Text>
              <Text style={styles.toggleDesc}>Surface complete looks when viewing individual pieces.</Text>
            </View>
            <Switch
              testID="toggle-auto-suggest"
              value={autoSuggest}
              onValueChange={setAutoSuggest}
            />
          </View>
        </View>
      </ScrollView>

      {onSavePreferences && (
        <View style={styles.footer}>
          <TouchableOpacity
            testID="save-ai-preferences-btn"
            style={styles.saveButton}
            onPress={handleSave}
          >
            <Text style={styles.saveButtonText}>Save Preferences</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#FDFDFD",
  },
  content: {
    padding: 16,
    paddingBottom: 80,
  },
  header: {
    marginBottom: 20,
  },
  headerTag: {
    fontSize: 9,
    fontWeight: "700",
    color: "#5856D6",
    letterSpacing: 1,
    marginBottom: 4,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: "#1C1C1E",
  },
  subtitle: {
    fontSize: 13,
    color: "#636366",
    marginTop: 4,
    lineHeight: 18,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 1.1,
    marginBottom: 10,
  },
  chipsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  chip: {
    backgroundColor: "#F2F2F7",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
  },
  chipActive: {
    backgroundColor: "#1C1C1E",
    borderColor: "#1C1C1E",
  },
  chipText: {
    fontSize: 12,
    color: "#1C1C1E",
  },
  chipTextActive: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
  toggleRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5EA",
    padding: 14,
    marginBottom: 10,
  },
  toggleInfo: {
    flex: 1,
    marginRight: 12,
  },
  toggleLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  toggleDesc: {
    fontSize: 11,
    color: "#8E8E93",
    marginTop: 2,
  },
  footer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "#FFFFFF",
    borderTopWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
    padding: 16,
  },
  saveButton: {
    backgroundColor: "#1C1C1E",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  saveButtonText: {
    color: "#FFFFFF",
    fontSize: 14,
    fontWeight: "700",
  },
});
