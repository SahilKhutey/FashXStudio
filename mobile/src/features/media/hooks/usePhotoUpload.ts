import { useState, useCallback } from 'react';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system';
import {
  SelectedPhoto,
  UploadPurpose,
  UploadStatusResponse,
} from '../types/media.types';
import {
  executePhotoUploadPipeline,
  validateLocalPhoto,
} from '../services/uploadService';

export type UploadStage =
  | 'idle'
  | 'selecting'
  | 'prevalidating'
  | 'initiating'
  | 'uploading'
  | 'validating'
  | 'completed'
  | 'error';

export function usePhotoUpload() {
  const [selectedPhoto, setSelectedPhoto] = useState<SelectedPhoto | null>(null);
  const [stage, setStage] = useState<UploadStage>('idle');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<UploadStatusResponse | null>(null);

  const processPickerResult = useCallback(async (pickerResult: ImagePicker.ImagePickerResult) => {
    if (pickerResult.canceled || !pickerResult.assets || pickerResult.assets.length === 0) {
      return null;
    }

    const asset = pickerResult.assets[0];
    if (!asset) {
      return null;
    }
    const fileInfo = await FileSystem.getInfoAsync(asset.uri);
    const fileSizeBytes = fileInfo.exists && 'size' in fileInfo ? fileInfo.size : (asset.fileSize ?? 0);

    const filename = asset.fileName || asset.uri.split('/').pop() || 'upload.jpg';
    let contentType = asset.mimeType || 'image/jpeg';
    if (filename.toLowerCase().endsWith('.png')) {
      contentType = 'image/png';
    } else if (filename.toLowerCase().endsWith('.webp')) {
      contentType = 'image/webp';
    }

    const photo: SelectedPhoto = {
      uri: asset.uri,
      filename,
      contentType,
      fileSizeBytes,
      width: asset.width,
      height: asset.height,
    };

    const preCheck = validateLocalPhoto(photo);
    if (!preCheck.valid) {
      setError(preCheck.errors.join(' '));
      setSelectedPhoto(photo);
      setStage('error');
      return null;
    }

    setSelectedPhoto(photo);
    setError(null);
    setStage('idle');
    return photo;
  }, []);

  const pickFromGallery = useCallback(async () => {
    try {
      setStage('selecting');
      setError(null);
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        setError('Photo library access permission is required.');
        setStage('error');
        return null;
      }

      const res = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.9,
      });

      return await processPickerResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to select photo.';
      setError(msg);
      setStage('error');
      return null;
    }
  }, [processPickerResult]);

  const captureWithCamera = useCallback(async () => {
    try {
      setStage('selecting');
      setError(null);
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (!perm.granted) {
        setError('Camera access permission is required.');
        setStage('error');
        return null;
      }

      const res = await ImagePicker.launchCameraAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        quality: 0.9,
      });

      return await processPickerResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to capture photo.';
      setError(msg);
      setStage('error');
      return null;
    }
  }, [processPickerResult]);

  const upload = useCallback(async (purpose: UploadPurpose = 'VTO_PERSONAL_PHOTO') => {
    if (!selectedPhoto) {
      setError('Please select a photo before uploading.');
      setStage('error');
      return null;
    }

    try {
      setError(null);
      const res = await executePhotoUploadPipeline(
        selectedPhoto,
        purpose,
        (currentStage) => setStage(currentStage),
      );
      setResult(res);
      setStage('completed');
      return res;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Photo upload failed.';
      setError(msg);
      setStage('error');
      return null;
    }
  }, [selectedPhoto]);

  const reset = useCallback(() => {
    setSelectedPhoto(null);
    setStage('idle');
    setError(null);
    setResult(null);
  }, []);

  return {
    selectedPhoto,
    stage,
    error,
    result,
    pickFromGallery,
    captureWithCamera,
    upload,
    reset,
  };
}
