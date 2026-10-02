/**
 * FashXStudio Master Visual Design Track Status Banner.
 * Phase 16: VD-16 — FINAL (Section 16.61).
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { VisualTrackStatusContract } from '../types';

export interface TrackStatusBannerProps {
  status: VisualTrackStatusContract;
}

export const TrackStatusBanner: React.FC<TrackStatusBannerProps> = ({ status }) => {
  return (
    <View
      style={styles.banner}
      accessible={true}
      accessibilityRole="summary"
      accessibilityLabel={`Visual Design Track 100% Complete: ${status.status_message}`}
    >
      <View style={styles.topRow}>
        <Text style={styles.badgeText}>VD-00 → VD-16</Text>
        <Text style={styles.percentageText}>100% SPECIFIED</Text>
      </View>
      <Text style={styles.title}>Visual Architecture Locked & Verified</Text>
      <Text style={styles.description}>{status.status_message}</Text>
      <View style={styles.progressContainer}>
        <View style={styles.progressBarBackground}>
          <View style={[styles.progressBarFill, { width: '100%' }]} />
        </View>
      </View>
      <View style={styles.statsRow}>
        <Text style={styles.statLabel}>Total Phases: {status.total_phases}</Text>
        <Text style={styles.statLabel}>Repo Implementation Ready</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  banner: {
    backgroundColor: '#111827',
    borderRadius: 12,
    padding: 20,
    marginVertical: 12,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#9CA3AF',
    letterSpacing: 1,
  },
  percentageText: {
    fontSize: 12,
    fontWeight: '800',
    color: '#10B981',
  },
  title: {
    fontSize: 18,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 6,
  },
  description: {
    fontSize: 13,
    color: '#D1D5DB',
    lineHeight: 18,
    marginBottom: 14,
  },
  progressContainer: {
    marginBottom: 12,
  },
  progressBarBackground: {
    height: 6,
    backgroundColor: '#374151',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: 6,
    backgroundColor: '#10B981',
    borderRadius: 3,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: '#9CA3AF',
    fontWeight: '500',
  },
});
