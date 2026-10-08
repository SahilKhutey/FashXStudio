import { StyleSheet, Text, View } from "react-native";

const GUIDE = [
  "Face the camera directly",
  "Keep your full body in frame",
  "Stand upright with arms slightly away",
  "Use even lighting",
  "Keep a plain background",
];

export function CaptureGuide() {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Before you capture</Text>
      {GUIDE.map((item) => (
        <View key={item} style={styles.row}>
          <Text style={styles.dot}>•</Text>
          <Text style={styles.item}>{item}</Text>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 16,
    borderRadius: 18,
    backgroundColor: "#111827",
    gap: 8,
  },
  title: { color: "#fff", fontSize: 16, fontWeight: "700", marginBottom: 2 },
  row: { flexDirection: "row", gap: 8, alignItems: "flex-start" },
  dot: { color: "#fff", fontSize: 18, lineHeight: 20 },
  item: { flex: 1, color: "#e5e7eb", fontSize: 14, lineHeight: 20 },
});
