import { Link } from "expo-router";
import { StyleSheet, Text, View, Pressable } from "react-native";

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>AI Fashion Assistant</Text>
      <Text style={styles.subtitle}>Foundation 7 capture flow is ready.</Text>
      <Link href="/feed" asChild>
        <Pressable style={styles.button}>
          <Text style={styles.buttonText}>Browse Fashion Feed</Text>
        </Pressable>
      </Link>
      <Link href="/capture/tryon" asChild>
        <Pressable style={styles.button}>
          <Text style={styles.buttonText}>Set Up Try-On Photo</Text>
        </Pressable>
      </Link>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  title: { fontSize: 28, fontWeight: "700" },
  subtitle: { marginTop: 8, fontSize: 16, textAlign: "center" },
  button: { marginTop: 24, backgroundColor: "#111827", borderRadius: 14, paddingHorizontal: 20, paddingVertical: 14 },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "700" },
});
