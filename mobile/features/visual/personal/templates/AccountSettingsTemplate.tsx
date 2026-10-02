import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput } from "react-native";
import { AccountSettingsTemplateSpecContract, AccountSettingsContract } from "../types";
import { SettingsSection } from "../components/SettingsSection";
import { SettingsNavigation } from "../components/SettingsNavigation";
import { PreferenceSwitch } from "../components/PreferenceSwitch";

interface AccountSettingsTemplateProps {
  data: AccountSettingsTemplateSpecContract;
  activeCategory?: string;
  onSelectCategory?: (category: string) => void;
  onUpdateName?: (name: string) => void;
  onToggleNotifications?: (enabled: boolean) => void;
  onToggle2FA?: (enabled: boolean) => void;
  onSelectPrivacyLevel?: (level: string) => void;
  onSelectRetention?: (retention: string) => void;
  onSaveChanges?: () => void;
  onDiscardChanges?: () => void;
  onSignOut?: () => void;
  testID?: string;
}

export const AccountSettingsTemplate: React.FC<AccountSettingsTemplateProps> = ({
  data,
  activeCategory = "profile",
  onSelectCategory,
  onUpdateName,
  onToggleNotifications,
  onToggle2FA,
  onSelectPrivacyLevel,
  onSelectRetention,
  onSaveChanges,
  onDiscardChanges,
  onSignOut,
  testID = "account-settings-pr11",
}) => {
  const privacyLevels = ["minimal", "standard", "enhanced"];
  const retentionOptions = ["30_days", "90_days", "1_year", "indefinite"];

  return (
    <ScrollView testID={testID} style={styles.container}>
      <SettingsNavigation
        categories={data.categories}
        activeCategory={activeCategory}
        onSelectCategory={onSelectCategory || (() => {})}
        onSignOut={onSignOut}
      />

      <SettingsSection
        title="Account & Security"
        hasUnsavedChanges={data.has_unsaved_changes}
        saveState={data.state}
        onSave={onSaveChanges}
        onDiscard={onDiscardChanges}
        testID="settings-profile-section"
      >
        <View style={styles.field}>
          <Text style={styles.fieldLabel}>DISPLAY NAME</Text>
          <TextInput
            testID="settings-name-input"
            style={styles.textInput}
            value={data.settings.display_name}
            onChangeText={onUpdateName}
          />
        </View>

        <View style={styles.field}>
          <Text style={styles.fieldLabel}>ACCOUNT EMAIL</Text>
          <Text style={styles.readOnlyEmail}>{data.settings.email}</Text>
        </View>

        <PreferenceSwitch
          testID="notif-switch"
          label="Push Notifications"
          description="Receive drops, outfit reminders, and price reduction alerts."
          value={data.settings.notifications_enabled}
          onValueChange={onToggleNotifications || (() => {})}
        />

        <PreferenceSwitch
          testID="two-fa-switch"
          label="Two-Factor Authentication"
          description="Protect your personal fashion space with biometric or SMS verification."
          value={data.settings.two_factor_auth}
          onValueChange={onToggle2FA || (() => {})}
        />

        <View style={styles.field}>
          <Text style={styles.fieldLabel}>PRIVACY LEVEL</Text>
          <View style={styles.chipsRow}>
            {privacyLevels.map((lvl) => {
              const isSelected = data.settings.privacy_level === lvl;
              return (
                <TouchableOpacity
                  key={lvl}
                  testID={`privacy-${lvl}`}
                  style={[styles.chip, isSelected ? styles.selectedChip : styles.unselectedChip]}
                  onPress={() => onSelectPrivacyLevel && onSelectPrivacyLevel(lvl)}
                >
                  <Text
                    style={[
                      styles.chipText,
                      isSelected ? styles.selectedChipText : styles.unselectedChipText,
                    ]}
                  >
                    {lvl.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View style={styles.field}>
          <Text style={styles.fieldLabel}>ACTIVITY HISTORY RETENTION</Text>
          <View style={styles.chipsRow}>
            {retentionOptions.map((ret) => {
              const isSelected = data.settings.activity_history_retention === ret;
              return (
                <TouchableOpacity
                  key={ret}
                  testID={`retention-${ret}`}
                  style={[styles.chip, isSelected ? styles.selectedChip : styles.unselectedChip]}
                  onPress={() => onSelectRetention && onSelectRetention(ret)}
                >
                  <Text
                    style={[
                      styles.chipText,
                      isSelected ? styles.selectedChipText : styles.unselectedChipText,
                    ]}
                  >
                    {ret.replace("_", " ")}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
        </View>
      </SettingsSection>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F2F2F7",
    padding: 16,
  },
  field: {
    marginVertical: 10,
  },
  fieldLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 6,
  },
  textInput: {
    borderWidth: 1,
    borderColor: "#C7C7CC",
    backgroundColor: "#FFFFFF",
    borderRadius: 6,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 14,
    color: "#1C1C1E",
  },
  readOnlyEmail: {
    fontSize: 14,
    color: "#636366",
    paddingVertical: 4,
  },
  chipsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginTop: 4,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
  },
  selectedChip: {
    backgroundColor: "#1C1C1E",
    borderColor: "#1C1C1E",
  },
  unselectedChip: {
    backgroundColor: "#F2F2F7",
    borderColor: "#E5E5EA",
  },
  chipText: {
    fontSize: 11,
    fontWeight: "600",
  },
  selectedChipText: {
    color: "#FFFFFF",
  },
  unselectedChipText: {
    color: "#1C1C1E",
  },
});
