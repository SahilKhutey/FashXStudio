export type UploadPurpose = 'PROFILE_PHOTO' | 'VTO_PERSONAL_PHOTO';

export type UploadStatus =
  | 'PENDING_UPLOAD'
  | 'VALIDATING'
  | 'AVAILABLE'
  | 'REJECTED'
  | 'FAILED'
  | 'EXPIRED'
  | 'CANCELLED';

export type MediaStatus = 'AVAILABLE' | 'DELETION_PENDING' | 'DELETED' | 'QUARANTINED';

export interface UploadInitiateRequest {
  purpose: UploadPurpose;
  filename: string;
  content_type: string;
  declared_size_bytes: number;
  client_checksum_sha256?: string;
}

export interface UploadInitiateResponse {
  upload_id: string;
  image_id: string;
  upload_url: string;
  method: 'PUT';
  required_headers: Record<string, string>;
  expires_in_seconds: number;
  status: 'PENDING_UPLOAD';
}

export interface UploadCompleteRequest {
  client_checksum_sha256?: string;
}

export interface UploadStatusResponse {
  upload_id: string;
  image_id: string;
  status: UploadStatus;
  message?: string | null;
}

export interface MediaMetadataResponse {
  id: string;
  user_id: string;
  purpose: string;
  status: MediaStatus;
  content_type: string;
  size_bytes: number;
  width: number;
  height: number;
  sha256_normalized: string;
  created_at: string;
}

export interface MediaAccessUrlResponse {
  image_id: string;
  url: string;
  expires_in_seconds: number;
}

export interface MediaDeletionResponse {
  image_id: string;
  status: 'DELETION_PENDING';
}

export interface SelectedPhoto {
  uri: string;
  filename: string;
  contentType: string;
  fileSizeBytes: number;
  width: number;
  height: number;
}

export interface PreValidationResult {
  valid: boolean;
  errors: string[];
}
