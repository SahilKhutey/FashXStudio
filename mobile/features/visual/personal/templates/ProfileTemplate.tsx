import React from "react";
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from "react-native";
import { ProfileTemplateSpecContract } from "../types";
import { ProfileHeader } from "../components/ProfileHeader";
import { ProfileSummary } from "../components/ProfileSummary";
import { RecentItem } from "../components/RecentItem";

interface ProfileTemplateProps {
  data: ProfileTemplateSpecContract;
  onEditProfile?: () => void;
  onNavigateCategory?: (category: string) => void;
  onNavigateSettings?: () => void;
  onOpenActivity?: (id: string, type: string) => void;
  testID?: string;
}

export const ProfileTemplate: React.FC<ProfileTemplateProps> = ({
  data,
  onEditProfile,
  onNavigateCategory,
  onNavigateSettings,
  onOpenActivity,
  testID = "profile-screen-pr01",
}) => {
  return (
    <ScrollView testID={testID} style={styles.container}>
      <ProfileHeader
        displayName={data.display_name}
        avatarUrl={data.avatar_url}
        bio={data.bio}
        savedSummary={data.saved_summary}
        onEditProfile={onEditProfile}
      />

      <ProfileSummary
        summary={data.saved_summary}
        onSelectCategory={onNavigateCategory}
      />

      {/* Your Style */}
      <View style={styles.section} testID="profile-style-tags">
        <Text style={styles.sectionTitle}>YOUR STYLE</Text>
        <View style={styles.tagsRow}>
          {data.style_tags.map((tag) => (
            <View key={tag} style={styles.styleTag}>
              <Text style={styles.styleTagText}>{tag}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Preferences Preview */}
      <View style={styles.section} testID="profile-pref-preview">
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>PREFERENCES PREVIEW</Text>
          <TouchableOpacity onPress={() => onNavigateCategory && onNavigateCategory("preferences")}>
            <Text style={styles.linkText}>Edit</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.tagsRow}>
          {data.preferences_preview.map((pref) => (
            <View key={pref} style={styles.prefChip}>
              <Text style={styles.prefChipText}>{pref}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Recent Activity */}
      <View style={styles.section} testID="profile-recent-activity">
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>RECENT ACTIVITY</Text>
          <TouchableOpacity onPress={() => onNavigateCategory && onNavigateCategory("recent")}>
            <Text style={styles.linkText}>See All</Text>
          </TouchableOpacity>
        </View>
        {data.recent_activity_preview.map((act) => (
          <RecentItem
            key={`${act.entity_id}-${act.timestamp}`}
            activity={act}
            onOpen={onOpenActivity}
          />
        ))}
      </View>

      {/* Regional Context Banner */}
      <View style={styles.section} testID="profile-regional-context">
        <Text style={styles.sectionTitle}>REGIONAL DISCOVERY</Text>
        <Text style={styles.regionalText}>
          Preferred Capital: {data.regional_context.preferred_city},{" "}
          {data.regional_context.preferred_country}
        </Text>
        <Text style={styles.disclaimerText}>{data.regional_context.disclaimer}</Text>
      </View>

      {/* Settings Action */}
      <View style={styles.section}>
        <TouchableOpacity
          testID="profile-settings-button"
          style={styles.settingsBtn}
          onPress={onNavigateSettings}
          accessibilityRole="button"
          accessibilityLabel="Open Account Settings"
        >
          <Text style={styles.settingsBtnText}>Account Settings & Privacy</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F2F2F7",
  },
  section: {
    backgroundColor: "#FFFFFF",
    padding: 16,
    marginVertical: 6,
  },
  sectionHeaderRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  linkText: {
    fontSize: 13,
    color: "#007AFF",
    fontWeight: "600",
  },
  tagsRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  styleTag: {
    backgroundColor: "#1C1C1E",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  styleTagText: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "600",
  },
  prefChip: {
    backgroundColor: "#F2F2F7",
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#E5E5EA",
  },
  prefChipText: {
    color: "#1C1C1E",
    fontSize: 12,
    fontWeight: "500",
  },
  regionalText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
    marginBottom: 4,
  },
  disclaimerText: {
    fontSize: 11,
    color: "#8E8E93",
    lineHeight: 15,
  },
  settingsBtn: {
    borderWidth: 1,
    borderColor: "#C7C7CC",
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: "center",
  },
  settingsBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
  },
});
