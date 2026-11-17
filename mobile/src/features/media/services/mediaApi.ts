import { api } from '../../../api/client';
import {
  MediaAccessUrlResponse,
  MediaDeletionResponse,
  MediaMetadataResponse,
  UploadCompleteRequest,
  UploadInitiateRequest,
  UploadInitiateResponse,
  UploadStatusResponse,
} from '../types/media.types';

export const mediaApi = {
  initiateUpload: async (
    payload: UploadInitiateRequest,
  ): Promise<UploadInitiateResponse> => {
    return api<UploadInitiateResponse>('/media/uploads', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getUploadStatus: async (
    uploadId: string,
  ): Promise<UploadStatusResponse> => {
    return api<UploadStatusResponse>(`/media/uploads/${uploadId}`);
  },

  completeUpload: async (
    uploadId: string,
    payload?: UploadCompleteRequest,
  ): Promise<UploadStatusResponse> => {
    return api<UploadStatusResponse>(`/media/uploads/${uploadId}/complete`, {
      method: 'POST',
      body: JSON.stringify(payload ?? {}),
    });
  },

  getMediaMetadata: async (
    imageId: string,
  ): Promise<MediaMetadataResponse> => {
    return api<MediaMetadataResponse>(`/media/${imageId}`);
  },

  getMediaAccessUrl: async (
    imageId: string,
  ): Promise<MediaAccessUrlResponse> => {
    return api<MediaAccessUrlResponse>(`/media/${imageId}/access-url`, {
      method: 'POST',
    });
  },

  deleteMedia: async (
    imageId: string,
  ): Promise<MediaDeletionResponse> => {
    return api<MediaDeletionResponse>(`/media/${imageId}`, {
      method: 'DELETE',
    });
  },
};
