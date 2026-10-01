/**
 * FashXStudio — SearchBar Component (Phase 05 - L3 Composite)
 *
 * Composed search bar component providing input trigger, clear button,
 * and optional filter button integration (Section 5.47 & 5.50).
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  neutralPrimitives,
  radiusScale,
  spacingScale,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { SearchBarProps } from './types';

export function SearchBar({
  placeholder = 'Search products, styles, trends…',
  value,
  onChangeText,
  onSubmit,
  onFilterPress,
  showFilterButton = true,
  testID,
}: SearchBarProps) {
  return (
    <View style={styles.container} testID={testID}>
      <View style={styles.inputWrapper}>
        <Text style={styles.searchIcon}>🔍</Text>
        <TextInput
          value={value}
          onChangeText={onChangeText}
          onSubmitEditing={onSubmit}
          placeholder={placeholder}
          placeholderTextColor={lightSemanticContent.tertiary}
          returnKeyType="search"
          style={styles.input}
          accessibilityRole="search"
          accessibilityLabel="Search input"
        />
        {value && value.length > 0 && (
          <Pressable
            onPress={() => onChangeText && onChangeText('')}
            style={styles.clearButton}
            accessibilityRole="button"
            accessibilityLabel="Clear search input"
          >
            <Text style={styles.clearIcon}>✕</Text>
          </Pressable>
        )}
      </View>

      {showFilterButton && onFilterPress && (
        <Pressable
          onPress={onFilterPress}
          style={styles.filterButton}
          accessibilityRole="button"
          accessibilityLabel="Open filters"
        >
          <Text style={styles.filterIcon}>⚙️</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacingScale.space2,
    width: '100%',
  },
  inputWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: lightSemanticSurfaces.secondary,
    borderWidth: 1,
    borderColor: lightSemanticBorders.default,
    borderRadius: radiusScale.sm,
    paddingHorizontal: spacingScale.space3,
    minHeight: 44, // WCAG touch target
  },
  searchIcon: {
    fontSize: 16,
    marginRight: spacingScale.space2,
    color: lightSemanticContent.tertiary,
  },
  input: {
    flex: 1,
    height: '100%',
    fontSize: typeScale.bodyM.fontSize,
    color: lightSemanticContent.primary,
  },
  clearButton: {
    minWidth: 32,
    minHeight: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clearIcon: {
    fontSize: 12,
    color: lightSemanticContent.tertiary,
    fontWeight: '700',
  },
  filterButton: {
    minWidth: 44,
    minHeight: 44,
    borderWidth: 1,
    borderColor: lightSemanticBorders.default,
    borderRadius: radiusScale.sm,
    backgroundColor: lightSemanticSurfaces.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  filterIcon: {
    fontSize: 18,
  },
});
