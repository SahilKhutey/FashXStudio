import { useCallback, useEffect, useState } from "react";
import { Camera } from "expo-camera";
import {
  completePhotoUpload,
  createPhotoUpload,
  getPhotoGuidance,
  type PhotoGuidance,
} from "../../api/profile";

export type CaptureState = "permission" | "camera" | "uploading" | "processing" | "ready" | "retry" | "error";

export function useTryOnCapture() {
  const [permission, requestPermission] = Camera.useCameraPermissions();
  const [state, setState] = useState<CaptureState>(permission?.granted ? "camera" : "permission");
  const [photoId, setPhotoId] = useState<string | null>(null);
  const [guidance, setGuidance] = useState<PhotoGuidance | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (permission?.granted) setState("camera");
  }, [permission?.granted]);

  const refresh = useCallback(async (id: string) => {
    const result = await getPhotoGuidance(id);
    setGuidance(result);
    if (result.state === "ready") setState("ready");
    else if (result.state === "retry") setState("retry");
    else if (result.state === "processing" || result.state === "not_started") setState("processing");
  }, []);

  useEffect(() => {
    if (!photoId || state !== "processing") return;
    const timer = setInterval(() => {
      void refresh(photoId).catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : "Unable to check photo status.");
      });
    }, 2000);
    return () => clearInterval(timer);
  }, [photoId, state, refresh]);

  const captureAndUpload = useCallback(async (photo: { uri: string; width?: number; height?: number }) => {
    setError(null);
    setState("uploading");
    try {
      const response = await fetch(photo.uri);
      const blob = await response.blob();
      const contentType = blob.type || "image/jpeg";

      if (!blob.size) throw new Error("The captured photo is empty.");
      if (blob.size > 15 * 1024 * 1024) throw new Error("Photo is larger than 15 MB.");

      const upload = await createPhotoUpload({
        photo_type: "tryon_reference",
        content_type: contentType,
        file_size_bytes: blob.size,
      });

      const uploadResponse = await fetch(upload.upload_url, {
        method: "PUT",
        headers: { "Content-Type": contentType },
        body: blob,
      });
      if (!uploadResponse.ok) throw new Error("The photo upload failed. Please try again.");

      const completion = await completePhotoUpload(upload.photo_id);
      setPhotoId(completion.photo_id);
      setState("processing");
      await refresh(completion.photo_id);
    } catch (cause: unknown) {
      setState("error");
      setError(cause instanceof Error ? cause.message : "Unable to process the photo.");
    }
  }, [refresh]);

  const requestCameraPermission = useCallback(async () => {
    const result = await requestPermission();
    if (!result.granted) {
      setState("permission");
      setError("Camera permission is required to capture a try-on photo.");
    } else {
      setState("camera");
      setError(null);
    }
  }, [requestPermission]);

  return {
    permission,
    state,
    photoId,
    guidance,
    error,
    requestCameraPermission,
    captureAndUpload,
    retry: () => {
      setPhotoId(null);
      setGuidance(null);
      setError(null);
      setState("camera");
    },
  };
}
