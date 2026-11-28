import React from "react";
import { View, StyleSheet, type ViewProps } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useResponsiveLayout } from "../hooks/useResponsiveLayout";

type Props = ViewProps & {
  children: React.ReactNode;
  safeArea?: boolean;
};

export function ResponsiveContainer({
  children,
  safeArea = true,
  style,
  ...rest
}: Props) {
  const layout = useResponsiveLayout();
  const Wrapper = safeArea ? SafeAreaView : View;

  return (
    <Wrapper
      style={[
        styles.screen,
        { paddingHorizontal: layout.horizontalPadding },
      ]}
    >
      <View
        {...rest}
        style={[
          styles.content,
          { maxWidth: layout.contentMaxWidth },
          style,
        ]}
      >
        {children}
      </View>
    </Wrapper>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    width: "100%",
    alignItems: "center",
  },
  content: {
    flex: 1,
    width: "100%",
    alignSelf: "center",
  },
});
