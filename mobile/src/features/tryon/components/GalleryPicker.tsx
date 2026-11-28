import React from "react";
import { Alert, Pressable, StyleSheet, Text } from "react-native";
import * as ImagePicker from "expo-image-picker";

interface Props {
  onSelected: (uri: string) => void;
}

export function GalleryPicker({ onSelected }: Props) {
  async function selectPhoto() {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ["images"],
        allowsEditing: false,
        quality: 1,
        exif: false,
      });

      if (result.canceled || !result.assets?.length) {
        return;
      }

      const firstAsset = result.assets[0];
      if (firstAsset?.uri) {
        onSelected(firstAsset.uri);
      }
    } catch {
      Alert.alert(
        "Unable to open photos",
        "Please try again or use your camera.",
      );
    }
  }

  return (
    <Pressable
      onPress={() => {
        void selectPhoto();
      }}
      accessibilityRole="button"
      style={styles.button}
    >
      <Text style={styles.text}>Choose from gallery</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    alignItems: "center",
  },
  text: { fontWeight: "600", color: "#111827" },
});
