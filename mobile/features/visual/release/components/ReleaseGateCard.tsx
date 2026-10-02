/**
 * FashXStudio Release Gate Card Component.
 * Phase 16: VD-16 — FINAL.
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { ReleaseGateResultContract } from '../types';

export interface ReleaseGateCardProps {
  gate: ReleaseGateResultContract;
}

export const ReleaseGateCard: React.FC<ReleaseGateCardProps> = ({ gate }) => {
  const isPassed = gate.passed;
  const statusColor = isPassed ? '#059669' : '#DC2626';
  const statusBg = isPassed ? '#ECFDF5' : '#FEF2F2';

  return (
    <View
      style={[styles.container, { borderLeftColor: statusColor }]}
      accessible={true}
      accessibilityRole="summary"
      accessibilityLabel={`Release Gate ${gate.gate_name}: ${gate.status}, score ${gate.score}%`}
    >
      <View style={styles.headerRow}>
        <Text style={styles.gateName}>{gate.gate_name.toUpperCase()} GATE</Text>
        <View style={[styles.badge, { backgroundColor: statusBg }]}>
          <Text style={[styles.badgeText, { color: statusColor }]}>{gate.status.toUpperCase()}</Text>
        </View>
      </View>
      <View style={styles.scoreRow}>
        <Text style={styles.scoreLabel}>Compliance Score:</Text>
        <Text style={[styles.scoreValue, { color: statusColor }]}>{gate.score.toFixed(1)}%</Text>
      </View>
      {gate.violations.length > 0 && (
        <View style={styles.violationsContainer}>
          <Text style={styles.violationsTitle}>Violations Detected:</Text>
          {gate.violations.map((v, i) => (
            <Text key={i} style={styles.violationText}>
              • {v}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    borderLeftWidth: 4,
    padding: 16,
    marginVertical: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  gateName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
    letterSpacing: 0.5,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  scoreLabel: {
    fontSize: 13,
    color: '#6B7280',
  },
  scoreValue: {
    fontSize: 15,
    fontWeight: '700',
  },
  violationsContainer: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  violationsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: '#DC2626',
    marginBottom: 4,
  },
  violationText: {
    fontSize: 12,
    color: '#4B5563',
    lineHeight: 16,
  },
});
