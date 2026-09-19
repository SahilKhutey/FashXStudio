import React, { useMemo } from "react";
import { FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";

import { useFeed } from "../../features/feed/useFeed";
import { useRouter } from "expo-router";
import type { FeedItem } from "../../api/feed";

function priceLabel(minor?: number | null, currency?: string | null): string {
  if (minor == null) return "Price unavailable";
  const value = (minor / 100).toFixed(0);
  return `${currency ?? "INR"} ${value}`;
}

function FeedCard({ item }: { item: FeedItem }) {
  const router = useRouter();
  const product = item.product;
  return (
    <Pressable style={styles.card} onPress={() => router.push(`/product/${product.id}`)}>
      <View style={styles.imagePlaceholder}>
        <Text style={styles.placeholderText}>Fashion Image</Text>
      </View>
      <Text style={styles.title}>{product.display_name}</Text>
      <Text style={styles.meta}>{product.category}{product.subcategory ? ` · ${product.subcategory}` : ""}</Text>
      <Text style={styles.price}>{priceLabel(product.lowest_price_minor, product.currency)}</Text>
      <View style={styles.reasonRow}>
        {item.reasons.map((reason) => (
          <View key={reason} style={styles.reasonChip}>
            <Text style={styles.reason}>{reason.replaceAll("_", " ")}</Text>
          </View>
        ))}
      </View>
    </Pressable>
  );
}

export default function FeedScreen() {
  const feed = useFeed();
  const items = useMemo(() => feed.data?.pages.flatMap((page) => page.items) ?? [], [feed.data]);

  if (feed.isPending) {
    return <View style={styles.center}><Text>Loading your fashion feed…</Text></View>;
  }

  if (feed.isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>Unable to load the fashion feed.</Text>
        <Pressable style={styles.button} onPress={() => feed.refetch()}>
          <Text style={styles.buttonText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <FlatList
      contentContainerStyle={styles.list}
      data={items}
      keyExtractor={(item) => item.product.id}
      renderItem={({ item }) => <FeedCard item={item} />}
      onEndReached={() => {
        if (feed.hasNextPage && !feed.isFetchingNextPage) void feed.fetchNextPage();
      }}
      onEndReachedThreshold={0.5}
      refreshControl={
        <RefreshControl refreshing={feed.isRefetching} onRefresh={() => feed.refetch()} />
      }
      ListEmptyComponent={<View style={styles.center}><Text>No garments are available yet.</Text></View>}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: 16, gap: 12 },
  card: { borderRadius: 16, padding: 12, backgroundColor: "#ffffff", borderWidth: 1, borderColor: "#e5e7eb" },
  imagePlaceholder: { height: 220, borderRadius: 12, backgroundColor: "#f3f4f6", alignItems: "center", justifyContent: "center" },
  placeholderText: { color: "#6b7280" },
  title: { marginTop: 10, fontSize: 17, fontWeight: "600" },
  meta: { marginTop: 4, color: "#6b7280" },
  price: { marginTop: 8, fontWeight: "600" },
  reasonRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 },
  reasonChip: { borderRadius: 999, paddingHorizontal: 8, paddingVertical: 4, backgroundColor: "#f3f4f6" },
  reason: { fontSize: 12, color: "#4b5563" },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  error: { marginBottom: 12, textAlign: "center" },
  button: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 10, backgroundColor: "#111827" },
  buttonText: { color: "#ffffff", fontWeight: "600" },
});
