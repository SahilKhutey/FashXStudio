/**
 * SearchInputBar Component — Phase 08 (Section 8.17).
 *
 * Dedicated search field supporting query typing, clear trigger,
 * submit action, loading spinner, and keyboard navigation.
 */

import React from "react";
import { StyleSheet, TextInput, TouchableOpacity, View } from "react-native";
import { defaultDesignTokens } from "../../tokens";
import { Icon } from "../../components/Icon";

export interface SearchInputBarProps {
  query: string;
  placeholder?: string;
  onChangeQuery: (text: string) => void;
  onSubmitQuery?: (text: string) => void;
  onClearQuery?: () => void;
  isLoading?: boolean;
}

export const SearchInputBar: React.FC<SearchInputBarProps> = ({
  query,
  placeholder = "Search fashion, styles, products...",
  onChangeQuery,
  onSubmitQuery,
  onClearQuery,
  isLoading,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.searchIcon}>
        <Icon name="search" size={18} color={defaultDesignTokens.neutral.neutral400} />
      </View>

      <TextInput
        value={query}
        placeholder={placeholder}
        placeholderTextColor={defaultDesignTokens.neutral.neutral400}
        style={styles.input}
        returnKeyType="search"
        autoCapitalize="none"
        autoCorrect={false}
        onChangeText={onChangeQuery}
        onSubmitEditing={() => onSubmitQuery?.(query)}
      />

      {query.length > 0 ? (
        <TouchableOpacity
          accessibilityLabel="Clear search input"
          onPress={onClearQuery}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          style={styles.clearButton}
        >
          <Icon name="x" size={16} color={defaultDesignTokens.neutral.neutral500} />
        </TouchableOpacity>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    height: 48,
    borderRadius: 24,
    backgroundColor: defaultDesignTokens.neutral.neutral100,
    borderWidth: 1.5,
    borderColor: defaultDesignTokens.neutral.neutral200,
    paddingHorizontal: 14,
    gap: 8,
  },
  searchIcon: {
    justifyContent: "center",
    alignItems: "center",
  },
  input: {
    flex: 1,
    fontSize: 15,
    color: defaultDesignTokens.neutral.neutral900,
    height: "100%",
  },
  clearButton: {
    padding: 4,
    justifyContent: "center",
    alignItems: "center",
  },
});
