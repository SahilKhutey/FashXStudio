import * as FileSystem from "expo-file-system";
import { TRYON_IMAGE_POLICY } from "./constants";

export async function validateLocalImage(uri: string) {
  const info = await FileSystem.getInfoAsync(uri);

  if (!info.exists) {
    throw new Error("IMAGE_NOT_FOUND");
  }

  if (
    typeof info.size === "number" &&
    info.size > TRYON_IMAGE_POLICY.maxFileSizeBytes
  ) {
    throw new Error("IMAGE_TOO_LARGE");
  }

  if (typeof info.size === "number" && info.size <= 0) {
    throw new Error("IMAGE_EMPTY");
  }

  return {
    uri,
    fileSizeBytes: "size" in info && typeof info.size === "number" ? info.size : null,
  };
}
