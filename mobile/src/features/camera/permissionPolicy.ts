export type CameraPermissionStatus =
  | "unknown"
  | "granted"
  | "denied"
  | "blocked";

export type CameraAction =
  | "REQUEST_PERMISSION"
  | "SHOW_DENIAL_HELP"
  | "OPEN_SETTINGS"
  | "CONTINUE_CAPTURE";

export function getCameraPermissionAction(
  state: CameraPermissionStatus,
): CameraAction {
  switch (state) {
    case "unknown":
      return "REQUEST_PERMISSION";
    case "granted":
      return "CONTINUE_CAPTURE";
    case "denied":
      return "SHOW_DENIAL_HELP";
    case "blocked":
      return "OPEN_SETTINGS";
  }
}
