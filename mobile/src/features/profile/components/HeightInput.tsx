import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet } from 'react-native';

interface HeightInputProps {
  valueCm?: number | null;
  onChangeCm: (cm: number | null) => void;
  error?: string;
}

export const HeightInput: React.FC<HeightInputProps> = ({
  valueCm,
  onChangeCm,
  error,
}) => {
  const [unit, setUnit] = useState<'cm' | 'ft_in'>('cm');
  const [cmText, setCmText] = useState<string>(valueCm ? String(valueCm) : '');
  const [feetText, setFeetText] = useState<string>('');
  const [inchesText, setInchesText] = useState<string>('');

  useEffect(() => {
    if (valueCm != null && !isNaN(valueCm)) {
      setCmText(String(valueCm));
      const totalInches = valueCm / 2.54;
      const ft = Math.floor(totalInches / 12);
      const inc = Math.round((totalInches % 12) * 10) / 10;
      setFeetText(String(ft));
      setInchesText(String(inc));
    } else {
      setCmText('');
      setFeetText('');
      setInchesText('');
    }
  }, [valueCm]);

  const handleCmChange = (text: string) => {
    setCmText(text);
    const parsed = parseFloat(text);
    if (!text.trim()) {
      onChangeCm(null);
    } else if (!isNaN(parsed)) {
      onChangeCm(Math.round(parsed * 10) / 10);
    }
  };

  const handleFtInChange = (newFt: string, newIn: string) => {
    setFeetText(newFt);
    setInchesText(newIn);
    const ft = parseFloat(newFt) || 0;
    const inc = parseFloat(newIn) || 0;
    if (!newFt.trim() && !newIn.trim()) {
      onChangeCm(null);
    } else {
      const cm = Math.round(((ft * 12 + inc) * 2.54) * 10) / 10;
      onChangeCm(cm);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <Text style={styles.label}>Height</Text>
        <View style={styles.toggleRow}>
          <TouchableOpacity
            style={[styles.unitButton, unit === 'cm' && styles.unitButtonActive]}
            onPress={() => setUnit('cm')}
          >
            <Text style={[styles.unitText, unit === 'cm' && styles.unitTextActive]}>cm</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.unitButton, unit === 'ft_in' && styles.unitButtonActive]}
            onPress={() => setUnit('ft_in')}
          >
            <Text style={[styles.unitText, unit === 'ft_in' && styles.unitTextActive]}>ft / in</Text>
          </TouchableOpacity>
        </View>
      </View>

      {unit === 'cm' ? (
        <View style={styles.inputRow}>
          <TextInput
            style={[styles.input, error ? styles.inputError : null]}
            placeholder="e.g. 175"
            keyboardType="decimal-pad"
            value={cmText}
            onChangeText={handleCmChange}
          />
          <Text style={styles.suffix}>cm</Text>
        </View>
      ) : (
        <View style={styles.inputRow}>
          <TextInput
            style={[styles.inputHalf, error ? styles.inputError : null]}
            placeholder="ft"
            keyboardType="number-pad"
            value={feetText}
            onChangeText={(txt) => handleFtInChange(txt, inchesText)}
          />
          <Text style={styles.suffix}>ft</Text>
          <TextInput
            style={[styles.inputHalf, error ? styles.inputError : null]}
            placeholder="in"
            keyboardType="decimal-pad"
            value={inchesText}
            onChangeText={(txt) => handleFtInChange(feetText, txt)}
          />
          <Text style={styles.suffix}>in</Text>
        </View>
      )}

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
  inputHalf: {
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
    marginLeft: 6,
    marginRight: 10,
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
