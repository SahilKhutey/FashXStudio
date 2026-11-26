import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";

import { fitProfileApi } from "../api/fitProfileApi";
import { FitPreferenceSelector } from "../components/FitPreferenceSelector";
import { MeasurementGuidanceCard } from "../components/MeasurementGuidanceCard";
import { MeasurementInput } from "../components/MeasurementInput";
import { useFitProfileStore } from "../store/fitProfileStore";
import type {
  FitPreference,
  MeasurementDefinition,
  MeasurementUnit,
} from "../types";

export function FitProfileScreen() {
  const {
    profile,
    definitions,
    loading,
    error,
    setProfile,
    setDefinitions,
    setLoading,
    setError,
    clearProfile,
  } = useFitProfileStore();

  const [editingDef, setEditingDef] = useState<MeasurementDefinition | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      try {
        const [prof, defs] = await Promise.all([
          fitProfileApi.getProfile(),
          fitProfileApi.getDefinitions(),
        ]);
        if (active) {
          setProfile(prof);
          setDefinitions(defs);
        }
      } catch {
        if (active) {
          setError("Could not load your fit profile. Pull to retry.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [setDefinitions, setError, setLoading, setProfile]);

  const savedByField = new Map(
    (profile?.measurements ?? []).map((m) => [m.field, m]),
  );

  const storageConsented = Boolean(profile?.consents?.fit_profile_storage);

  async function handleToggleStorageConsent(granted: boolean) {
    setLoading(true);
    try {
      await fitProfileApi.updateConsent("fit_profile_storage", granted, true);
      const updated = await fitProfileApi.getProfile();
      setProfile(updated);
    } catch {
      setError("Could not update consent preference.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveMeasurement(
    def: MeasurementDefinition,
    value: string,
    unit: MeasurementUnit,
    confirmUnusual = false,
  ) {
    const existing = savedByField.get(def.code);
    if (existing) {
      await fitProfileApi.updateMeasurement(def.code, {
        value,
        unit,
        expected_version: existing.version,
        confirm_unusual: confirmUnusual,
      });
      const updated = await fitProfileApi.getProfile();
      setProfile(updated);
    } else {
      const updated = await fitProfileApi.addMeasurements([
        {
          field: def.code,
          value,
          unit,
          confirm_unusual: confirmUnusual,
        },
      ]);
      setProfile(updated);
    }
    setEditingDef(null);
  }

  async function handleDeleteMeasurement(fieldCode: string) {
    await fitProfileApi.deleteMeasurement(fieldCode);
    const updated = await fitProfileApi.getProfile();
    setProfile(updated);
    setEditingDef(null);
  }

  async function handleDefaultFitChange(pref: FitPreference) {
    const updated = await fitProfileApi.updateDefaultPreference(pref);
    setProfile(updated);
  }

  async function handleDeleteProfile() {
    await fitProfileApi.deleteFitProfile();
    clearProfile();
    const updated = await fitProfileApi.getProfile();
    setProfile(updated);
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.heading}>My Fit Profile</Text>
      <Text style={styles.privacyBanner}>
        Your measurements are private body information. You can update, withdraw consent, or remove them at any time.
      </Text>

      {loading ? <ActivityIndicator size="small" color="#0F766E" /> : null}
      {error ? (
        <Text style={styles.errorText} accessibilityRole="alert">
          {error}
        </Text>
      ) : null}

      {/* Storage Consent Control */}
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Measurement Storage Consent</Text>
        <Text style={styles.caption}>
          Status: {storageConsented ? "Granted" : "Not granted"}
        </Text>
        <Pressable
          style={styles.secondaryButton}
          onPress={() => handleToggleStorageConsent(!storageConsented)}
          accessibilityRole="button"
        >
          <Text style={styles.secondaryButtonText}>
            {storageConsented ? "Withdraw measurement consent" : "Grant storage consent"}
          </Text>
        </Pressable>
      </View>

      {/* Active Measurement Editor */}
      {editingDef ? (
        <View>
          <MeasurementGuidanceCard definition={editingDef} />
          <MeasurementInput
            title={editingDef.display_name}
            explanation={editingDef.explanation}
            fieldCode={editingDef.code}
            hasExistingValue={savedByField.has(editingDef.code)}
            initialValue={
              savedByField.get(editingDef.code)?.value !== undefined
                ? String(savedByField.get(editingDef.code)?.value)
                : ""
            }
            initialUnit={savedByField.get(editingDef.code)?.unit}
            onSave={(val, unit, confirmUnusual) =>
              handleSaveMeasurement(editingDef, val, unit, confirmUnusual)
            }
            onDelete={
              savedByField.has(editingDef.code)
                ? () => handleDeleteMeasurement(editingDef.code)
                : undefined
            }
          />
          <Pressable onPress={() => setEditingDef(null)} accessibilityRole="button">
            <Text style={styles.cancelLink}>Cancel editing</Text>
          </Pressable>
        </View>
      ) : null}

      {/* Measurements List */}
      <Text style={styles.sectionHeader}>Measurements</Text>
      {definitions.map((def) => {
        const saved = savedByField.get(def.code);
        return (
          <View key={def.code} style={styles.card}>
            <View style={styles.rowHeader}>
              <Text style={styles.fieldTitle}>{def.display_name}</Text>
              <Text style={styles.badge}>
                {saved ? saved.status : "NOT PROVIDED"}
              </Text>
            </View>
            {saved ? (
              <View>
                <Text style={styles.valueText}>
                  {saved.value} {saved.unit} ({saved.normalized_value} {saved.normalized_unit})
                </Text>
                <Text style={styles.metaText}>
                  Last measured: {new Date(saved.measured_at).toLocaleDateString()}
                </Text>
              </View>
            ) : (
              <Text style={styles.caption}>{def.explanation}</Text>
            )}
            <Pressable
              onPress={() => setEditingDef(def)}
              accessibilityRole="button"
            >
              <Text style={styles.actionLink}>
                {saved ? "Edit measurement ->" : "Add measurement ->"}
              </Text>
            </Pressable>
          </View>
        );
      })}

      {/* Fit Preference Selector */}
      <FitPreferenceSelector
        title="Default fit preference"
        selected={profile?.default_fit_preference ?? "NO_PREFERENCE"}
        onSelect={handleDefaultFitChange}
      />

      {/* Profile Deletion Control */}
      <Pressable
        style={styles.dangerButton}
        onPress={handleDeleteProfile}
        accessibilityRole="button"
      >
        <Text style={styles.dangerButtonText}>Delete all fit profile data</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F9FAFB" },
  content: { padding: 16, paddingBottom: 40 },
  heading: { fontSize: 22, fontWeight: "700", color: "#111827", marginBottom: 6 },
  privacyBanner: { fontSize: 13, color: "#4B5563", marginBottom: 14 },
  errorText: { color: "#DC2626", fontSize: 13, marginBottom: 10 },
  sectionHeader: { fontSize: 17, fontWeight: "700", color: "#111827", marginTop: 12, marginBottom: 6 },
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    marginBottom: 8,
  },
  rowHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  sectionTitle: { fontSize: 15, fontWeight: "700", color: "#111827", marginBottom: 4 },
  fieldTitle: { fontSize: 15, fontWeight: "700", color: "#111827" },
  badge: { fontSize: 10, fontWeight: "700", color: "#0F766E" },
  valueText: { fontSize: 18, fontWeight: "700", color: "#111827", marginTop: 4 },
  metaText: { fontSize: 11, color: "#6B7280", marginTop: 2 },
  caption: { fontSize: 12, color: "#6B7280", marginTop: 4 },
  actionLink: { marginTop: 8, fontSize: 13, fontWeight: "600", color: "#0F766E" },
  cancelLink: { fontSize: 13, fontWeight: "600", color: "#6B7280", textAlign: "center", marginVertical: 8 },
  secondaryButton: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#0F766E",
    alignSelf: "flex-start",
  },
  secondaryButtonText: { color: "#0F766E", fontSize: 13, fontWeight: "600" },
  dangerButton: {
    marginTop: 18,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#FCA5A5",
    alignItems: "center",
  },
  dangerButtonText: { color: "#B91C1C", fontSize: 14, fontWeight: "600" },
});
