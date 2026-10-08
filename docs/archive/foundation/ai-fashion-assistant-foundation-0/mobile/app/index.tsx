import { StyleSheet, Text, View } from "react-native";

export default function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>AI Fashion Assistant</Text>
      <Text style={styles.subtitle}>Foundation 0 is running.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center", padding: 24 },
  title: { fontSize: 28, fontWeight: "700" },
  subtitle: { marginTop: 8, fontSize: 16 },
});
