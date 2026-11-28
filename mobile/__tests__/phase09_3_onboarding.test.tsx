import React from "react";
import { WelcomeScreen } from "../src/features/onboarding/screens/WelcomeScreen";
import { ProductIntroScreen } from "../src/features/onboarding/screens/ProductIntroScreen";
import { PrivacyScreen } from "../src/features/onboarding/screens/PrivacyScreen";
import { ConsentScreen } from "../src/features/onboarding/screens/ConsentScreen";
import { HeightInput } from "../src/features/onboarding/components/HeightInput";
import { MeasurementsScreen } from "../src/features/onboarding/screens/MeasurementsScreen";
import { OnboardingProgress } from "../src/features/onboarding/components/OnboardingProgress";
import { useOnboardingStore } from "../src/features/onboarding/onboarding.store";
import { completeOnboarding } from "../src/features/onboarding/onboarding.service";
import * as consentApi from "../src/features/onboarding/consent.api";
import { profileApi } from "../src/features/profile/services/profileApi";
import { fitProfileApi } from "../src/features/fit-profile/api/fitProfileApi";

jest.mock("../src/api/client", () => ({
  api: jest.fn(),
  apiClient: jest.fn(),
}));

type TestNode = {
  props: Record<string, unknown>;
  findByProps: (props: Record<string, unknown>) => TestNode;
  findAllByProps: (props: Record<string, unknown>) => TestNode[];
};

// eslint-disable-next-line @typescript-eslint/no-require-imports
const TestRenderer = require("react-test-renderer") as {
  create: (element: React.ReactElement) => {
    root: TestNode;
    toJSON: () => unknown;
  };
  act: (callback: () => void | Promise<void>) => Promise<void>;
};

describe("Phase 09.3 onboarding screens (WEL, INTRO, PRIV, CON)", () => {
  beforeEach(() => {
    jest.restoreAllMocks();
  });

  it("renders WelcomeScreen and ProductIntroScreen with required VTO & fit disclaimers", async () => {
    const onContinue = jest.fn();
    let welcomeTree!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      welcomeTree = TestRenderer.create(<WelcomeScreen onContinue={onContinue} />);
    });
    expect(JSON.stringify(welcomeTree.toJSON())).toContain("FashXStudio");
    await TestRenderer.act(async () => {
      (welcomeTree.root.findByProps({ accessibilityRole: "button" }).props.onPress as () => void)();
    });
    expect(onContinue).toHaveBeenCalledTimes(1);

    const onSkip = jest.fn();
    let introTree!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      introTree = TestRenderer.create(
        <ProductIntroScreen onContinue={jest.fn()} onSkip={onSkip} />,
      );
    });
    const introJson = JSON.stringify(introTree.toJSON());
    expect(introJson).toContain("AI-generated visual representation");
    expect(introJson).toContain("does not guarantee physical fit");
  });

  it("renders PrivacyScreen and ConsentScreen with all optional switches off by default", async () => {
    const onOpen = jest.fn();
    let privTree!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      privTree = TestRenderer.create(
        <PrivacyScreen
          privacyUrl="https://fashxstudio.com/privacy"
          onOpenPolicy={onOpen}
          onContinue={jest.fn()}
        />,
      );
    });
    await TestRenderer.act(async () => {
      (privTree.root.findByProps({ accessibilityRole: "link" }).props.onPress as () => void)();
    });
    expect(onOpen).toHaveBeenCalledWith("https://fashxstudio.com/privacy");

    const saveSpy = jest
      .spyOn(consentApi, "savePurposeConsent")
      .mockResolvedValue({ ok: true });
    const onComplete = jest.fn();

    let conTree!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      conTree = TestRenderer.create(
        <ConsentScreen noticeVersion="2026.1" onComplete={onComplete} />,
      );
    });

    const persSwitch = conTree.root.findByProps({
      accessibilityLabel: "Allow personalization",
    });
    expect(persSwitch.props.value).toBe(false);

    await TestRenderer.act(async () => {
      (persSwitch.props.onValueChange as (v: boolean) => void)(true);
    });
    await TestRenderer.act(async () => {
      (conTree.root.findByProps({ accessibilityRole: "button" }).props.onPress as () => void)();
    });

    expect(saveSpy).toHaveBeenCalledWith({
      purpose: "PERSONALIZED_RANKING",
      granted: true,
      noticeVersion: "2026.1",
    });
    expect(saveSpy).toHaveBeenCalledWith({
      purpose: "THIRD_PARTY_VTO_PROCESSING",
      granted: false,
      noticeVersion: "2026.1",
    });
    expect(onComplete).toHaveBeenCalledTimes(1);
  });
});

