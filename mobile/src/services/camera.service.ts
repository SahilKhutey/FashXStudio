import { Camera, CameraView, useCameraPermissions } from "expo-camera";

export type PermissionState =
  | "UNKNOWN"
  | "GRANTED"
  | "DENIED"
  | "BLOCKED"
  | "UNAVAILABLE";

export function toPermissionState(
  permission: { granted: boolean; canAskAgain?: boolean } | null | undefined,
): PermissionState {
  if (!permission) {
    return "UNKNOWN";
  }
  if (permission.granted) {
    return "GRANTED";
  }
  if (permission.canAskAgain === false) {
    return "BLOCKED";
  }
  return "DENIED";
}

export { Camera, CameraView, useCameraPermissions };
