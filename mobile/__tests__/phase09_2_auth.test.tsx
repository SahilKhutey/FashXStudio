import React from "react";
import { AuthError, toAuthUserMessage } from "../src/auth/auth.errors";
import { maskEmail } from "../src/auth/auth.types";
import { ProviderAuthService } from "../src/auth/auth.service";
import type { AuthProvider } from "../src/auth/auth.provider";
import { authProviderService } from "../src/auth/auth.instance";
import { refreshSessionOnce } from "../src/auth/refresh-manager";
import { initializeAuthSession, performAppLogout } from "../src/auth/logout";
import { useAuthStore } from "../src/auth/stores/authStore";
import { useAppStore } from "../src/stores/app.store";
import { RegisterScreen } from "../src/features/auth/RegisterScreen";
import { LoginScreen } from "../src/features/auth/LoginScreen";
import { VerificationScreen } from "../src/features/auth/VerificationScreen";
import { RecoveryScreen } from "../src/features/auth/RecoveryScreen";
import { queryClient } from "../src/app-shell/queryClient";
import * as sessionModule from "../src/auth/session";

jest.mock("../src/lib/supabase", () => ({
  supabase: {
    auth: {
      signUp: jest.fn(),
      signInWithPassword: jest.fn(),
      verifyOtp: jest.fn(),
      resend: jest.fn(),
      resetPasswordForEmail: jest.fn(),
      updateUser: jest.fn(),
      getSession: jest.fn(),
      refreshSession: jest.fn(),
      signOut: jest.fn(),
    },
  },
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

describe("Phase 09.2 auth types, errors, and provider service", () => {
  it("masks email addresses before display", () => {
    expect(maskEmail("Shopper@Example.com")).toBe("s***r@example.com");
    expect(maskEmail("a@b.com")).toBe("***@b.com");
  });

  it("maps AuthError codes to user-safe copy without leaking internals", () => {
    const err = new AuthError("NETWORK_UNAVAILABLE", "ECONNREFUSED 10.0.0.1", true);
    expect(toAuthUserMessage(err)).toBe("Check your internet connection and try again.");
    expect(toAuthUserMessage(new Error("SQL syntax error at line 1"))).toBe(
      "Something went wrong. Please try again.",
    );
  });

  it("delegates registration and login through ProviderAuthService", async () => {
    const mockProvider: AuthProvider = {
      register: jest.fn().mockResolvedValue({
        status: "VERIFICATION_REQUIRED",
        email: "user@fashxstudio.com",
        destination: "u***r@fashxstudio.com",
      }),
      login: jest.fn().mockResolvedValue({ status: "AUTHENTICATED" }),
      confirmRegistration: jest.fn().mockResolvedValue(undefined),
      resendVerificationCode: jest.fn().mockResolvedValue(undefined),
      startRecovery: jest.fn().mockResolvedValue(undefined),
      completeRecovery: jest.fn().mockResolvedValue(undefined),
      getCurrentSession: jest.fn().mockResolvedValue(null),
      getAccessToken: jest.fn().mockResolvedValue(null),
      refreshSession: jest.fn(),
      logout: jest.fn().mockResolvedValue(undefined),
    };

    const svc = new ProviderAuthService(mockProvider);
    const reg = await svc.register({
      name: "Asha Rao",
      email: "user@fashxstudio.com",
      password: "StrongPassword123!",
    });
    expect(reg.status).toBe("VERIFICATION_REQUIRED");
    expect(
      (await svc.login({ email: "user@fashxstudio.com", password: "StrongPassword123!" })).status,
    ).toBe("AUTHENTICATED");
  });
});

describe("Phase 09.2 single-flight refresh, session init, and logout", () => {
  beforeEach(() => {
    jest.restoreAllMocks();
    useAppStore.getState().reset();
    useAuthStore.getState().setUnauthenticated();
  });

  it("coalesces concurrent refreshSessionOnce calls into one provider call", async () => {
    let resolveRefresh!: (value: {
      user: { subject: string };
      accessToken: string;
      expiresAt: number;
    }) => void;
    const refreshSpy = jest
      .spyOn(authProviderService, "refreshSession")
      .mockImplementation(
        () =>
          new Promise((resolve) => {
            resolveRefresh = resolve;
          }),
      );

    const p1 = refreshSessionOnce();
    const p2 = refreshSessionOnce();
    expect(refreshSpy).toHaveBeenCalledTimes(1);

    resolveRefresh({
      user: { subject: "usr-1" },
      accessToken: "fresh-token",
      expiresAt: 9999999999,
    });

    const [r1, r2] = await Promise.all([p1, p2]);
    expect(r1.accessToken).toBe("fresh-token");
    expect(r2.accessToken).toBe("fresh-token");
  });

  it("restores authenticated session via initializeAuthSession", async () => {
    jest.spyOn(authProviderService, "getCurrentSession").mockResolvedValue({
      user: { subject: "usr-42", email: "shopper@fashxstudio.com" },
      accessToken: "tok-42",
      expiresAt: 9999999999,
    });

    await initializeAuthSession();
    expect(useAuthStore.getState().isAuthenticated).toBe(true);
    expect(useAuthStore.getState().userId).toBe("usr-42");
  });

  it("clears local session, queryCache, and appStore even when remote logout fails", async () => {
    useAppStore.getState().setSearchQuery("linen shirt");
    useAuthStore.getState().setAuthenticated("usr-42");

    jest.spyOn(authProviderService, "logout").mockRejectedValue(new Error("offline"));
    const purgeSpy = jest.spyOn(sessionModule, "purgeLocalSession").mockResolvedValue(undefined);
    const cacheClearSpy = jest.spyOn(queryClient, "clear");

    await performAppLogout();

    expect(purgeSpy).toHaveBeenCalledTimes(1);
    expect(cacheClearSpy).toHaveBeenCalled();
    expect(useAppStore.getState().searchQuery).toBe("");
    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().userId).toBeNull();
  });
});

describe("Phase 09.2 auth screens (REG, LOG, VER, REC)", () => {
  beforeEach(() => {
    jest.restoreAllMocks();
  });

  it("validates registration inputs and calls verification callback on success", async () => {
    const regSpy = jest.spyOn(authProviderService, "register").mockResolvedValue({
      status: "VERIFICATION_REQUIRED",
      email: "asha@example.com",
      destination: "a***a@example.com",
    });
    const onVerify = jest.fn();

    let renderer!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      renderer = TestRenderer.create(
        <RegisterScreen onVerificationRequired={onVerify} onLoginPress={jest.fn()} />,
      );
    });

    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ placeholder: "Full name" }).props.onChangeText as (v: string) => void)("Asha Rao");
      (renderer.root.findByProps({ placeholder: "Email address" }).props.onChangeText as (v: string) => void)("Asha@Example.com");
      (renderer.root.findByProps({ placeholder: "Password (min 12 characters)" }).props.onChangeText as (v: string) => void)("StrongPass123!");
      (renderer.root.findByProps({ placeholder: "Confirm password" }).props.onChangeText as (v: string) => void)("StrongPass123!");
      (renderer.root.findByProps({ accessibilityRole: "checkbox" }).props.onPress as () => void)();
    });

    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ accessibilityRole: "button" }).props.onPress as () => void)();
    });

    expect(regSpy).toHaveBeenCalledWith({
      name: "Asha Rao",
      email: "asha@example.com",
      password: "StrongPass123!",
    });
    expect(onVerify).toHaveBeenCalledWith("asha@example.com");
  });

  it("signs in via LoginScreen and routes unverified accounts to verification", async () => {
    jest.spyOn(authProviderService, "login").mockResolvedValue({
      status: "VERIFICATION_REQUIRED",
      email: "asha@example.com",
      destination: "a***a@example.com",
    });
    const onVerify = jest.fn();

    let renderer!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      renderer = TestRenderer.create(
        <LoginScreen
          onAuthenticated={jest.fn()}
          onRegisterPress={jest.fn()}
          onForgotPassword={jest.fn()}
          onVerificationRequired={onVerify}
        />,
      );
    });

    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ placeholder: "Email address" }).props.onChangeText as (v: string) => void)("asha@example.com");
      (renderer.root.findByProps({ placeholder: "Password" }).props.onChangeText as (v: string) => void)("StrongPass123!");
    });

    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ accessibilityRole: "button" }).props.onPress as () => void)();
    });

    expect(onVerify).toHaveBeenCalledWith("asha@example.com");
  });

  it("validates 6-digit code in VerificationScreen", async () => {
    const confirmSpy = jest
      .spyOn(authProviderService, "confirmRegistration")
      .mockResolvedValue(undefined);
    const onVerified = jest.fn();

    let renderer!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      renderer = TestRenderer.create(
        <VerificationScreen
          email="asha@example.com"
          onVerified={onVerified}
          onBackToLogin={jest.fn()}
        />,
      );
    });

    expect(JSON.stringify(renderer.toJSON())).toContain("a***a@example.com");

    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ placeholder: "Verification code" }).props.onChangeText as (v: string) => void)("123456");
    });

    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ accessibilityRole: "button" }).props.onPress as () => void)();
    });

    expect(confirmSpy).toHaveBeenCalledWith({
      email: "asha@example.com",
      code: "123456",
    });
    expect(onVerified).toHaveBeenCalledTimes(1);
  });

  it("completes two-step password recovery in RecoveryScreen", async () => {
    const startSpy = jest
      .spyOn(authProviderService, "startRecovery")
      .mockResolvedValue(undefined);
    const completeSpy = jest
      .spyOn(authProviderService, "completeRecovery")
      .mockResolvedValue(undefined);
    const onComplete = jest.fn();

    let renderer!: { root: TestNode; toJSON: () => unknown };
    await TestRenderer.act(async () => {
      renderer = TestRenderer.create(
        <RecoveryScreen onRecoveryComplete={onComplete} onBackToLogin={jest.fn()} />,
      );
    });

    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ placeholder: "Email address" }).props.onChangeText as (v: string) => void)("asha@example.com");
    });
    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ accessibilityRole: "button" }).props.onPress as () => void)();
    });

    expect(startSpy).toHaveBeenCalledWith({ email: "asha@example.com" });

    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ placeholder: "Recovery code" }).props.onChangeText as (v: string) => void)("654321");
      (renderer.root.findByProps({ placeholder: "New password (min 12 characters)" }).props.onChangeText as (v: string) => void)("NewStrongPass123!");
      (renderer.root.findByProps({ placeholder: "Confirm new password" }).props.onChangeText as (v: string) => void)("NewStrongPass123!");
    });
    await TestRenderer.act(async () => {
      (renderer.root.findByProps({ accessibilityRole: "button" }).props.onPress as () => void)();
    });

    expect(completeSpy).toHaveBeenCalledWith({
      email: "asha@example.com",
      code: "654321",
      newPassword: "NewStrongPass123!",
    });
    expect(onComplete).toHaveBeenCalledTimes(1);
  });
});
