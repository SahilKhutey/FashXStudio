import { mediaApi } from './mediaApi';
import {
  PreValidationResult,
  SelectedPhoto,
  UploadPurpose,
  UploadStatusResponse,
} from '../types/media.types';

export const MIN_FILE_SIZE_BYTES = 10 * 1024; // 10 KB
export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB
export const MAX_DIMENSION_PX = 4096;
export const MAX_PIXELS = 20_000_000;
export const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export function validateLocalPhoto(photo: SelectedPhoto): PreValidationResult {
  const errors: string[] = [];

  const normalizedMime = photo.contentType.toLowerCase().trim();
  if (!ALLOWED_MIME_TYPES.includes(normalizedMime)) {
    errors.push('Supported formats are JPEG, PNG, and WebP.');
  }

  if (photo.fileSizeBytes < MIN_FILE_SIZE_BYTES) {
    errors.push('File size is below the minimum limit of 10 KB.');
  }

  if (photo.fileSizeBytes > MAX_FILE_SIZE_BYTES) {
    errors.push('File size exceeds the maximum limit of 10 MB.');
  }

  if (photo.width > MAX_DIMENSION_PX || photo.height > MAX_DIMENSION_PX) {
    errors.push(`Image dimensions exceed the maximum limit of ${MAX_DIMENSION_PX}px.`);
  }

  if (photo.width * photo.height > MAX_PIXELS) {
    errors.push('Image resolution exceeds the 20 megapixel safety limit.');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

export async function uploadToPresignedUrl(
  uploadUrl: string,
  fileUri: string,
  contentType: string,
): Promise<void> {
  const fileResponse = await fetch(fileUri);
  const blob = await fileResponse.blob();

  const uploadResult = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Content-Type': contentType,
    },
    body: blob,
  });

  if (!uploadResult.ok) {
    throw new Error(`Upload to storage failed with status ${uploadResult.status}`);
  }
}

export async function pollUploadCompletion(
  uploadId: string,
  maxAttempts: number = 10,
  intervalMs: number = 1500,
): Promise<UploadStatusResponse> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const statusRes = await mediaApi.getUploadStatus(uploadId);
    if (statusRes.status === 'AVAILABLE' || statusRes.status === 'REJECTED' || statusRes.status === 'FAILED') {
      return statusRes;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error('Photo validation timed out. Please check back shortly.');
}

export async function executePhotoUploadPipeline(
  photo: SelectedPhoto,
  purpose: UploadPurpose,
  onStageChange?: (stage: 'initiating' | 'uploading' | 'validating' | 'completed') => void,
): Promise<UploadStatusResponse> {
  const preCheck = validateLocalPhoto(photo);
  if (!preCheck.valid) {
    throw new Error(preCheck.errors.join(' '));
  }

  onStageChange?.('initiating');
  const initiateRes = await mediaApi.initiateUpload({
    purpose,
    filename: photo.filename,
    content_type: photo.contentType,
    declared_size_bytes: photo.fileSizeBytes,
  });

  onStageChange?.('uploading');
  await uploadToPresignedUrl(
    initiateRes.upload_url,
    photo.uri,
    photo.contentType,
  );

  onStageChange?.('validating');
  const completeRes = await mediaApi.completeUpload(initiateRes.upload_id);

  if (completeRes.status === 'VALIDATING') {
    const finalStatus = await pollUploadCompletion(initiateRes.upload_id);
    onStageChange?.('completed');
    return finalStatus;
  }

  onStageChange?.('completed');
  return completeRes;
}
