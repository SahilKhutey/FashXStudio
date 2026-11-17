import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';

interface WeightInputProps {
  valueKg?: number | null;
  onChangeKg: (kg: number | null) => void;
  error?: string;
}

export const WeightInput: React.FC<WeightInputProps> = ({
  valueKg,
  onChangeKg,
  error,
}) => {
  const [unit, setUnit] = useState<'kg' | 'lbs'>('kg');
  const [kgText, setKgText] = useState<string>(valueKg ? String(valueKg) : '');
  const [lbsText, setLbsText] = useState<string>('');

  useEffect(() => {
    if (valueKg != null && !isNaN(valueKg)) {
      setKgText(String(valueKg));
      const lbs = Math.round((valueKg / 0.45359237) * 10) / 10;
      setLbsText(String(lbs));
    } else {
      setKgText('');
      setLbsText('');
    }
  }, [valueKg]);

  const handleKgChange = (text: string) => {
    setKgText(text);
    const parsed = parseFloat(text);
    if (!text.trim()) {
      onChangeKg(null);
    } else if (!isNaN(parsed)) {
      onChangeKg(Math.round(parsed * 10) / 10);
    }
  };

  const handleLbsChange = (text: string) => {
    setLbsText(text);
    const parsed = parseFloat(text);
    if (!text.trim()) {
      onChangeKg(null);
    } else if (!isNaN(parsed)) {
      const kg = Math.round((parsed * 0.45359237) * 10) / 10;
      onChangeKg(kg);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.label}>Weight (Optional)</Text>
        <View style={styles.toggleRow}>
          <TouchableOpacity
            style={[styles.unitButton, unit === 'kg' && styles.unitButtonActive]}
            onPress={() => setUnit('kg')}
          >
            <Text style={[styles.unitText, unit === 'kg' && styles.unitTextActive]}>kg</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.unitButton, unit === 'lbs' && styles.unitButtonActive]}
            onPress={() => setUnit('lbs')}
          >
            <Text style={[styles.unitText, unit === 'lbs' && styles.unitTextActive]}>lbs</Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.inputRow}>
        {unit === 'kg' ? (
          <>
            <TextInput
              style={[styles.input, error ? styles.inputError : null]}
              placeholder="e.g. 70"
              keyboardType="decimal-pad"
              value={kgText}
              onChangeText={handleKgChange}
            />
            <Text style={styles.suffix}>kg</Text>
          </>
        ) : (
          <>
            <TextInput
              style={[styles.input, error ? styles.inputError : null]}
              placeholder="e.g. 154"
              keyboardType="decimal-pad"
              value={lbsText}
              onChangeText={handleLbsChange}
            />
            <Text style={styles.suffix}>lbs</Text>
          </>
        )}
      </View>

      {error ? <Text style={styles.errorText}>{error}</Text> : null}
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
    marginBottom: 6,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },
  toggleRow: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    borderRadius: 6,
    padding: 2,
  },
  unitButton: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 4,
  },
  unitButtonActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  unitText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  unitTextActive: {
    color: '#111827',
    fontWeight: '700',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    height: 44,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    color: '#111827',
    backgroundColor: '#FFFFFF',
  },
  suffix: {
    marginLeft: 8,
    fontSize: 14,
    color: '#4B5563',
  },
  inputError: {
    borderColor: '#EF4444',
  },
  errorText: {
    marginTop: 4,
    fontSize: 12,
    color: '#EF4444',
  },
});
