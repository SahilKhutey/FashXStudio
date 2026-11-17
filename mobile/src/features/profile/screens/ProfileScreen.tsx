import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { useProfileStore } from '../store/profileStore';
import { ProfileCompletionCard } from '../components/ProfileCompletionCard';
import { EditPhysicalProfileScreen } from './EditPhysicalProfileScreen';
import { EditStylePreferencesScreen } from './EditStylePreferencesScreen';
import { EditShoppingPreferencesScreen } from './EditShoppingPreferencesScreen';

type ActiveModal = 'NONE' | 'PHYSICAL' | 'STYLE' | 'SHOPPING';

export const ProfileScreen: React.FC = () => {
  const { profile, completeness, isLoading, fetchProfile } = useProfileStore();
  const [activeModal, setActiveModal] = useState<ActiveModal>('NONE');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchProfile();
    setRefreshing(false);
  };

  if (activeModal === 'PHYSICAL') {
    return (
      <EditPhysicalProfileScreen
        onSaved={() => setActiveModal('NONE')}
        onCancel={() => setActiveModal('NONE')}
      />
    );
  }

  if (activeModal === 'STYLE') {
    return (
      <EditStylePreferencesScreen
        onSaved={() => setActiveModal('NONE')}
        onCancel={() => setActiveModal('NONE')}
      />
    );
  }

  if (activeModal === 'SHOPPING') {
    return (
      <EditShoppingPreferencesScreen
        onSaved={() => setActiveModal('NONE')}
        onCancel={() => setActiveModal('NONE')}
      />
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.title}>Shopper Profile</Text>
          <Text style={styles.subtitle}>
            Your sizing, fit, and style preferences
          </Text>
        </View>
        {isLoading && !refreshing && <ActivityIndicator size="small" color="#4F46E5" />}
      </View>

      <ProfileCompletionCard completeness={completeness} />

      {/* Physical & Sizing Section */}
      <View style={styles.sectionCard}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Physical & Sizing</Text>
          <TouchableOpacity
            style={styles.editBtn}
            onPress={() => setActiveModal('PHYSICAL')}
          >
            <Text style={styles.editBtnText}>Edit</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Height:</Text>
          <Text style={styles.infoValue}>
            {profile?.height_cm ? `${profile.height_cm} cm` : 'Not set'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Weight:</Text>
          <Text style={styles.infoValue}>
            {profile?.weight_kg ? `${profile.weight_kg} kg` : 'Not set'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Preferred Fit:</Text>
          <Text style={styles.infoValue}>
            {profile?.preferred_fit || 'Not set'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Size System:</Text>
          <Text style={styles.infoValue}>
            {profile?.preferred_size_system || 'Not set'}
          </Text>
        </View>
      </View>

      {/* Style & Aesthetic Section */}
      <View style={styles.sectionCard}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Style & Aesthetic</Text>
          <TouchableOpacity
            style={styles.editBtn}
            onPress={() => setActiveModal('STYLE')}
          >
            <Text style={styles.editBtnText}>Edit</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.infoBlock}>
          <Text style={styles.infoLabel}>Aesthetic Preferences:</Text>
          <Text style={styles.infoValue}>
            {profile?.style_preferences && profile.style_preferences.length > 0
              ? profile.style_preferences.join(', ')
              : 'None selected'}
          </Text>
        </View>
        <View style={styles.infoBlock}>
          <Text style={styles.infoLabel}>Preferred Colors:</Text>
          <Text style={styles.infoValue}>
            {profile?.preferred_colors && profile.preferred_colors.length > 0
              ? profile.preferred_colors.join(', ')
              : 'None selected'}
          </Text>
        </View>
        <View style={styles.infoBlock}>
          <Text style={styles.infoLabel}>Categories:</Text>
          <Text style={styles.infoValue}>
            {profile?.product_categories && profile.product_categories.length > 0
              ? profile.product_categories.join(', ')
              : 'All categories'}
          </Text>
        </View>
      </View>

      {/* Shopping & Budget Section */}
      <View style={styles.sectionCard}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Shopping & Budget</Text>
          <TouchableOpacity
            style={styles.editBtn}
            onPress={() => setActiveModal('SHOPPING')}
          >
            <Text style={styles.editBtnText}>Edit</Text>
          </TouchableOpacity>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Budget Range:</Text>
          <Text style={styles.infoValue}>
            {profile?.shopping_preferences?.budget?.min != null ||
            profile?.shopping_preferences?.budget?.max != null
              ? `₹${profile?.shopping_preferences?.budget?.min ?? 0} – ₹${profile?.shopping_preferences?.budget?.max ?? 'Any'}`
              : 'Not set'}
          </Text>
        </View>
        <View style={styles.infoBlock}>
          <Text style={styles.infoLabel}>Occasions / Intents:</Text>
          <Text style={styles.infoValue}>
            {profile?.shopping_preferences?.shopping_intents &&
            profile.shopping_preferences.shopping_intents.length > 0
              ? profile.shopping_preferences.shopping_intents.join(', ')
              : 'None selected'}
          </Text>
        </View>
        <View style={styles.infoBlock}>
          <Text style={styles.infoLabel}>Preferred Brands:</Text>
          <Text style={styles.infoValue}>
            {profile?.shopping_preferences?.preferred_brands &&
            profile.shopping_preferences.preferred_brands.length > 0
              ? profile.shopping_preferences.preferred_brands.join(', ')
              : 'None selected'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Eco / Sustainability:</Text>
          <Text style={styles.infoValue}>
            {profile?.shopping_preferences?.sustainability_preference
              ? 'Preferred'
              : 'Standard'}
          </Text>
        </View>
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
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  title: {
    fontSize: 22,
    fontWeight: '800',
    color: '#111827',
  },
  subtitle: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
  },
  sectionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginVertical: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    paddingBottom: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  editBtn: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: '#EEF2FF',
  },
  editBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#4F46E5',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 4,
  },
  infoBlock: {
    marginVertical: 4,
  },
  infoLabel: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  infoValue: {
    fontSize: 14,
    color: '#111827',
    fontWeight: '600',
    marginTop: 1,
  },
});
