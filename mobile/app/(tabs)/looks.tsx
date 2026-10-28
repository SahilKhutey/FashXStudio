import React from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  FlatList,
} from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { useTryOnJobs, TryOnJobListItem } from "../../src/features/tryon/useTryOn";
import { useDesignTokens, AppText, spacing, radius } from "../../src/design-system";
import { LoadingState, ErrorState, EmptyState } from "../../src/components/states";

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
  const { colors } = useDesignTokens();
  const { data: jobs, isLoading, isError, refetch, isRefetching } = useTryOnJobs();

  const renderItem = ({ item }: { item: TryOnJobListItem }) => {
    const isCompleted = item.status === "completed";
    const isFailed = item.status === "failed";
    const statusColor = isCompleted
      ? colors.success
      : isFailed
      ? colors.danger
      : colors.info;

    return (
      <TouchableOpacity
        style={[styles.card, { backgroundColor: colors.surface }]}
        activeOpacity={0.8}
        onPress={() => router.push(`/tryon/${item.job_id}`)}
        accessibilityRole="button"
        accessibilityLabel={`Try-on job ${item.job_id}`}
      >
        <View style={[styles.thumbnailContainer, { backgroundColor: colors.surfaceSecondary }]}>
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

          <AppText variant="caption" color="textSecondary" style={styles.dateText}>
            {formatDate(item.created_at)}
          </AppText>
          <AppText variant="caption" color="textMuted" style={styles.jobIdText} numberOfLines={1}>
            ID: {item.job_id.slice(0, 8)}...
          </AppText>
        </View>

        <Text style={[styles.chevron, { color: colors.borderStrong }]}>›</Text>
      </TouchableOpacity>
    );
  };

  if (isLoading) {
    return <LoadingState message={t("common.loading")} />;
  }

  if (isError) {
    return <ErrorState onRetry={() => void refetch()} />;
  }

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <FlatList
        data={jobs || []}
        renderItem={renderItem}
        keyExtractor={(item) => item.job_id}
        refreshing={isRefetching}
        onRefresh={() => void refetch()}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <EmptyState
            icon="📸"
            title={t("looks.empty")}
            message={t("looks.emptySub")}
            actionLabel={t("common.retry")}
            onAction={() => void refetch()}
          />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  listContent: {
    padding: spacing[4],
    flexGrow: 1,
  },
  card: {
    borderRadius: radius.lg,
    padding: spacing[3],
    flexDirection: "row",
    alignItems: "center",
    marginBottom: spacing[3],
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  thumbnailContainer: {
    width: 68,
    height: 80,
    borderRadius: radius.md,
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
    paddingHorizontal: spacing[2],
    paddingVertical: 3,
    borderRadius: radius.lg,
    marginBottom: spacing[1.5],
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
    marginBottom: 2,
  },
  jobIdText: {},
  chevron: {
    fontSize: 22,
    paddingHorizontal: spacing[2],
  },
});
