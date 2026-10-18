import React, { useState } from "react";
import {
  View,
  Text,
  Pressable,
  ActivityIndicator,
  StyleSheet,
  Dimensions,
} from "react-native";
import { Image } from "expo-image";
import { FlashList } from "@shopify/flash-list";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useRouter } from "expo-router";
import { api } from "../../src/api/client";
import { isDevTokenEnabled } from "../../src/lib/env";

export interface StyleQuizItem {
  id: string;
  title: string;
  category: string;
  subcategory?: string | null;
  image_url?: string | null;
  tags?: string[];
}

interface StyleQuizResponse {
  garments: StyleQuizItem[];
}

const { width } = Dimensions.get("window");
const TILE_WIDTH = (width - 48 - 12) / 2;

export default function StyleQuizScreen() {
  const router = useRouter();
  const { t } = useTranslation();
  const qc = useQueryClient();

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["quiz"],
    queryFn: async () => {
      const res = await api<StyleQuizResponse>("/onboarding/style-quiz?count=10");
      return res.garments || [];
    },
  });

  const [picked, setPicked] = useState<Set<string>>(new Set());

  const items = data || [];
  const min = Math.min(3, items.length || 3);

  const toggle = (id: string) => {
    setPicked((prev) => {
      const nextSet = new Set(prev);
      if (nextSet.has(id)) {
        nextSet.delete(id);
      } else {
        if (nextSet.size < 10) {
          nextSet.add(id);
        }
      }
      return nextSet;
    });
  };

  const save = useMutation({
    mutationFn: () =>
      api("/onboarding/style-quiz/picks", {
        method: "POST",
        body: JSON.stringify({ garment_ids: [...picked] }),
      }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] });
      router.push("/onboarding/capture");
    },
  });

  const canContinue = picked.size >= min && !save.isPending;

  // 1. Loading state with skeleton indicator
  if (isLoading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={styles.loadingText}>{t("common.loading")}</Text>
      </View>
    );
  }

  // 2. Error state with retry
  if (isError) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorTitle} accessibilityRole="header">
          {t("common.error")}
        </Text>
        <Text style={styles.errorMessage}>{t("common.networkError")}</Text>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t("common.retry")}
          onPress={() => refetch()}
          style={styles.retryButton}
        >
          <Text style={styles.retryButtonText}>{t("common.retry")}</Text>
        </Pressable>
      </View>
    );
  }

  // 3. Empty catalog state
  if (items.length === 0) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.emptyTitle}>{t("quiz.emptyCatalog")}</Text>
        {isDevTokenEnabled() && (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={t("quiz.skipDev")}
            onPress={async () => {
              await qc.invalidateQueries({ queryKey: ["me"] });
              router.push("/onboarding/capture");
            }}
            style={styles.devSkipButton}
          >
            <Text style={styles.devSkipText}>{t("quiz.skipDev")}</Text>
          </Pressable>
        )}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title} accessibilityRole="header">
          {t("quiz.title")}
        </Text>
        <Text style={styles.subtitle}>{t("quiz.subtitle")}</Text>
        <Text
          style={styles.countBadge}
          accessibilityLiveRegion="polite"
        >
          {t("quiz.pickedCount", { count: picked.size, min })}
        </Text>
      </View>

      <FlashList
        data={items}
        numColumns={2}
        contentContainerStyle={styles.listContainer}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => {
          const isSelected = picked.has(item.id);
          return (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${item.title}, ${item.category}`}
              accessibilityState={{ selected: isSelected }}
              onPress={() => toggle(item.id)}
              style={[styles.tile, isSelected && styles.tileSelected]}
            >
              {item.image_url ? (
                <Image
                  source={{ uri: item.image_url }}
                  style={styles.tileImage}
                  contentFit="cover"
                  transition={200}
                />
              ) : (
                <View style={[styles.tileImage, styles.placeholderImage]}>
                  <Text style={styles.placeholderText}>{item.category}</Text>
                </View>
              )}
              <View style={styles.tileContent}>
                <Text style={styles.tileTitle} numberOfLines={1}>
                  {item.title}
                </Text>
                <Text style={styles.tileCategory} numberOfLines={1}>
                  {item.category}
                </Text>
              </View>
              <View style={[styles.checkmark, isSelected && styles.checkmarkSelected]}>
                {isSelected ? <Text style={styles.checkmarkIcon}>✓</Text> : null}
              </View>
            </Pressable>
          );
        }}
      />

      <View style={styles.footer}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t("common.continue")}
          accessibilityState={{ disabled: !canContinue }}
          disabled={!canContinue}
          onPress={() => save.mutate()}
          style={[styles.continueButton, !canContinue && styles.buttonDisabled]}
        >
          {save.isPending ? (
            <ActivityIndicator color="#FFFFFF" size="small" />
          ) : (
            <Text style={styles.continueText}>{t("common.continue")}</Text>
          )}
        </Pressable>
      </View>
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
    backgroundColor: "#FFFFFF",
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 12,
    backgroundColor: "#FFFFFF",
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#4B5563",
    lineHeight: 20,
    marginBottom: 10,
  },
  countBadge: {
    fontSize: 13,
    fontWeight: "600",
    color: "#4F46E5",
  },
  listContainer: {
    padding: 18,
  },
  tile: {
    width: TILE_WIDTH,
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    margin: 6,
    borderWidth: 2,
    borderColor: "#E5E7EB",
    overflow: "hidden",
    position: "relative",
  },
  tileSelected: {
    borderColor: "#4F46E5",
  },
  tileImage: {
    width: "100%",
    height: TILE_WIDTH * 1.25,
    backgroundColor: "#F3F4F6",
  },
  placeholderImage: {
    justifyContent: "center",
    alignItems: "center",
  },
  placeholderText: {
    fontSize: 13,
    color: "#9CA3AF",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  tileContent: {
    padding: 8,
  },
  tileTitle: {
    fontSize: 13,
    fontWeight: "600",
    color: "#111827",
  },
  tileCategory: {
    fontSize: 11,
    color: "#6B7280",
    textTransform: "capitalize",
    marginTop: 2,
  },
  checkmark: {
    position: "absolute",
    top: 8,
    right: 8,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: "rgba(255,255,255,0.85)",
    borderWidth: 1,
    borderColor: "#D1D5DB",
    justifyContent: "center",
    alignItems: "center",
  },
  checkmarkSelected: {
    backgroundColor: "#4F46E5",
    borderColor: "#4F46E5",
  },
  checkmarkIcon: {
    color: "#FFFFFF",
    fontSize: 12,
    fontWeight: "700",
  },
  footer: {
    padding: 20,
    backgroundColor: "#FFFFFF",
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
  continueButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: "center",
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  continueText: {
    color: "#FFFFFF",
    fontSize: 16,
    fontWeight: "600",
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: "#6B7280",
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
  },
  errorMessage: {
    fontSize: 14,
    color: "#4B5563",
    textAlign: "center",
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: "#4F46E5",
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 8,
  },
  retryButtonText: {
    color: "#FFFFFF",
    fontWeight: "600",
  },
  emptyTitle: {
    fontSize: 16,
    color: "#6B7280",
    marginBottom: 16,
  },
  devSkipButton: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#4F46E5",
  },
  devSkipText: {
    color: "#4F46E5",
    fontWeight: "600",
  },
});
