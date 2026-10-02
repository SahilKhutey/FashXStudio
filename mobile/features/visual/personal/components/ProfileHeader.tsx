import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { SavedSummaryContract } from "../types";

interface ProfileHeaderProps {
  displayName: string;
  avatarUrl?: string | null;
  bio?: string | null;
  savedSummary?: SavedSummaryContract;
  onEditProfile?: () => void;
  testID?: string;
}

export const ProfileHeader: React.FC<ProfileHeaderProps> = ({
  displayName,
  avatarUrl,
  bio,
  savedSummary,
  onEditProfile,
  testID = "profile-header",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.topRow}>
        <View style={styles.avatarContainer}>
          {avatarUrl ? (
            <Image source={{ uri: avatarUrl }} style={styles.avatar} />
          ) : (
            <View style={styles.avatarFallback}>
              <Text style={styles.avatarInitial}>{displayName.charAt(0)}</Text>
            </View>
          )}
        </View>

        <View style={styles.infoCol}>
          <Text style={styles.name}>{displayName}</Text>
          <Text style={styles.badge}>PERSONAL FASHION SPACE</Text>
          {bio && <Text style={styles.bio}>{bio}</Text>}
        </View>
      </View>

      <TouchableOpacity
        testID="profile-edit-button"
        style={styles.editButton}
        onPress={onEditProfile}
        accessibilityRole="button"
        accessibilityLabel="Edit Profile"
      >
        <Text style={styles.editButtonText}>Edit Profile</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  topRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  avatarContainer: {
    marginRight: 16,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#E5E5EA",
  },
  avatarFallback: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#1C1C1E",
    justifyContent: "center",
    alignItems: "center",
  },
  avatarInitial: {
    color: "#FFFFFF",
    fontSize: 24,
    fontWeight: "700",
  },
  infoCol: {
    flex: 1,
  },
  name: {
    fontSize: 20,
    fontWeight: "700",
    color: "#1C1C1E",
    letterSpacing: -0.4,
    marginBottom: 2,
  },
  badge: {
    fontSize: 10,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  bio: {
    fontSize: 13,
    color: "#636366",
    lineHeight: 18,
  },
  editButton: {
    borderWidth: 1,
    borderColor: "#C7C7CC",
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  editButtonText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#1C1C1E",
  },
});
