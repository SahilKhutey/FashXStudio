import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { PhotoPicker } from '../components/PhotoPicker';
import { usePhotoUpload } from '../hooks/usePhotoUpload';
import { UploadPurpose } from '../types/media.types';

interface PhotoUploadScreenProps {
  purpose?: UploadPurpose;
  onUploadSuccess?: (imageId: string) => void;
  onCancel?: () => void;
}

export const PhotoUploadScreen: React.FC<PhotoUploadScreenProps> = ({
  purpose = 'VTO_PERSONAL_PHOTO',
  onUploadSuccess,
  onCancel,
}) => {
  const [selectedPurpose, setSelectedPurpose] = useState<UploadPurpose>(purpose);
  const {
    selectedPhoto,
    stage,
    error,
    result,
    pickFromGallery,
    captureWithCamera,
    upload,
    reset,
  } = usePhotoUpload();

  const handleUpload = async () => {
    const res = await upload(selectedPurpose);
    if (res && res.status === 'AVAILABLE' && onUploadSuccess) {
      onUploadSuccess(res.image_id);
    }
  };

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.contentContainer}>
      <View style={styles.header}>
        <Text style={styles.title}>Secure Photo Upload</Text>
        <Text style={styles.subtitle}>
          Add a reference photo for your profile or virtual try-on fitting.
        </Text>
      </View>

      <View style={styles.purposeToggle}>
        <TouchableOpacity
          style={[
            styles.toggleOption,
            selectedPurpose === 'VTO_PERSONAL_PHOTO' && styles.toggleOptionActive,
          ]}
          onPress={() => setSelectedPurpose('VTO_PERSONAL_PHOTO')}
        >
          <Text
            style={[
              styles.toggleText,
              selectedPurpose === 'VTO_PERSONAL_PHOTO' && styles.toggleTextActive,
            ]}
          >
            Virtual Try-On
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[
            styles.toggleOption,
            selectedPurpose === 'PROFILE_PHOTO' && styles.toggleOptionActive,
          ]}
          onPress={() => setSelectedPurpose('PROFILE_PHOTO')}
        >
          <Text
            style={[
              styles.toggleText,
              selectedPurpose === 'PROFILE_PHOTO' && styles.toggleTextActive,
            ]}
          >
            Profile Photo
          </Text>
        </TouchableOpacity>
      </View>

      <PhotoPicker
        photo={selectedPhoto}
        stage={stage}
        error={error}
        onPickGallery={pickFromGallery}
        onCaptureCamera={captureWithCamera}
        onUpload={handleUpload}
        onReset={reset}
      />

      <View style={styles.privacyCard}>
        <Text style={styles.privacyTitle}>🔒 Privacy & Security Safeguards</Text>
        <View style={styles.privacyList}>
          <Text style={styles.privacyItem}>
            • <Text style={styles.boldText}>Private Storage:</Text> Stored exclusively in encrypted, private cloud storage with no public web access.
          </Text>
          <Text style={styles.privacyItem}>
            • <Text style={styles.boldText}>Metadata Stripped:</Text> GPS coordinates, device identifiers, and EXIF tags are scrubbed upon receipt.
          </Text>
          <Text style={styles.privacyItem}>
            • <Text style={styles.boldText}>Ephemeral Access:</Text> Pre-signed download URLs expire in 60 seconds and require active authentication.
          </Text>
          <Text style={styles.privacyItem}>
            • <Text style={styles.boldText}>Strict Consent:</Text> Uploading a photo does not authorize third-party processing without separate, explicit consent.
          </Text>
        </View>
      </View>

      {onCancel && (
        <TouchableOpacity style={styles.cancelButton} onPress={onCancel}>
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#111827',
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    lineHeight: 20,
  },
  purposeToggle: {
    flexDirection: 'row',
    backgroundColor: '#E5E7EB',
    borderRadius: 10,
    padding: 4,
    marginBottom: 12,
  },
  toggleOption: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  toggleOptionActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  toggleText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#4B5563',
  },
  toggleTextActive: {
    color: '#4F46E5',
    fontWeight: '600',
  },
  privacyCard: {
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  privacyTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  privacyList: {
    gap: 6,
  },
  privacyItem: {
    fontSize: 12,
    color: '#4B5563',
    lineHeight: 18,
  },
  boldText: {
    fontWeight: '600',
    color: '#1F2937',
  },
  cancelButton: {
    marginTop: 16,
    alignItems: 'center',
    paddingVertical: 12,
  },
  cancelButtonText: {
    color: '#6B7280',
    fontSize: 15,
    fontWeight: '500',
  },
});
