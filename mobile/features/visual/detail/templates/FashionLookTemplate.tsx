import React from "react";
import { View, StyleSheet, ScrollView, SafeAreaView } from "react-native";
import { FashionLookDetailTemplateSpecContract } from "../types";
import { LookDetailView } from "../components/LookDetailView";

interface FashionLookTemplateProps {
  spec: FashionLookDetailTemplateSpecContract;
  onSelectProduct?: (productId: string) => void;
  onSaveLook?: () => void;
  testID?: string;
}

export const FashionLookTemplate: React.FC<FashionLookTemplateProps> = ({
  spec,
  onSelectProduct,
  onSaveLook,
  testID = "fashion-look-template",
}) => {
  return (
    <SafeAreaView testID={testID} style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <LookDetailView
          heroImageUri={spec.hero_image_uri}
          lookTitle={spec.name}
          styleName={spec.style}
          contextDescription={spec.context_description}
          outfitItems={spec.outfit_items}
          hotspots={spec.hotspots}
          onSelectProduct={onSelectProduct}
          onSaveLook={onSaveLook}
          isSaved={spec.is_saved}
        />
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: "#ffffff",
  },
  scrollContent: {
    paddingBottom: 40,
  },
});
