import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { ActivityContract } from "../types";

interface RecentItemProps {
  activity: ActivityContract;
  onOpen?: (entityId: string, entityType: string) => void;
  testID?: string;
}

export const RecentItem: React.FC<RecentItemProps> = ({
  activity,
  onOpen,
  testID = `recent-item-${activity.entity_id}`,
}) => {
  return (
    <View testID={testID} style={styles.card}>
      <View style={styles.thumbContainer}>
        {activity.image_url ? (
          <Image source={{ uri: activity.image_url }} style={styles.thumb} />
        ) : (
          <View style={styles.thumbPlaceholder}>
            <Text style={styles.placeholderText}>
              {activity.entity_type.charAt(0).toUpperCase()}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.infoCol}>
        <View style={styles.tagRow}>
          <Text style={styles.typeTag}>
            {activity.entity_type.toUpperCase()} • {activity.action.toUpperCase()}
          </Text>
        </View>
        <Text style={styles.title} numberOfLines={1}>
          {activity.title}
        </Text>
        {activity.subtitle && (
          <Text style={styles.subtitle} numberOfLines={1}>
            {activity.subtitle}
          </Text>
        )}
        <Text style={styles.viewedTime}>Viewed recently</Text>
      </View>

      <TouchableOpacity
        testID={`open-recent-${activity.entity_id}`}
        style={styles.openBtn}
        onPress={() => onOpen && onOpen(activity.entity_id, activity.entity_type)}
        accessibilityRole="button"
        accessibilityLabel={`Open ${activity.title}`}
      >
        <Text style={styles.openBtnText}>Open</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderColor: "#E5E5EA",
  },
  thumbContainer: {
    width: 48,
    height: 48,
    borderRadius: 6,
    overflow: "hidden",
    backgroundColor: "#F2F2F7",
    marginRight: 12,
  },
  thumb: {
    width: "100%",
    height: "100%",
    resizeMode: "cover",
  },
  thumbPlaceholder: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#E5E5EA",
  },
  placeholderText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#8E8E93",
  },
  infoCol: {
    flex: 1,
    marginRight: 8,
  },
  tagRow: {
    marginBottom: 2,
  },
  typeTag: {
    fontSize: 9,
    fontWeight: "700",
    color: "#8E8E93",
    letterSpacing: 0.5,
  },
  title: {
    fontSize: 14,
    fontWeight: "600",
    color: "#1C1C1E",
  },
  subtitle: {
    fontSize: 12,
    color: "#636366",
  },
  viewedTime: {
    fontSize: 10,
    color: "#8E8E93",
    marginTop: 2,
  },
  openBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: "#F2F2F7",
    borderRadius: 6,
  },
  openBtnText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#1C1C1E",
  },
});
