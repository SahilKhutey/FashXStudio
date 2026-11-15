/**
 * Amazon Cognito & FashXStudio Mobile Authentication Types.
 */

export interface AuthTokens {
  accessToken: string;
  idToken: string;
  refreshToken?: string;
}

export interface AuthenticatedUser {
  userId: string; // Internal FashXStudio profile UUID
  cognitoSub: string;
  email: string;
  emailVerified: boolean;
}

export interface AuthSession {
  tokens: AuthTokens | null;
  user: AuthenticatedUser | null;
  isValid: boolean;
}

export interface SignUpParams {
  email: string;
  password: string;
}

export interface SignInParams {
  email: string;
  password: string;
}

export interface ConfirmSignUpParams {
  email: string;
  code: string;
}

export interface ResetPasswordParams {
  email: string;
}

export interface ConfirmResetPasswordParams {
  email: string;
  newPassword: string;
  code: string;
}
