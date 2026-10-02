import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { MixMatchTemplateSpecContract } from "../types";
import { MixMatchMatrix } from "../components/MixMatchMatrix";

interface MixMatchTemplateProps {
  data: MixMatchTemplateSpecContract;
  onSelectCandidate: (slotId: string, productId: string) => void;
  onBackToBuilder?: () => void;
  testID?: string;
}

export const MixMatchTemplate: React.FC<MixMatchTemplateProps> = ({
  data,
  onSelectCandidate,
  onBackToBuilder,
  testID = "mix-match-screen",
}) => {
  return (
    <View testID={testID} style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Mix & Match Studio</Text>
          <Text style={styles.subtitle}>Tap any candidate to swap it into your active look</Text>
        </View>
        {onBackToBuilder && (
          <TouchableOpacity
            testID="back-to-builder-btn"
            style={styles.doneBtn}
            onPress={onBackToBuilder}
          >
            <Text style={styles.doneBtnText}>Done</Text>
          </TouchableOpacity>
        )}
      </View>

      <MixMatchMatrix matrix={data.matrix} onSelectCandidate={onSelectCandidate} />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: "#eeeeee",
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    color: "#111111",
  },
  subtitle: {
    fontSize: 11,
    color: "#6b7280",
    marginTop: 2,
  },
  doneBtn: {
    backgroundColor: "#111111",
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 6,
  },
  doneBtnText: {
    color: "#ffffff",
    fontSize: 12,
    fontWeight: "600",
  },
});
