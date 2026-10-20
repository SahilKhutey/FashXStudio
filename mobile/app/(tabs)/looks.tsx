import React from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  FlatList,
} from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { useTryOnJobs, TryOnJobListItem } from "../../src/features/tryon/useTryOn";

function formatDate(isoDate?: string | null): string {
  if (!isoDate) return "";
  try {
    const d = new Date(isoDate);
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export default function LooksScreen() {
  const { t } = useTranslation();
  const router = useRouter();
  const { data: jobs, isLoading, isError, refetch, isRefetching } = useTryOnJobs();

  const renderItem = ({ item }: { item: TryOnJobListItem }) => {
    const isCompleted = item.status === "completed";
    const isFailed = item.status === "failed";
    const statusColor = isCompleted
      ? "#10B981"
      : isFailed
      ? "#EF4444"
      : "#3B82F6";

    return (
      <TouchableOpacity
        style={styles.card}
        activeOpacity={0.8}
        onPress={() => router.push(`/tryon/${item.job_id}`)}
        accessibilityRole="button"
        accessibilityLabel={`Try-on job ${item.job_id}`}
      >
        <View style={styles.thumbnailContainer}>
          {item.result_url ? (
            <Image
              source={{ uri: item.result_url, cacheKey: item.result_url.split("?")[0] }}
              style={styles.thumbnail}
              contentFit="cover"
              transition={200}
            />
          ) : (
            <View style={styles.thumbnailPlaceholder}>
              <Text style={styles.thumbnailIcon}>✨</Text>
            </View>
          )}
        </View>

        <View style={styles.detailsContainer}>
          <View style={[styles.statusBadge, { backgroundColor: `${statusColor}1A` }]}>
            <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
            <Text style={[styles.statusText, { color: statusColor }]}>
              {item.status.toUpperCase()}
            </Text>
          </View>

          <Text style={styles.dateText}>{formatDate(item.created_at)}</Text>
          <Text style={styles.jobIdText} numberOfLines={1}>
            ID: {item.job_id.slice(0, 8)}...
          </Text>
        </View>

        <Text style={styles.chevron}>›</Text>
      </TouchableOpacity>
    );
  };

  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorTitle}>{t("common.error")}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>{t("common.retry")}</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <FlatList
        data={jobs || []}
        renderItem={renderItem}
        keyExtractor={(item) => item.job_id}
        refreshing={isRefetching}
        onRefresh={refetch}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>📸</Text>
            <Text style={styles.emptyTitle}>{t("looks.empty")}</Text>
            <Text style={styles.emptySub}>{t("looks.emptySub")}</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F9FAFB",
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  listContent: {
    padding: 16,
    flexGrow: 1,
  },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 12,
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  thumbnailContainer: {
    width: 68,
    height: 80,
    borderRadius: 8,
    backgroundColor: "#F3F4F6",
    overflow: "hidden",
  },
  thumbnail: {
    width: "100%",
    height: "100%",
  },
  thumbnailPlaceholder: {
    width: "100%",
    height: "100%",
    justifyContent: "center",
    alignItems: "center",
  },
  thumbnailIcon: {
    fontSize: 24,
  },
  detailsContainer: {
    flex: 1,
    marginLeft: 14,
    justifyContent: "center",
  },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    marginBottom: 6,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 6,
  },
  statusText: {
    fontSize: 11,
    fontWeight: "700",
  },
  dateText: {
    fontSize: 13,
    color: "#4B5563",
    marginBottom: 2,
  },
  jobIdText: {
    fontSize: 11,
    color: "#9CA3AF",
  },
  chevron: {
    fontSize: 22,
    color: "#D1D5DB",
    paddingHorizontal: 8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingTop: 80,
    paddingHorizontal: 24,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
  },
  emptySub: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    lineHeight: 20,
  },
  errorTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 12,
  },
  retryButton: {
    backgroundColor: "#4F46E5",
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
});
