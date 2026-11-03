import React from "react";
import {
  Pressable,
  StyleSheet,
  TextInput,
  View,
  type ViewStyle,
} from "react-native";
import { AppText } from "./AppText";
import { useDesignTokens } from "../useDesignTokens";

export type SearchBarProps = {
  value: string;
  onChangeText: (text: string) => void;
  onSubmit?: () => void;
  onClear?: () => void;
  placeholder?: string;
  style?: ViewStyle;
  autoFocus?: boolean;
};

export function SearchBar({
  value,
  onChangeText,
  onSubmit,
  onClear,
  placeholder = "Search styles, brands, garments...",
  style,
  autoFocus = false,
}: SearchBarProps) {
  const { colors, radius, spacing } = useDesignTokens();

  return (
    <View
      style={[
        styles.container,
        {
          backgroundColor: colors.surfaceSecondary,
          borderColor: colors.border,
          borderRadius: radius.pill,
          paddingHorizontal: spacing[4],
        },
        style,
      ]}
    >
      <AppText variant="body" color="textMuted" style={styles.searchIcon}>
        ⌕
      </AppText>
      <TextInput
        style={[
          styles.input,
          {
            color: colors.textPrimary,
          },
        ]}
        value={value}
        onChangeText={onChangeText}
        onSubmitEditing={onSubmit}
        placeholder={placeholder}
        placeholderTextColor={colors.textMuted}
        returnKeyType="search"
        autoCapitalize="none"
        autoCorrect={false}
        autoFocus={autoFocus}
        accessibilityRole="search"
        accessibilityLabel="Search input"
      />
      {value.length > 0 && (
        <Pressable
          onPress={() => {
            onChangeText("");
            onClear?.();
          }}
          accessibilityRole="button"
          accessibilityLabel="Clear search input"
          style={styles.clearButton}
        >
          <AppText variant="caption" color="textMuted">
            ✕
          </AppText>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 48,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
  },
  searchIcon: {
    fontSize: 20,
    marginRight: 8,
  },
  input: {
    flex: 1,
    height: "100%",
    fontSize: 15,
  },
  clearButton: {
    padding: 6,
    justifyContent: "center",
    alignItems: "center",
  },
});
