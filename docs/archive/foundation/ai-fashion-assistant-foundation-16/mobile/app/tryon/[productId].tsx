import React, { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Image, Pressable, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useCreateTryOn, useTryOnJob, useCancelTryOn } from "../../features/tryon/useTryOn";
import { useCatalogActions, useProductDetail } from "../../features/product/useProductDetail";

const TERMINAL = new Set(["completed", "failed", "cancelled"]);

function friendlyStatus(status?: string): string {
  switch (status) {
    case "queued": return "Preparing your try-on…";
    case "validating": return "Checking your inputs…";
    case "preprocessing": return "Preparing the garment and your photo…";
    case "inference": return "AI is generating your look…";
    case "postprocessing": return "Finishing your preview…";
    case "quality_check": return "Checking the generated image…";
    case "completed": return "Your try-on is ready";
    case "failed": return "Try-on could not be completed";
    case "cancelled": return "Try-on cancelled";
    default: return "Preparing your try-on…";
  }
}

export default function TryOnScreen() {
  const { productId } = useLocalSearchParams<{ productId: string }>();
  const router = useRouter();
  const [jobId, setJobId] = useState<string | null>(null);
  const [started, setStarted] = useState(false);
  const detail = useProductDetail(String(productId));
  const create = useCreateTryOn(String(productId));
  const cancel = useCancelTryOn();
  const catalogActions = useCatalogActions(String(productId));
  const status = useTryOnJob(jobId);

  const imageUrl = status.data?.result_url ?? status.data?.result?.result_url ?? null;
  const completed = status.data?.status === "completed" && Boolean(imageUrl);
  const failed = status.data?.status === "failed";
  const terminal = Boolean(status.data?.status && TERMINAL.has(status.data.status));
  const selectedOfferId = detail.data?.selected_offer_id ?? detail.data?.offers.find((o) => o.in_stock)?.id;

  useEffect(() => {
    if (!started && !jobId && productId) {
      setStarted(true);
      void create.mutateAsync()
        .then((response) => setJobId(response.job_id))
        .catch(() => undefined);
    }
  }, [create, jobId, productId, started]);

  const retry = async () => {
    setJobId(null);
    setStarted(true);
    const response = await create.mutateAsync();
    setJobId(response.job_id);
  };

  const buy = async () => {
    await catalogActions.save.mutateAsync(selectedOfferId);
    router.push({ pathname: "/product/[id]", params: { id: String(productId), offerId: selectedOfferId ?? "" } });
  };

  const statusText = useMemo(() => friendlyStatus(status.data?.status), [status.data?.status]);

  if (!productId) {
    return <SafeAreaView style={styles.center}><Text>Missing product.</Text></SafeAreaView>;
  }

  if (detail.isPending || create.isPending || (!jobId && !create.isError)) {
    return <Loading title="Starting virtual try-on" message="Preparing your selected garment." />;
  }

  if (create.isError && !jobId) {
    return <ErrorState title="We couldn't start try-on" message={create.error instanceof Error ? create.error.message : "Please try again."} onRetry={() => void retry()} />;
  }

  if (status.isError) {
    return <ErrorState title="We lost the try-on status" message="Your job may still be processing. Retry the status check." onRetry={() => void status.refetch()} />;
  }

  if (completed && imageUrl) {
    return (
      <SafeAreaView style={styles.safe}>
        <ScrollView contentContainerStyle={styles.container}>
          <Text style={styles.title}>Your try-on</Text>
          <View style={styles.resultCard}>
            <Image source={{ uri: imageUrl }} style={styles.resultImage} resizeMode="contain" />
          </View>
          <Text style={styles.confidenceLabel}>Generated preview</Text>
          {status.data?.result?.quality_score != null ? (
            <Text style={styles.subtle}>Technical image quality: {Math.round(status.data.result.quality_score * 100)}%</Text>
          ) : null}
          <View style={styles.actions}>
            <Pressable style={styles.primary} onPress={() => void catalogActions.save.mutateAsync(selectedOfferId)} disabled={catalogActions.save.isPending}>
              <Text style={styles.primaryText}>{catalogActions.save.isPending ? "Saving…" : "Save to wardrobe"}</Text>
            </Pressable>
            <Pressable style={styles.secondary} onPress={() => void buy()}>
              <Text style={styles.secondaryText}>Go to buy</Text>
            </Pressable>
          </View>
          <Pressable style={styles.link} onPress={() => void retry()}>
            <Text style={styles.linkText}>Try this garment again</Text>
          </Pressable>
        </ScrollView>
      </SafeAreaView>
    );
  }

  if (failed) {
    return <ErrorState title="Try-on failed" message={status.data?.failure_reason ?? "The preview could not be generated."} onRetry={() => void retry()} />;
  }

  if (status.data?.status === "cancelled") {
    return <ErrorState title="Try-on cancelled" message="You can start another preview whenever you're ready." onRetry={() => void retry()} />;
  }

  if (!terminal) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator size="large" />
        <Text style={styles.title}>{statusText}</Text>
        <Text style={styles.message}>This usually takes a few seconds. You can leave this screen and return later.</Text>
        {jobId ? <Text style={styles.jobId}>Job {jobId.slice(0, 8)}…</Text> : null}
        {jobId ? (
          <Pressable style={styles.cancel} onPress={() => void cancel.mutateAsync(jobId)} disabled={cancel.isPending}>
            <Text>{cancel.isPending ? "Cancelling…" : "Cancel"}</Text>
          </Pressable>
        ) : null}
      </SafeAreaView>
    );
  }

  return <Loading title="Preparing result" message="Please wait." />;
}

