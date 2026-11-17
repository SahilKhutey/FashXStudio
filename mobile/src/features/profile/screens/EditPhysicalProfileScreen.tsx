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
import { HeightInput } from '../components/HeightInput';
import { WeightInput } from '../components/WeightInput';
import { FitPreferenceSelector } from '../components/FitPreferenceSelector';
import { SizeSystemSelector } from '../components/SizeSystemSelector';
import { PreferredFit, SizeSystem } from '../types/profile.types';

interface EditPhysicalProfileScreenProps {
  onSaved?: () => void;
  onCancel?: () => void;
}

export const EditPhysicalProfileScreen: React.FC<EditPhysicalProfileScreenProps> = ({
  onSaved,
  onCancel,
}) => {
  const { profile, updateProfile, isLoading } = useProfileStore();

  const [heightCm, setHeightCm] = useState<number | null>(profile?.height_cm ?? null);
  const [weightKg, setWeightKg] = useState<number | null>(profile?.weight_kg ?? null);
  const [fit, setFit] = useState<PreferredFit | null>(profile?.preferred_fit ?? null);
  const [sizeSystem, setSizeSystem] = useState<SizeSystem | null>(
    profile?.preferred_size_system ?? null,
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSave = async () => {
    setErrorMsg(null);
    if (heightCm !== null && (heightCm < 80 || heightCm > 250)) {
      setErrorMsg('Height must be between 80 cm and 250 cm.');
      return;
    }
    if (weightKg !== null && (weightKg < 20 || weightKg > 400)) {
      setErrorMsg('Weight must be between 20 kg and 400 kg.');
      return;
    }

    try {
      await updateProfile({
        height_cm: heightCm,
        weight_kg: weightKg,
        preferred_fit: fit,
        preferred_size_system: sizeSystem,
      });
      Alert.alert('Success', 'Physical profile updated.');
      onSaved?.();
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to save changes.');
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Physical Profile & Sizing</Text>
      <Text style={styles.subtext}>
        Accurate measurements help us recommend the right sizes across brands.
      </Text>

      {errorMsg ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{errorMsg}</Text>
        </View>
      ) : null}

      <HeightInput valueCm={heightCm} onChangeCm={setHeightCm} />
      <WeightInput valueKg={weightKg} onChangeKg={setWeightKg} />

      <FitPreferenceSelector selected={fit} onSelect={setFit} />
      <SizeSystemSelector selected={sizeSystem} onSelect={setSizeSystem} />

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
