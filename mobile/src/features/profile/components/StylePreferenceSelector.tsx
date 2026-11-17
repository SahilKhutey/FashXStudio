import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { StylePreference } from '../types/profile.types';

interface StylePreferenceSelectorProps {
  selected: StylePreference[];
  onToggle: (style: StylePreference) => void;
  maxSelection?: number;
}

const STYLES: { key: StylePreference; label: string }[] = [
  { key: 'CASUAL', label: 'Casual' },
  { key: 'FORMAL', label: 'Formal' },
  { key: 'STREETWEAR', label: 'Streetwear' },
  { key: 'BOHEMIAN', label: 'Bohemian' },
  { key: 'MINIMALIST', label: 'Minimalist' },
  { key: 'VINTAGE', label: 'Vintage' },
  { key: 'ATHLEISURE', label: 'Athleisure' },
  { key: 'BUSINESS_CASUAL', label: 'Business Casual' },
  { key: 'ETHNIC', label: 'Ethnic / Traditional' },
  { key: 'PARTYWEAR', label: 'Partywear' },
];

export const StylePreferenceSelector: React.FC<StylePreferenceSelectorProps> = ({
  selected,
  onToggle,
  maxSelection = 5,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.label}>Style Preferences</Text>
        <Text style={styles.counter}>
          {selected.length}/{maxSelection} selected
        </Text>
      </View>
      <View style={styles.chipWrap}>
        {STYLES.map((st) => {
          const isSelected = selected.includes(st.key);
          return (
            <TouchableOpacity
              key={st.key}
              style={[styles.chip, isSelected && styles.chipSelected]}
              onPress={() => onToggle(st.key)}
            >
              <Text style={[styles.chipText, isSelected && styles.chipTextSelected]}>
                {isSelected ? '✓ ' : '+ '}
                {st.label}
              </Text>
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  counter: {
    fontSize: 12,
    color: '#6B7280',
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  chipSelected: {
    backgroundColor: '#EEF2FF',
    borderColor: '#4F46E5',
  },
  chipText: {
    fontSize: 13,
    color: '#374151',
    fontWeight: '500',
  },
  chipTextSelected: {
    color: '#4F46E5',
    fontWeight: '700',
  },
});
