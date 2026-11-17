import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { PreferredFit } from '../types/profile.types';

interface FitPreferenceSelectorProps {
  selected?: PreferredFit | null;
  onSelect: (fit: PreferredFit) => void;
}

const FITS: { key: PreferredFit; label: string; desc: string }[] = [
  { key: 'SLIM', label: 'Slim Fit', desc: 'Close-fitting contour' },
  { key: 'REGULAR', label: 'Regular Fit', desc: 'Classic comfortable cut' },
  { key: 'RELAXED', label: 'Relaxed Fit', desc: 'Loose and breezy silhouette' },
  { key: 'OVERSIZED', label: 'Oversized', desc: 'Roomy contemporary street drape' },
  { key: 'NO_PREFERENCE', label: 'No Preference', desc: 'Open to all fit profiles' },
];

export const FitPreferenceSelector: React.FC<FitPreferenceSelectorProps> = ({
  selected,
  onSelect,
}) => {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>Preferred Fit</Text>
      <View style={styles.grid}>
        {FITS.map((item) => {
          const isSelected = selected === item.key;
          return (
            <TouchableOpacity
              key={item.key}
              style={[styles.chip, isSelected && styles.chipSelected]}
              onPress={() => onSelect(item.key)}
            >
              <Text style={[styles.chipLabel, isSelected && styles.chipLabelSelected]}>
                {item.label}
              </Text>
              <Text style={styles.chipDesc}>{item.desc}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  grid: {
    gap: 8,
  },
  chip: {
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
  },
  chipSelected: {
    borderColor: '#4F46E5',
    backgroundColor: '#EEF2FF',
  },
  chipLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  chipLabelSelected: {
    color: '#4F46E5',
  },
  chipDesc: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
});
