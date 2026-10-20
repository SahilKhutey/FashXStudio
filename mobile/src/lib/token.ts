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
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token;
}
