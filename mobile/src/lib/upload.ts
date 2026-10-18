import { getAccessToken } from "./token";
import { env } from "./env";

const FIELD = "file";

export interface UploadPhotoResult {
  photo_id: string;
  user_id: string;
  photo_type: string;
  status: "accepted" | "rejected";
  storage_key?: string | null;
  reject_reason?: string | null;
  skin_tone?: Record<string, any> | null;
}

export async function uploadPhoto(
  userId: string,
  uri: string,
  onProgress: (p: number) => void
): Promise<UploadPhotoResult> {
  const token = await getAccessToken();
  const form = new FormData();
  form.append(FIELD, {
    uri,
    name: "photo.jpg",
    type: "image/jpeg",
  } as any);

  return new Promise((resolve, reject) => {
    const x = new XMLHttpRequest();
    x.open("POST", `${env.apiUrl}/api/v1/profile/${userId}/photos`);
    if (token) {
      x.setRequestHeader("Authorization", `Bearer ${token}`);
    }
    x.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        onProgress(e.loaded / e.total);
      }
    };
    x.onload = () => {
      let body: any = {};
      try {
        body = JSON.parse(x.responseText);
      } catch {
        body = {};
      }
      if (x.status >= 200 && x.status < 300) {
        resolve(body as UploadPhotoResult);
      } else {
        const err = body?.error || body;
        reject(err);
      }
    };
    x.onerror = () => {
      reject(new Error("Network error during upload"));
    };
    x.send(form);
  });
}
