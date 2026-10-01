/**
 * FashXStudio — ListingTemplate Component (Phase 06 - Content Template)
 *
 * Architecture template for listing products, looks, and collections with
 * title, active filters, sorting, content grid, and pagination (Section 6.36).
 */

import React from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  spacingScale,
  typeScale,
} from '../../tokens/primitives';
import { lightSemanticContent } from '../../tokens/semantic';
import { FilterBar } from '../../components/FilterBar';
import { Grid } from '../../components/Grid';
import { Pagination } from '../../components/Pagination';
import type { VisualContent } from '../types';

export interface ListingTemplateProps {
  title: string;
  totalCount: number;
  items: VisualContent[];
  renderItem: (item: VisualContent) => React.ReactNode;
  activeChips?: { id: string; label: string }[];
  onRemoveChip?: (id: string) => void;
  onClearAllChips?: () => void;
  currentPage?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
  testID?: string;
}

export function ListingTemplate({
  title,
  totalCount,
  items,
  renderItem,
  activeChips = [],
  onRemoveChip,
  onClearAllChips,
  currentPage = 1,
  totalPages = 1,
  onPageChange,
  testID,
}: ListingTemplateProps) {
  return (
    <ScrollView style={styles.container} testID={testID}>
      {/* Page Header */}
      <View style={styles.header}>
        <Text style={styles.title}>{title}</Text>
        <Text style={styles.countText}>{totalCount} items</Text>
      </View>

      {/* Filter and Faceting Bar */}
      {activeChips.length > 0 && onRemoveChip && (
        <FilterBar
          activeChips={activeChips}
          onRemoveChip={onRemoveChip}
          onClearAll={onClearAllChips}
          filterCount={activeChips.length}
        />
      )}

      {/* Content Grid */}
      <View style={styles.gridSection}>
        <Grid columns={2} gutter={spacingScale.space3}>
          {items.map((item) => (
            <View key={item.id} style={styles.gridItem}>
              {renderItem(item)}
            </View>
          ))}
        </Grid>
      </View>

      {/* Pagination */}
      {totalPages > 1 && onPageChange && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={onPageChange}
        />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: spacingScale.space4,
    paddingTop: spacingScale.space3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: spacingScale.space3,
  },
  title: {
    fontSize: typeScale.headingL.fontSize,
    lineHeight: typeScale.headingL.lineHeight,
    fontWeight: '700',
    color: lightSemanticContent.primary,
  },
  countText: {
    fontSize: typeScale.caption.fontSize,
    color: lightSemanticContent.tertiary,
    fontWeight: '600',
  },
  gridSection: {
    marginVertical: spacingScale.space4,
  },
  gridItem: {
    marginBottom: spacingScale.space3,
  },
});
