/**
 * FashXStudio Master Visual Quality Checklist Viewer.
 * Phase 16: VD-16 — FINAL (Section 16.57).
 */

import React from 'react';
import { View, Text, StyleSheet, FlatList } from 'react-native';
import type { VisualChecklistItemContract } from '../types';

export interface ChecklistViewerProps {
  items: VisualChecklistItemContract[];
  categoryFilter?: string;
}

export const ChecklistViewer: React.FC<ChecklistViewerProps> = ({ items, categoryFilter }) => {
  const filtered = categoryFilter
    ? items.filter((item) => item.category === categoryFilter)
    : items;

  return (
    <View style={styles.container} accessible={true} accessibilityRole="list">
      <Text style={styles.title}>Visual Quality Checklist ({filtered.length} Items)</Text>
      <FlatList
        data={filtered}
        keyExtractor={(item) => item.item_id}
        renderItem={({ item }) => (
          <View
            style={styles.itemRow}
            accessible={true}
            accessibilityRole="checkbox"
            accessibilityState={{ checked: item.is_verified }}
            accessibilityLabel={`${item.title}: ${item.is_verified ? 'Verified' : 'Unverified'}`}
          >
            <View style={[styles.checkbox, item.is_verified && styles.checkboxChecked]}>
              <Text style={styles.checkmark}>{item.is_verified ? '✓' : ''}</Text>
            </View>
            <View style={styles.textContainer}>
              <View style={styles.metaRow}>
                <Text style={styles.itemTitle}>{item.title}</Text>
                <Text style={styles.categoryBadge}>{item.category.toUpperCase()}</Text>
              </View>
              <Text style={styles.itemDesc}>{item.description}</Text>
            </View>
          </View>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 16,
    marginVertical: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  checkboxChecked: {
    backgroundColor: '#059669',
    borderColor: '#059669',
  },
  checkmark: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  textContainer: {
    flex: 1,
  },
  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  itemTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  categoryBadge: {
    fontSize: 10,
    fontWeight: '700',
    color: '#6B7280',
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  itemDesc: {
    fontSize: 12,
    color: '#6B7280',
    lineHeight: 16,
  },
});
