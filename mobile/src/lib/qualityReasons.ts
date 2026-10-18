import rejectReasonsJson from "../api/reject-reasons.json";

const KNOWN_CODES = new Set<string>(rejectReasonsJson);

export function rejectKey(reason: string | null | undefined): string {
  if (!reason) {
    return "capture.reject.generic";
  }

  const normalized = reason.trim().toLowerCase();

  // 1. Direct code match
  if (KNOWN_CODES.has(normalized)) {
    return `capture.reject.${normalized}`;
  }

  // 2. Descriptive phrase heuristics from validator messages
  if (normalized.includes("too dark") || normalized.includes("dark")) {
    return "capture.reject.too_dark";
  }
  if (normalized.includes("overexposed") || normalized.includes("bright")) {
    return "capture.reject.too_bright";
  }
  if (normalized.includes("contrast")) {
    return "capture.reject.low_contrast";
  }
  if (normalized.includes("resolution") || normalized.includes("below the required")) {
    return "capture.reject.resolution_too_low";
  }
  if (normalized.includes("landscape")) {
    return "capture.reject.landscape_orientation";
  }
  if (normalized.includes("face")) {
    return "capture.reject.face_not_visible";
  }
  if (normalized.includes("multiple")) {
    return "capture.reject.multiple_people";
  }
  if (normalized.includes("person") || normalized.includes("no person")) {
    return "capture.reject.person_not_detected";
  }
  if (normalized.includes("pose") || normalized.includes("upright")) {
    return "capture.reject.pose_not_upright";
  }
  if (normalized.includes("invalid") || normalized.includes("unreadable")) {
    return "capture.reject.invalid_format";
  }

  return "capture.reject.generic";
}
