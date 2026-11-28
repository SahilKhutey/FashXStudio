import React from "react";
import { getLayoutMetrics } from "../src/hooks/useResponsiveLayout";
import { deriveNetworkStatus } from "../src/hooks/useNetworkStatus";
import {
  captureSafeError,
  initializeCrashReporting,
  redactSensitiveText,
} from "../src/services/crashReporting";
import { getCameraPermissionAction } from "../src/features/camera/permissionPolicy";
import { AccessibleButton } from "../src/components/AccessibleButton";
import { ImageWithFallback } from "../src/components/ImageWithFallback";
import { NetworkStatusBanner } from "../src/components/NetworkStatusBanner";

type TestNode = {
  props: Record<string, unknown>;
  findByProps: (props: Record<string, unknown>) => TestNode;
};

// eslint-disable-next-line @typescript-eslint/no-require-imports
const TestRenderer = require("react-test-renderer") as {
  create: (element: React.ReactElement) => {
    root: TestNode;
    toJSON: () => unknown;
  };
  act: (callback: () => void | Promise<void>) => Promise<void>;
};

describe("Phase 09.8 responsive layout metrics (MOB-RESP)", () => {
  it("adapts columns and gutters across compact, phone, tablet, and desktop widths", () => {
    const compact = getLayoutMetrics(320, 720, 1);
    expect(compact.layout).toBe("compact");
    expect(compact.columns).toBe(1);
    expect(compact.horizontalPadding).toBe(12);

    const phone = getLayoutMetrics(390, 844, 1.3);
    expect(phone.layout).toBe("phone");
    expect(phone.columns).toBe(2);
    expect(phone.horizontalPadding).toBe(16);

    const tablet = getLayoutMetrics(800, 1080, 1);
    expect(tablet.layout).toBe("tablet");
    expect(tablet.columns).toBe(3);
    expect(tablet.isTablet).toBe(true);

    const desktop = getLayoutMetrics(1100, 1366, 1);
    expect(desktop.layout).toBe("desktop");
    expect(desktop.columns).toBe(4);
  });
});

describe("Phase 09.8 network status & crash reporting redaction (MOB-NET, MOB-CRASH)", () => {
  it("classifies connected, unknown-reachability, and offline states accurately", () => {
    expect(deriveNetworkStatus(true, null).offline).toBe(false);
    expect(deriveNetworkStatus(true, false).offline).toBe(true);
    expect(deriveNetworkStatus(false, null).offline).toBe(true);
  });

  it("redacts Bearer tokens, signed URLs, base64 images, and file URIs in crash reports", () => {
    const sink = jest.fn();
    initializeCrashReporting(sink);

    const err = new Error(
      "Upload failed for file:///tmp/photo.jpg with Bearer secret.jwt.token and https://s3.example.com/img?X-Amz-Signature=abc123",
    );
    const payload = captureSafeError(err, {
      feature: "tryon",
      screen: "capture",
      requestId: "req-99",
    });

    expect(payload.message).not.toContain("secret.jwt.token");
    expect(payload.message).not.toContain("X-Amz-Signature");
    expect(payload.message).not.toContain("file:///tmp/photo.jpg");
    expect(redactSensitiveText("data:image/jpeg;base64,/9j/4AAQ==")).toBe("[REDACTED]");
    expect(sink).toHaveBeenCalledTimes(1);
  });
});

describe("Phase 09.8 camera permission policy & accessible components (MOB-PERM, MOB-A11Y, MOB-IMG)", () => {
  it("maps permission states to deterministic actions", () => {
    expect(getCameraPermissionAction("unknown")).toBe("REQUEST_PERMISSION");
    expect(getCameraPermissionAction("granted")).toBe("CONTINUE_CAPTURE");
    expect(getCameraPermissionAction("denied")).toBe("SHOW_DENIAL_HELP");
    expect(getCameraPermissionAction("blocked")).toBe("OPEN_SETTINGS");
  });

  it("renders AccessibleButton with 48dp target, ImageWithFallback, and NetworkStatusBanner", async () => {
    let btnTree!: { root: TestNode; toJSON: () => unknown };
    let imgTree!: { toJSON: () => unknown };
    let bannerTree!: { toJSON: () => unknown };

    await TestRenderer.act(async () => {
      btnTree = TestRenderer.create(
        <AccessibleButton label="Save product" onPress={jest.fn()} loading={false} />,
      );
      imgTree = TestRenderer.create(
        <ImageWithFallback uri={null} accessibilityLabel="Blue cotton shirt" />,
      );
      bannerTree = TestRenderer.create(<NetworkStatusBanner forceOffline={true} />);
    });

    const pressable = btnTree.root.findByProps({ accessibilityRole: "button" });
    expect(pressable.props.accessibilityLabel).toBe("Save product");
    expect(JSON.stringify(imgTree.toJSON())).toContain("Image unavailable");
    expect(JSON.stringify(bannerTree.toJSON())).toContain("You're offline");
  });
});
