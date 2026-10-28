import React from "react";
import {
  ScrollView,
  StyleSheet,
  View,
  type ScrollViewProps,
  type ViewStyle,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useDesignTokens } from "../design-system";

type ScreenContainerProps = {
  children: React.ReactNode;
  scroll?: boolean;
  padded?: boolean;
  style?: ViewStyle;
  contentContainerStyle?: ViewStyle;
  scrollProps?: Omit<ScrollViewProps, "children" | "style">;
};

export function ScreenContainer({
  children,
  scroll = false,
  padded = true,
  style,
  contentContainerStyle,
  scrollProps,
}: ScreenContainerProps) {
  const { colors, spacing } = useDesignTokens();

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.background }]}
      edges={["left", "right", "bottom"]}
    >
      {scroll ? (
        <ScrollView
          {...scrollProps}
          style={[styles.fill, style]}
          contentContainerStyle={[
            styles.content,
            padded && { padding: spacing[4] },
            contentContainerStyle,
          ]}
          keyboardShouldPersistTaps="handled"
        >
          {children}
        </ScrollView>
      ) : (
        <View
          style={[
            styles.fill,
            padded && { padding: spacing[4] },
            style,
          ]}
        >
          {children}
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  fill: {
    flex: 1,
  },
  content: {
    flexGrow: 1,
  },
});
