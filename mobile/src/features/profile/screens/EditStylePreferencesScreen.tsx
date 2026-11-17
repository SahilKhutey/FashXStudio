import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from 'react-native';
import { useProfileStore } from '../store/profileStore';
import { StylePreferenceSelector } from '../components/StylePreferenceSelector';
import { ColorPreferenceSelector } from '../components/ColorPreferenceSelector';
import {
  ColorPreference,
  ProductCategory,
  StylePreference,
} from '../types/profile.types';

interface EditStylePreferencesScreenProps {
  onSaved?: () => void;
  onCancel?: () => void;
}

const CATEGORIES: { key: ProductCategory; label: string }[] = [
  { key: 'TOPS', label: 'Tops & Shirts' },
  { key: 'BOTTOMS', label: 'Bottoms & Trousers' },
  { key: 'DRESSES', label: 'Dresses & Jumpsuits' },
  { key: 'OUTERWEAR', label: 'Jackets & Coats' },
  { key: 'ACTIVEWEAR', label: 'Activewear' },
  { key: 'FORMALWEAR', label: 'Suits & Blazers' },
  { key: 'FOOTWEAR', label: 'Shoes & Footwear' },
  { key: 'ACCESSORIES', label: 'Bags & Accessories' },
  { key: 'TRADITIONAL', label: 'Kurtas & Ethnic' },
];

export const EditStylePreferencesScreen: React.FC<EditStylePreferencesScreenProps> = ({
  onSaved,
  onCancel,
}) => {
  const { profile, updateProfile, isLoading } = useProfileStore();

  const [stylesList, setStylesList] = useState<StylePreference[]>(
    profile?.style_preferences || [],
  );
  const [colorsList, setColorsList] = useState<ColorPreference[]>(
    profile?.preferred_colors || [],
  );
  const [categoriesList, setCategoriesList] = useState<ProductCategory[]>(
    profile?.product_categories || [],
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const toggleStyle = (item: StylePreference) => {
    if (stylesList.includes(item)) {
      setStylesList(stylesList.filter((s) => s !== item));
    } else {
      if (stylesList.length >= 5) return;
      setStylesList([...stylesList, item]);
    }
  };

  const toggleColor = (item: ColorPreference) => {
    if (colorsList.includes(item)) {
      setColorsList(colorsList.filter((c) => c !== item));
    } else {
      if (colorsList.length >= 6) return;
      setColorsList([...colorsList, item]);
    }
  };

  const toggleCategory = (item: ProductCategory) => {
    if (categoriesList.includes(item)) {
      setCategoriesList(categoriesList.filter((c) => c !== item));
    } else {
      setCategoriesList([...categoriesList, item]);
    }
  };

  const handleSave = async () => {
    setErrorMsg(null);
    try {
      await updateProfile({
        style_preferences: stylesList,
        preferred_colors: colorsList,
        product_categories: categoriesList,
      });
      Alert.alert('Success', 'Style preferences updated.');
      onSaved?.();
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to save changes.');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Style & Aesthetic</Text>
      <Text style={styles.subtext}>
        Tell us what aesthetic and palettes match your taste for personalized recommendations.
      </Text>

      {errorMsg ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{errorMsg}</Text>
        </View>
      ) : null}

      <StylePreferenceSelector
        selected={stylesList}
        onToggle={toggleStyle}
        maxSelection={5}
      />

      <ColorPreferenceSelector
        selected={colorsList}
        onToggle={toggleColor}
        maxSelection={6}
      />

      <View style={styles.sectionWrap}>
        <Text style={styles.sectionLabel}>Preferred Categories</Text>
        <View style={styles.chipWrap}>
          {CATEGORIES.map((cat) => {
            const isSelected = categoriesList.includes(cat.key);
            return (
              <TouchableOpacity
                key={cat.key}
                style={[styles.catChip, isSelected && styles.catChipSelected]}
                onPress={() => toggleCategory(cat.key)}
              >
                <Text style={[styles.catText, isSelected && styles.catTextSelected]}>
                  {isSelected ? '✓ ' : '+ '}
                  {cat.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      <View style={styles.buttonRow}>
        {onCancel && (
          <TouchableOpacity
            style={styles.cancelButton}
            onPress={onCancel}
            disabled={isLoading}
          >
            <Text style={styles.cancelText}>Cancel</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={styles.saveButton}
          onPress={handleSave}
          disabled={isLoading}
        >
          {isLoading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <Text style={styles.saveText}>Save Changes</Text>
          )}
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  subtext: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 4,
    marginBottom: 16,
  },
  errorBox: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#F87171',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: '#B91C1C',
    fontSize: 13,
  },
  sectionWrap: {
    marginVertical: 12,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 8,
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  catChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  catChipSelected: {
    backgroundColor: '#EEF2FF',
    borderColor: '#4F46E5',
  },
  catText: {
    fontSize: 13,
    color: '#374151',
    fontWeight: '500',
  },
  catTextSelected: {
    color: '#4F46E5',
    fontWeight: '700',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  cancelButton: {
    flex: 1,
    height: 48,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  cancelText: {
    color: '#374151',
    fontSize: 15,
    fontWeight: '600',
  },
  saveButton: {
    flex: 2,
    height: 48,
    borderRadius: 8,
    backgroundColor: '#4F46E5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  saveText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
});
