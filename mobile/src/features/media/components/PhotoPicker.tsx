import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { SelectedPhoto } from '../types/media.types';
import { UploadStage } from '../hooks/usePhotoUpload';

interface PhotoPickerProps {
  photo: SelectedPhoto | null;
  stage: UploadStage;
  error: string | null;
  onPickGallery: () => void;
  onCaptureCamera: () => void;
  onUpload: () => void;
  onReset: () => void;
}

export const PhotoPicker: React.FC<PhotoPickerProps> = ({
  photo,
  stage,
  error,
  onPickGallery,
  onCaptureCamera,
  onUpload,
  onReset,
}) => {
  const isBusy =
    stage === 'selecting' ||
    stage === 'initiating' ||
    stage === 'uploading' ||
    stage === 'validating';

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <View style={styles.container}>
      {photo ? (
        <View style={styles.previewContainer}>
          <Image source={{ uri: photo.uri }} style={styles.previewImage} resizeMode="cover" />
          <View style={styles.metaRow}>
            <Text style={styles.metaText}>
              {photo.width} × {photo.height} px
            </Text>
            <Text style={styles.metaDot}>•</Text>
            <Text style={styles.metaText}>{formatFileSize(photo.fileSizeBytes)}</Text>
            <Text style={styles.metaDot}>•</Text>
            <Text style={styles.metaText}>{photo.contentType.split('/')[1]?.toUpperCase()}</Text>
          </View>

          {stage === 'completed' && (
            <View style={styles.successBanner}>
              <Text style={styles.successText}>✓ Photo uploaded & validated successfully</Text>
            </View>
          )}

          {error && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorText}>⚠ {error}</Text>
            </View>
          )}

          {isBusy && (
            <View style={styles.statusBox}>
              <ActivityIndicator size="small" color="#4F46E5" />
              <Text style={styles.statusText}>
                {stage === 'initiating' && 'Authorizing secure upload...'}
                {stage === 'uploading' && 'Streaming to encrypted storage...'}
                {stage === 'validating' && 'Verifying dimensions & format safety...'}
                {stage === 'selecting' && 'Processing selection...'}
              </Text>
            </View>
          )}

          <View style={styles.actionRow}>
            {stage !== 'completed' && !isBusy && (
              <TouchableOpacity
                style={[styles.primaryButton, error ? styles.buttonDisabled : null]}
                onPress={onUpload}
                disabled={Boolean(error)}
              >
                <Text style={styles.primaryButtonText}>Upload Photo</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={styles.secondaryButton}
              onPress={onReset}
              disabled={isBusy}
            >
              <Text style={styles.secondaryButtonText}>
                {stage === 'completed' ? 'Choose Another' : 'Change Photo'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <View style={styles.emptyContainer}>
          <View style={styles.iconCircle}>
            <Text style={styles.iconText}>📷</Text>
          </View>
          <Text style={styles.emptyTitle}>Select or Take a Photo</Text>
          <Text style={styles.emptySubtitle}>
            JPEG, PNG, or WebP • 10 KB to 10 MB • Up to 4096×4096 px
          </Text>

          {error && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorText}>⚠ {error}</Text>
            </View>
          )}

          <View style={styles.pickerButtons}>
            <TouchableOpacity
              style={styles.pickerButton}
              onPress={onPickGallery}
              disabled={isBusy}
            >
              <Text style={styles.pickerButtonText}>Choose from Gallery</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.pickerButton, styles.cameraButton]}
              onPress={onCaptureCamera}
              disabled={isBusy}
            >
              <Text style={[styles.pickerButtonText, styles.cameraButtonText]}>
                Use Camera
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#EEF2FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  iconText: {
    fontSize: 28,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 20,
    paddingHorizontal: 16,
  },
  pickerButtons: {
    width: '100%',
    gap: 10,
  },
  pickerButton: {
    backgroundColor: '#4F46E5',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 10,
    alignItems: 'center',
  },
  pickerButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  cameraButton: {
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  cameraButtonText: {
    color: '#374151',
  },
  previewContainer: {
    alignItems: 'center',
  },
  previewImage: {
    width: '100%',
    height: 280,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    marginBottom: 12,
  },
  metaText: {
    fontSize: 13,
    color: '#6B7280',
  },
  metaDot: {
    fontSize: 13,
    color: '#9CA3AF',
    marginHorizontal: 8,
  },
  statusBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EEF2FF',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    marginVertical: 10,
    width: '100%',
    gap: 10,
  },
  statusText: {
    fontSize: 14,
    color: '#4338CA',
    fontWeight: '500',
  },
  successBanner: {
    backgroundColor: '#ECFDF5',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    marginVertical: 10,
    width: '100%',
    borderWidth: 1,
    borderColor: '#A7F3D0',
  },
  successText: {
    color: '#065F46',
    fontSize: 14,
    fontWeight: '500',
    textAlign: 'center',
  },
  errorBanner: {
    backgroundColor: '#FEF2F2',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    marginVertical: 10,
    width: '100%',
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  errorText: {
    color: '#991B1B',
    fontSize: 13,
    fontWeight: '500',
    textAlign: 'center',
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 8,
    width: '100%',
  },
  primaryButton: {
    flex: 1,
    backgroundColor: '#4F46E5',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#A5B4FC',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  secondaryButtonText: {
    color: '#374151',
    fontSize: 15,
    fontWeight: '500',
  },
});
