import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { SizeSystem } from '../types/profile.types';

interface SizeSystemSelectorProps {
  selected?: SizeSystem | null;
  onSelect: (system: SizeSystem) => void;
}

const SYSTEMS: { key: SizeSystem; label: string; desc: string }[] = [
  { key: 'IN', label: 'India (IN)', desc: 'Standard sizing for Indian brands' },
  { key: 'US', label: 'US', desc: 'United States sizing standard' },
  { key: 'UK', label: 'UK', desc: 'United Kingdom sizing standard' },
  { key: 'EU', label: 'EU', desc: 'European sizing standard' },
  { key: 'INTL', label: 'International', desc: 'XS / S / M / L / XL sizing' },
];

export const SizeSystemSelector: React.FC<SizeSystemSelectorProps> = ({
  selected,
  onSelect,
}) => {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>Preferred Size System</Text>
      <View style={styles.optionsList}>
        {SYSTEMS.map((sys) => {
          const isSelected = selected === sys.key;
          return (
            <TouchableOpacity
              key={sys.key}
              style={[styles.optionCard, isSelected && styles.optionCardSelected]}
              onPress={() => onSelect(sys.key)}
            >
              <View style={styles.radioOuter}>
                {isSelected && <View style={styles.radioInner} />}
              </View>
              <View style={styles.textContainer}>
                <Text style={[styles.title, isSelected && styles.titleSelected]}>
                  {sys.label}
                </Text>
                <Text style={styles.desc}>{sys.desc}</Text>
              </View>
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
  optionsList: {
    gap: 8,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    backgroundColor: '#FFFFFF',
  },
  optionCardSelected: {
    borderColor: '#4F46E5',
    backgroundColor: '#EEF2FF',
  },
  radioOuter: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#9CA3AF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#4F46E5',
  },
  textContainer: {
    flex: 1,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  titleSelected: {
    color: '#4F46E5',
  },
  desc: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
});
