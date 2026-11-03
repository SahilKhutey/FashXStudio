import React, { useMemo, useState } from "react";
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  FlatList,
  ScrollView,
} from "react-native";
import { Image } from "expo-image";
import { useRouter } from "expo-router";
import { useTranslation } from "react-i18next";
import { useTryOnJobs, TryOnJobListItem } from "../../src/features/tryon/useTryOn";
import {
  useDesignTokens,
  AppText,
  CategoryChip,
  SectionHeader,
  spacing,
  radius,
} from "../../src/design-system";
import { LoadingState, ErrorState, EmptyState } from "../../src/components/states";

const STATUS_FILTERS = [
  { id: "all", label: "All Looks" },
  { id: "completed", label: "Completed" },
  { id: "processing", label: "Processing" },
  { id: "failed", label: "Failed" },
];

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
  const [selectedFilter, setSelectedFilter] = useState("all");

  const filteredJobs = useMemo(() => {
    if (!jobs) return [];
    if (selectedFilter === "all") return jobs;
    if (selectedFilter === "processing") {
      return jobs.filter(
        (j) =>
          j.status === "queued" ||
          j.status === "validating" ||
          j.status === "preprocessing" ||
          j.status === "inference" ||
          j.status === "postprocessing" ||
          j.status === "quality_check"
      );
    }
    return jobs.filter((j) => j.status === selectedFilter);
  }, [jobs, selectedFilter]);

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
        style={[styles.card, { backgroundColor: colors.surface, borderColor: colors.border }]}
        activeOpacity={0.8}
        onPress={() => router.push(`/tryon/${item.job_id}` as any)}
        accessibilityRole="button"
        accessibilityLabel={`Try-on job ${item.job_id} status ${item.status}`}
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
              <Text style={styles.thumbnailIcon}>
                {isFailed ? "⚠️" : "✨"}
              </Text>
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
          {item.status === "completed" && (
            <AppText variant="caption" color="textPrimary" style={styles.viewResultText}>
              View Look ›
            </AppText>
          )}
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
      <View style={styles.filterArea}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.filterScroll}
        >
          {STATUS_FILTERS.map((f) => (
            <CategoryChip
              key={f.id}
              label={f.label}
              selected={selectedFilter === f.id}
              onPress={() => setSelectedFilter(f.id)}
              style={styles.chip}
            />
          ))}
        </ScrollView>
      </View>

      <FlatList
        data={filteredJobs}
        renderItem={renderItem}
        keyExtractor={(item) => item.job_id}
        refreshing={isRefetching}
        onRefresh={() => void refetch()}
        contentContainerStyle={styles.listContent}
        ListHeaderComponent={
          jobs && jobs.length > 0 ? (
            <SectionHeader
              title="Virtual Try-On Edits"
              subtitle="Renders, poses, and outfit experiments"
              actionLabel="Try on more"
              onAction={() => router.push("/explore" as any)}
            />
          ) : undefined
        }
        ListEmptyComponent={
          <EmptyState
            icon="▧"
            title="No Try-On Looks Yet"
            message="Experience how clothes fit you before buying. Select any garment from Discover or Explore to start your first virtual try-on."
            actionLabel="Discover styles"
            onAction={() => router.push("/explore" as any)}
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
  filterArea: {
    paddingHorizontal: spacing[4],
    paddingTop: spacing[3],
    paddingBottom: spacing[1],
  },
  filterScroll: {
    gap: spacing[2],
  },
  chip: {
    marginRight: spacing[2],
  },
  listContent: {
    padding: spacing[4],
    flexGrow: 1,
  },
  card: {
    borderRadius: radius.lg,
    padding: spacing[3],
    marginBottom: spacing[3],
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
  },
  thumbnailContainer: {
    width: 72,
    height: 96,
    borderRadius: radius.md,
    overflow: "hidden",
  },
  thumbnail: {
    width: "100%",
    height: "100%",
  },
  thumbnailPlaceholder: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  thumbnailIcon: {
    fontSize: 26,
  },
  detailsContainer: {
    flex: 1,
    marginLeft: spacing[3],
    justifyContent: "center",
  },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: radius.pill,
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
    marginBottom: 2,
  },
  jobIdText: {
    marginBottom: 4,
  },
  viewResultText: {
    fontWeight: "600",
    marginTop: 2,
  },
  chevron: {
    fontSize: 20,
    fontWeight: "700",
    paddingHorizontal: 8,
  },
});
