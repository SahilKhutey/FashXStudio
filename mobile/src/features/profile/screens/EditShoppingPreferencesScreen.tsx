import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
  Switch,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from 'react-native';
import { useProfileStore } from '../store/profileStore';
import {
  ShoppingIntent,
  ShoppingPreferences,
} from '../types/profile.types';

interface EditShoppingPreferencesScreenProps {
  onSaved?: () => void;
  onCancel?: () => void;
}

const INTENTS: { key: ShoppingIntent; label: string }[] = [
  { key: 'EVERYDAY', label: 'Everyday Wear' },
  { key: 'WORK', label: 'Work & Office' },
  { key: 'SPECIAL_OCCASION', label: 'Special Occasions' },
  { key: 'VACATION', label: 'Vacation & Travel' },
  { key: 'LOUNGE', label: 'Loungewear' },
  { key: 'FITNESS', label: 'Workout & Fitness' },
];

export const EditShoppingPreferencesScreen: React.FC<EditShoppingPreferencesScreenProps> = ({
  onSaved,
  onCancel,
}) => {
  const { profile, updateProfile, isLoading } = useProfileStore();

  const currentPrefs = profile?.shopping_preferences || {};
  const [budgetMin, setBudgetMin] = useState<string>(
    currentPrefs.budget?.min != null ? String(currentPrefs.budget.min) : '',
  );
  const [budgetMax, setBudgetMax] = useState<string>(
    currentPrefs.budget?.max != null ? String(currentPrefs.budget.max) : '',
  );
  const [intents, setIntents] = useState<ShoppingIntent[]>(
    currentPrefs.shopping_intents || [],
  );
  const [brandsText, setBrandsText] = useState<string>(
    (currentPrefs.preferred_brands || []).join(', '),
  );
  const [avoidMaterialsText, setAvoidMaterialsText] = useState<string>(
    (currentPrefs.avoid_materials || []).join(', '),
  );
  const [sustainability, setSustainability] = useState<boolean>(
    Boolean(currentPrefs.sustainability_preference),
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const toggleIntent = (intent: ShoppingIntent) => {
    if (intents.includes(intent)) {
      setIntents(intents.filter((i) => i !== intent));
    } else {
      setIntents([...intents, intent]);
    }
  };

  const handleSave = async () => {
    setErrorMsg(null);
    const parsedMin = budgetMin.trim() ? parseFloat(budgetMin) : null;
    const parsedMax = budgetMax.trim() ? parseFloat(budgetMax) : null;

    if (parsedMin !== null && parsedMin < 0) {
      setErrorMsg('Minimum budget must be non-negative.');
      return;
    }
    if (parsedMax !== null && parsedMax < 0) {
      setErrorMsg('Maximum budget must be non-negative.');
      return;
    }
    if (parsedMin !== null && parsedMax !== null && parsedMin > parsedMax) {
      setErrorMsg('Minimum budget cannot exceed maximum budget.');
      return;
    }

    const brands = brandsText
      .split(',')
      .map((b) => b.trim())
      .filter(Boolean);

    const avoidMaterials = avoidMaterialsText
      .split(',')
      .map((m) => m.trim())
      .filter(Boolean);

    const shoppingPrefs: ShoppingPreferences = {
      budget: {
        min: parsedMin,
        max: parsedMax,
        currency: 'INR',
      },
      shopping_intents: intents,
      preferred_brands: brands,
      avoid_materials: avoidMaterials,
      sustainability_preference: sustainability,
    };

    try {
      await updateProfile({
        shopping_preferences: shoppingPrefs,
      });
      Alert.alert('Success', 'Shopping preferences updated.');
      onSaved?.();
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to save changes.');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Shopping & Budget</Text>
      <Text style={styles.subtext}>
        Customize price ranges, occasions, and brands to refine catalog recommendations.
      </Text>

      {errorMsg ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{errorMsg}</Text>
        </View>
      ) : null}

      <View style={styles.sectionWrap}>
        <Text style={styles.sectionLabel}>Budget Range (₹ INR)</Text>
        <View style={styles.budgetRow}>
          <View style={styles.budgetCol}>
            <Text style={styles.inputLabel}>Min Price (₹)</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. 500"
              keyboardType="number-pad"
              value={budgetMin}
              onChangeText={setBudgetMin}
            />
          </View>
          <Text style={styles.dash}>—</Text>
          <View style={styles.budgetCol}>
            <Text style={styles.inputLabel}>Max Price (₹)</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g. 5000"
              keyboardType="number-pad"
              value={budgetMax}
              onChangeText={setBudgetMax}
            />
          </View>
        </View>
      </View>

      <View style={styles.sectionWrap}>
        <Text style={styles.sectionLabel}>Shopping Occasions / Intents</Text>
        <View style={styles.chipWrap}>
          {INTENTS.map((item) => {
            const isSelected = intents.includes(item.key);
            return (
              <TouchableOpacity
                key={item.key}
                style={[styles.intentChip, isSelected && styles.intentChipSelected]}
                onPress={() => toggleIntent(item.key)}
              >
                <Text style={[styles.intentText, isSelected && styles.intentTextSelected]}>
                  {isSelected ? '✓ ' : '+ '}
                  {item.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      <View style={styles.sectionWrap}>
        <Text style={styles.sectionLabel}>Preferred Brands (comma-separated)</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. Zara, H&M, FabIndia, Nike"
          value={brandsText}
          onChangeText={setBrandsText}
        />
      </View>

      <View style={styles.sectionWrap}>
        <Text style={styles.sectionLabel}>Materials to Avoid</Text>
        <TextInput
          style={styles.input}
          placeholder="e.g. Polyester, Wool, Silk"
          value={avoidMaterialsText}
          onChangeText={setAvoidMaterialsText}
        />
      </View>

      <View style={styles.switchRow}>
        <View style={styles.switchTextCol}>
          <Text style={styles.switchLabel}>Sustainability Preference</Text>
          <Text style={styles.switchSub}>
            Highlight eco-friendly, organic, and ethical fashion brands.
          </Text>
        </View>
        <Switch
          value={sustainability}
          onValueChange={setSustainability}
          trackColor={{ false: '#D1D5DB', true: '#A7F3D0' }}
          thumbColor={sustainability ? '#059669' : '#F4F3F4'}
        />
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
    marginVertical: 10,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 6,
  },
  inputLabel: {
    fontSize: 12,
    color: '#4B5563',
    marginBottom: 4,
  },
  budgetRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  budgetCol: {
    flex: 1,
  },
  dash: {
    fontSize: 18,
    color: '#9CA3AF',
    marginTop: 14,
  },
  input: {
    height: 44,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 15,
    backgroundColor: '#FFFFFF',
    color: '#111827',
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  intentChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  intentChipSelected: {
    backgroundColor: '#EEF2FF',
    borderColor: '#4F46E5',
  },
  intentText: {
    fontSize: 13,
    color: '#374151',
    fontWeight: '500',
  },
  intentTextSelected: {
    color: '#4F46E5',
    fontWeight: '700',
  },
  switchRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginVertical: 16,
    padding: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  switchTextCol: {
    flex: 1,
    marginRight: 12,
  },
  switchLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  switchSub: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
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
