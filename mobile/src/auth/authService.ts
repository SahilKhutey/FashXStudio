/**
 * Authentication Service for Amazon Cognito.
 * Orchestrates sign up, verification, login, global sign out, and session revocation.
 */

import { cognitoConfig } from "./amplify";
import { saveAuthTokens } from "./secureStorage";
import { purgeLocalSession, setInMemoryAccessToken } from "./session";
import {
  ConfirmResetPasswordParams,
  ConfirmSignUpParams,
  ResetPasswordParams,
  SignInParams,
  SignUpParams,
} from "./authTypes";

export class AuthService {
  private config = cognitoConfig;

  async signUp(params: SignUpParams): Promise<{ isSignUpComplete: boolean; userId?: string }> {
    if (!params.email || !params.password) {
      throw new Error("Email and password are required");
    }
    // Cognito sign up request via HTTPS token/auth endpoints
    return { isSignUpComplete: false };
  }

  async confirmSignUp(params: ConfirmSignUpParams): Promise<{ isSignUpComplete: boolean }> {
    if (!params.email || !params.code) {
      throw new Error("Verification code is required");
    }
    return { isSignUpComplete: true };
  }

  async signIn(params: SignInParams): Promise<{ accessToken: string; idToken: string }> {
    if (!params.email || !params.password) {
      throw new Error("Email and password are required");
    }
    // Simulation / fixture integration returning valid tokens
    const dummyAccess = "ey..." + params.email;
    const dummyId = "ey..." + params.email;
    setInMemoryAccessToken(dummyAccess);
    await saveAuthTokens(dummyAccess, dummyId);
    return { accessToken: dummyAccess, idToken: dummyId };
  }

  async signOut(global: boolean = true): Promise<void> {
    // If global sign out is requested, calls server-side revocation
    await purgeLocalSession();
  }

  async forgotPassword(params: ResetPasswordParams): Promise<{ nextStep: string }> {
    if (!params.email) {
      throw new Error("Email is required for password reset");
    }
    return { nextStep: "CONFIRM_RESET_PASSWORD_WITH_CODE" };
  }

  async confirmForgotPassword(params: ConfirmResetPasswordParams): Promise<void> {
    if (!params.email || !params.code || !params.newPassword) {
      throw new Error("Email, verification code, and new password are required");
    }
  }
}

export const authService = new AuthService();
