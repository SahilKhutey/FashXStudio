import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { FeatureCompleteness } from '../types/profile.types';

interface ProfileCompletionCardProps {
  completeness: FeatureCompleteness | null;
}

const FEATURE_NAMES: Record<string, string> = {
  product_discovery: 'Product Discovery',
  personalized_recommendations: 'Personalized Recs',
  size_guidance: 'Size Guidance',
  fit_recommendation: 'Fit Match',
  advanced_vto: 'Virtual Try-On',
};

export const ProfileCompletionCard: React.FC<ProfileCompletionCardProps> = ({
  completeness,
}) => {
  if (!completeness) {
    return null;
  }

  const { overall_percentage, features } = completeness;

  return (
    <View style={styles.card}>
      <View style={styles.topRow}>
        <View>
          <Text style={styles.title}>Profile Readiness</Text>
          <Text style={styles.subtitle}>
            Complete your profile to unlock tailored size and style guidance
          </Text>
        </View>
        <View style={styles.pctBadge}>
          <Text style={styles.pctText}>{overall_percentage}%</Text>
        </View>
      </View>

      <View style={styles.progressBarBg}>
        <View
          style={[styles.progressBarFill, { width: `${Math.min(100, Math.max(0, overall_percentage))}%` }]}
        />
      </View>

      <View style={styles.featureGrid}>
        {Object.entries(features).map(([featKey, featStatus]) => {
          const isReady = featStatus.ready;
          const label = FEATURE_NAMES[featKey] || featKey;
          return (
            <View
              key={featKey}
              style={[styles.featurePill, isReady ? styles.pillReady : styles.pillPending]}
            >
              <Text style={[styles.pillIcon, isReady ? styles.iconReady : styles.iconPending]}>
                {isReady ? '✓' : '○'}
              </Text>
              <Text style={[styles.pillText, isReady ? styles.textReady : styles.textPending]}>
                {label}
              </Text>
            </View>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  subtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
    maxWidth: 240,
  },
  pctBadge: {
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 16,
  },
  pctText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#4F46E5',
  },
  progressBarBg: {
    height: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 4,
    marginVertical: 12,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#4F46E5',
    borderRadius: 4,
  },
  featureGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  featurePill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
  },
  pillReady: {
    backgroundColor: '#ECFDF5',
    borderColor: '#A7F3D0',
  },
  pillPending: {
    backgroundColor: '#F9FAFB',
    borderColor: '#E5E7EB',
  },
  pillIcon: {
    fontSize: 11,
    marginRight: 4,
  },
  iconReady: {
    color: '#059669',
    fontWeight: 'bold',
  },
  iconPending: {
    color: '#9CA3AF',
  },
  pillText: {
    fontSize: 11,
    fontWeight: '500',
  },
  textReady: {
    color: '#065F46',
  },
  textPending: {
    color: '#6B7280',
  },
});
