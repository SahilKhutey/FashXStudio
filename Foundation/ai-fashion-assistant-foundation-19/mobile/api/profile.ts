import { apiRequest } from "./client";

export type PhotoType = "skin_tone" | "tryon_reference";
export type PhotoStatus = "upload_pending" | "processing" | "accepted" | "rejected";

export type PhotoCreateResponse = {
  photo_id: string;
  status: PhotoStatus;
  upload_url: string;
  expires_at: string;
};

export type PhotoCompleteResponse = {
  photo_id: string;
  status: PhotoStatus;
  processing_job_id: string;
};

export type PhotoGuidance = {
  photo_id: string;
  state: "ready" | "processing" | "retry" | "not_started" | "failed";
  ready_for_tryon: boolean;
  title: string;
  message: string;
  tips: string[];
  retryable: boolean;
  quality_score?: number | null;
  reasons: string[];
};

export async function createPhotoUpload(input: {
  photo_type: PhotoType;
  content_type: string;
  file_size_bytes: number;
}): Promise<PhotoCreateResponse> {
  return apiRequest<PhotoCreateResponse>("/profile/me/photos", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function completePhotoUpload(photoId: string): Promise<PhotoCompleteResponse> {
  return apiRequest<PhotoCompleteResponse>(`/profile/me/photos/${photoId}/complete`, {
    method: "POST",
  });
}

export async function getPhotoGuidance(photoId: string): Promise<PhotoGuidance> {
  return apiRequest<PhotoGuidance>(`/profile/me/photos/${photoId}/guidance`);
}
