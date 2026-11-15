import { getValidAccessToken as getCognitoAccessToken } from "../auth/session";
import { supabase } from "./supabase";

let devToken: string | null = null;

export const setDevToken = (t: string | null): void => {
  devToken = t;
};

export const getDevToken = (): string | null => {
  return devToken;
};

export async function getAccessToken(): Promise<string | undefined> {
  if (devToken) return devToken;

  const cognitoToken = await getCognitoAccessToken();
  if (cognitoToken) return cognitoToken;

  try {
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token;
  } catch {
    return undefined;
  }
}