function Loading({ title, message }: { title: string; message: string }) {
  return <SafeAreaView style={styles.center}><ActivityIndicator size="large" /><Text style={styles.title}>{title}</Text><Text style={styles.message}>{message}</Text></SafeAreaView>;
}

function ErrorState({ title, message, onRetry }: { title: string; message: string; onRetry: () => void }) {
  return <SafeAreaView style={styles.center}><Text style={styles.title}>{title}</Text><Text style={styles.message}>{message}</Text><Pressable style={styles.primary} onPress={onRetry}><Text style={styles.primaryText}>Try again</Text></Pressable></SafeAreaView>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f8fafc" },
  container: { padding: 16, gap: 14 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24, gap: 14, backgroundColor: "#f8fafc" },
  title: { fontSize: 24, fontWeight: "800", color: "#111827", textAlign: "center" },
  message: { maxWidth: 340, textAlign: "center", color: "#4b5563", lineHeight: 22 },
  jobId: { color: "#9ca3af", fontSize: 12 },
  resultCard: { minHeight: 500, backgroundColor: "#fff", borderRadius: 20, overflow: "hidden", alignItems: "center", justifyContent: "center" },
  resultImage: { width: "100%", height: 520 },
  confidenceLabel: { fontSize: 16, fontWeight: "700" },
  subtle: { color: "#6b7280" },
  actions: { flexDirection: "row", gap: 10 },
  primary: { flex: 1, minHeight: 50, borderRadius: 13, backgroundColor: "#111827", alignItems: "center", justifyContent: "center", paddingHorizontal: 16 },
  primaryText: { color: "#fff", fontWeight: "700" },
  secondary: { flex: 1, minHeight: 50, borderRadius: 13, borderWidth: 1, borderColor: "#d1d5db", alignItems: "center", justifyContent: "center", paddingHorizontal: 16 },
  secondaryText: { fontWeight: "700", color: "#111827" },
  link: { alignItems: "center", paddingVertical: 10 },
  linkText: { fontWeight: "700", color: "#2563eb" },
  cancel: { minHeight: 44, paddingHorizontal: 22, alignItems: "center", justifyContent: "center", borderRadius: 12, borderWidth: 1, borderColor: "#d1d5db" },
});
