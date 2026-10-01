/**
 * FashXStudio — Pagination Component (Phase 05 - L2 Core UI)
 *
 * Accessible page navigation control supporting numbered pages,
 * previous/next triggers, and current-page indication (Section 5.43).
 */

import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {
  neutralPrimitives,
  radiusScale,
  spacingScale,
  typeScale,
} from '../tokens/primitives';
import {
  lightSemanticActions,
  lightSemanticBorders,
  lightSemanticContent,
  lightSemanticSurfaces,
} from '../tokens/semantic';
import type { PaginationProps } from './types';

export function Pagination({
  currentPage,
  totalPages,
  onPageChange,
  showPrevNext = true,
  testID,
}: PaginationProps) {
  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  // Render a window of page numbers around current
  const getPageNumbers = () => {
    const pages = [];
    const start = Math.max(1, currentPage - 1);
    const end = Math.min(totalPages, currentPage + 1);

    for (let p = start; p <= end; p++) {
      pages.push(p);
    }
    return pages;
  };

  const pages = getPageNumbers();

  return (
    <View
      style={styles.container}
      accessibilityRole="navigation"
      accessibilityLabel="Pagination"
      testID={testID}
    >
      {showPrevNext && (
        <Pressable
          onPress={() => canGoPrev && onPageChange(currentPage - 1)}
          disabled={!canGoPrev}
          style={[styles.button, !canGoPrev && styles.buttonDisabled]}
          accessibilityRole="button"
          accessibilityLabel="Previous page"
        >
          <Text style={[styles.arrow, !canGoPrev && styles.textDisabled]}>←</Text>
        </Pressable>
      )}

      {pages.map((pageNum) => {
        const isCurrent = pageNum === currentPage;
        return (
          <Pressable
            key={pageNum}
            onPress={() => onPageChange(pageNum)}
            style={[
              styles.pageButton,
              isCurrent ? styles.pageCurrent : styles.pageNormal,
            ]}
            accessibilityRole="button"
            accessibilityState={{ selected: isCurrent }}
            accessibilityLabel={`Page ${pageNum}${isCurrent ? ', current page' : ''}`}
          >
            <Text
              style={[
                styles.pageText,
                isCurrent ? styles.textCurrent : styles.textNormal,
              ]}
            >
              {pageNum}
            </Text>
          </Pressable>
        );
      })}

      {showPrevNext && (
        <Pressable
          onPress={() => canGoNext && onPageChange(currentPage + 1)}
          disabled={!canGoNext}
          style={[styles.button, !canGoNext && styles.buttonDisabled]}
          accessibilityRole="button"
          accessibilityLabel="Next page"
        >
          <Text style={[styles.arrow, !canGoNext && styles.textDisabled]}>→</Text>
        </Pressable>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacingScale.space2,
    marginVertical: spacingScale.space4,
  },
  button: {
    minWidth: 44,
    minHeight: 44,
    borderWidth: 1,
    borderColor: lightSemanticBorders.default,
    borderRadius: radiusScale.sm,
    backgroundColor: lightSemanticSurfaces.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonDisabled: {
    opacity: 0.35,
  },
  arrow: {
    fontSize: 16,
    color: lightSemanticContent.primary,
    fontWeight: '700',
  },
  pageButton: {
    minWidth: 44,
    minHeight: 44,
    borderRadius: radiusScale.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  pageNormal: {
    backgroundColor: lightSemanticSurfaces.secondary,
  },
  pageCurrent: {
    backgroundColor: lightSemanticActions.primary,
  },
  pageText: {
    fontSize: typeScale.labelM.fontSize,
  },
  textNormal: {
    color: lightSemanticContent.primary,
    fontWeight: '500',
  },
  textCurrent: {
    color: neutralPrimitives.neutral0,
    fontWeight: '700',
  },
  textDisabled: {
    color: neutralPrimitives.neutral400,
  },
});