describe("Phase 09.3 height, measurements, and skip behavior (HGT, MEAS, SKIP)", () => {
  it("converts inches to cm in HeightInput and supports skipping", async () => {
    const onSubmit = jest.fn();
    const onSkip = jest.fn();

    let tree!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      tree = TestRenderer.create(<HeightInput onSubmit={onSubmit} onSkip={onSkip} />);
    });

    const buttons = tree.root
      .findAllByProps({ accessibilityRole: "button" })
      .filter((n) => typeof n.props.onPress === "function");
    const inButton = buttons[1]!;
    const continueButton = buttons[2]!;
    const skipButton = buttons[3]!;

    await TestRenderer.act(async () => {
      (inButton.props.onPress as () => void)();
    });
    await TestRenderer.act(async () => {
      (tree.root.findByProps({ accessibilityLabel: "Height" }).props.onChangeText as (v: string) => void)("70");
    });
    await TestRenderer.act(async () => {
      (continueButton.props.onPress as () => void)();
    });
    expect(onSubmit).toHaveBeenCalledWith(177.8);

    await TestRenderer.act(async () => {
      (skipButton.props.onPress as () => void)();
    });
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it("collects optional measurements and allows skipping all fields", async () => {
    const onContinue = jest.fn();
    const onSkip = jest.fn();

    let tree!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      tree = TestRenderer.create(
        <MeasurementsScreen onContinue={onContinue} onSkip={onSkip} />,
      );
    });

    await TestRenderer.act(async () => {
      (tree.root.findByProps({ accessibilityLabel: "Chest in cm" }).props.onChangeText as (v: string) => void)("94");
    });

    const buttons = tree.root
      .findAllByProps({ accessibilityRole: "button" })
      .filter((n) => typeof n.props.onPress === "function");
    await TestRenderer.act(async () => {
      (buttons[0]!.props.onPress as () => void)();
    });
    expect(onContinue).toHaveBeenCalledWith({ CHEST: 94 });

    await TestRenderer.act(async () => {
      (buttons[1]!.props.onPress as () => void)();
    });
    expect(onSkip).toHaveBeenCalledTimes(1);
  });

  it("renders OnboardingProgress cleanly", async () => {
    let tree!: { toJSON: () => unknown };
    await TestRenderer.act(async () => {
      tree = TestRenderer.create(<OnboardingProgress current={3} total={12} />);
    });
    const json = JSON.stringify(tree.toJSON());
    expect(json).toContain('"Step ","3"," of ","12"');
    expect(json).toContain("25%");
  });
});

describe("Phase 09.3 onboarding store & backend persistence (SAVE, PROG)", () => {
  beforeEach(() => {
    jest.restoreAllMocks();
    useOnboardingStore.getState().reset();
  });

  it("persists draft to profileApi & fitProfileApi and resets only after success", async () => {
    const profileSpy = jest
      .spyOn(profileApi, "updateProfile")
      .mockResolvedValue({ user_id: "usr-1" } as never);
    const measSpy = jest
      .spyOn(fitProfileApi, "addMeasurements")
      .mockResolvedValue({} as never);
    const prefSpy = jest
      .spyOn(fitProfileApi, "updateDefaultPreference")
      .mockResolvedValue({} as never);

    useOnboardingStore.getState().updateDraft({
      displayName: "Asha",
      countryCode: "IN",
      preferredUnit: "CM",
      heightCm: 170,
      preferredSizeSystem: "IN",
      measurements: { CHEST: 92, WAIST: 76 },
      fitPreference: "REGULAR",
      stylePreferences: ["MINIMALIST", "ETHNIC"],
      colorPreferences: ["BLACK", "NAVY"],
    });
    useOnboardingStore.getState().skipStep("PRODUCT_INTRO");

    expect(useOnboardingStore.getState().draft.skippedSteps).toEqual(["PRODUCT_INTRO"]);

    await completeOnboarding();

    expect(profileSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        display_name: "Asha",
        country_code: "IN",
        height_cm: 170,
        preferred_size_system: "IN",
        style_preferences: ["MINIMALIST", "ETHNIC"],
        color_preferences: ["BLACK", "NAVY"],
      }),
    );
    expect(measSpy).toHaveBeenCalledWith([
      { field: "CHEST", value: 92, unit: "CM", measurement_method: "SELF_MEASURED" },
      { field: "WAIST", value: 76, unit: "CM", measurement_method: "SELF_MEASURED" },
    ]);
    expect(prefSpy).toHaveBeenCalledWith("REGULAR");
    expect(useOnboardingStore.getState().draft.measurements).toEqual({});
  });
});
