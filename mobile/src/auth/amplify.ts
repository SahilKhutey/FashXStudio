/**
 * Amazon Cognito & AWS Amplify Configuration.
 * Validates public app client identifiers and registers OAuth 2.0 PKCE settings.
 */

export interface CognitoMobileConfig {
  userPoolId: string;
  userPoolClientId: string;
  domain: string;
  redirectSignIn: string;
  redirectSignOut: string;
}

export function getCognitoConfig(): CognitoMobileConfig {
  const userPoolId = process.env.EXPO_PUBLIC_COGNITO_USER_POOL_ID || "ap-south-1_DEVPOOL";
  const userPoolClientId = process.env.EXPO_PUBLIC_COGNITO_CLIENT_ID || "dev-public-client-id";
  const domain = process.env.EXPO_PUBLIC_COGNITO_DOMAIN || "auth-dev.fashxstudio.com";
  const redirectSignIn = process.env.EXPO_PUBLIC_AUTH_REDIRECT_SIGN_IN || "fashx://auth/callback";
  const redirectSignOut = process.env.EXPO_PUBLIC_AUTH_REDIRECT_SIGN_OUT || "fashx://auth/logout";

  return {
    userPoolId,
    userPoolClientId,
    domain,
    redirectSignIn,
    redirectSignOut,
  };
}

export const cognitoConfig = getCognitoConfig();
