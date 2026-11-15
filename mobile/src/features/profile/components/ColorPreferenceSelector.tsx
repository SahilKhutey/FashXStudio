import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { ColorPreference } from '../types/profile.types';

interface ColorPreferenceSelectorProps {
  selected: ColorPreference[];
  onToggle: (color: ColorPreference) => void;
  maxSelection?: number;
}

const COLORS: { key: ColorPreference; label: string; hex: string; border?: boolean }[] = [
  { key: 'BLACK', label: 'Black', hex: '#111827' },
  { key: 'WHITE', label: 'White', hex: '#FFFFFF', border: true },
  { key: 'NAVY', label: 'Navy', hex: '#1E3A8A' },
  { key: 'GREY', label: 'Grey', hex: '#6B7280' },
  { key: 'BEIGE', label: 'Beige', hex: '#F5F5DC', border: true },
  { key: 'BROWN', label: 'Brown', hex: '#78350F' },
  { key: 'RED', label: 'Red', hex: '#DC2626' },
  { key: 'BLUE', label: 'Blue', hex: '#2563EB' },
  { key: 'GREEN', label: 'Green', hex: '#16A34A' },
  { key: 'YELLOW', label: 'Yellow', hex: '#FACC15' },
  { key: 'PINK', label: 'Pink', hex: '#EC4899' },
  { key: 'PURPLE', label: 'Purple', hex: '#9333EA' },
  { key: 'ORANGE', label: 'Orange', hex: '#EA580C' },
  { key: 'PASTELS', label: 'Pastels', hex: '#FDE68A' },
  { key: 'EARTH_TONES', label: 'Earth Tones', hex: '#A16207' },
  { key: 'JEWEL_TONES', label: 'Jewel Tones', hex: '#0D9488' },
];

export const ColorPreferenceSelector: React.FC<ColorPreferenceSelectorProps> = ({
  selected,
  onToggle,
  maxSelection = 6,
}) => {
  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.label}>Preferred Colors</Text>
        <Text style={styles.counter}>
          {selected.length}/{maxSelection} selected
        </Text>
      </View>
      <View style={styles.grid}>
        {COLORS.map((col) => {
          const isSelected = selected.includes(col.key);
          return (
            <TouchableOpacity
              key={col.key}
              style={[styles.item, isSelected && styles.itemSelected]}
              onPress={() => onToggle(col.key)}
            >
              <View
                style={[
                  styles.colorDot,
                  { backgroundColor: col.hex },
                  col.border && styles.dotBorder,
                ]}
              />
              <Text style={[styles.itemText, isSelected && styles.itemTextSelected]}>
                {col.label}
              </Text>
              {isSelected && <Text style={styles.checkMark}>✓</Text>}
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
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 16,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  itemSelected: {
    backgroundColor: '#EEF2FF',
    borderColor: '#4F46E5',
  },
  colorDot: {
    width: 14,
    height: 14,
    borderRadius: 7,
    marginRight: 6,
  },
  dotBorder: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  itemText: {
    fontSize: 13,
    color: '#374151',
    fontWeight: '500',
  },
  itemTextSelected: {
    color: '#4F46E5',
    fontWeight: '700',
  },
  checkMark: {
    marginLeft: 4,
    fontSize: 12,
    color: '#4F46E5',
    fontWeight: 'bold',
  },
});
