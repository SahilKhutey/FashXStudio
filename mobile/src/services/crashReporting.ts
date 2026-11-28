export type SafeErrorContext = {
  feature?: string;
  screen?: string;
  requestId?: string;
  extra?: Record<string, unknown>;
};

export type CrashReportPayload = {
  name: string;
  message: string;
  feature: string;
  screen: string;
  requestId?: string;
};

export type CrashSink = (payload: CrashReportPayload) => void;

let activeSink: CrashSink | null = null;

const SENSITIVE_PATTERN =
  /(bearer\s+[a-z0-9._-]+|https?:\/\/[^\s]*\?(?:[^ \n]*signature|[^ \n]*x-amz-[^ \n]*)|data:image\/[a-z]+;base64,[^\s]+|file:\/\/[^\s]+)/gi;

export function redactSensitiveText(input: string): string {
  return input.replace(SENSITIVE_PATTERN, "[REDACTED]");
}

export function initializeCrashReporting(sink?: CrashSink) {
  activeSink = sink ?? null;
}

export function captureSafeError(
  error: unknown,
  context: SafeErrorContext = {},
): CrashReportPayload {
  const payload: CrashReportPayload = {
    name: error instanceof Error ? error.name : "NonErrorFailure",
    message:
      error instanceof Error
        ? redactSensitiveText(error.message)
        : "A non-Error failure occurred in the application",
    feature: context.feature ?? "unknown",
    screen: context.screen ?? "unknown",
    ...(context.requestId ? { requestId: context.requestId } : {}),
  };

  activeSink?.(payload);
  return payload;
}
