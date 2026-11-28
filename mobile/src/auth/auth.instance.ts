import { supabaseAuthProvider } from "./adapters/supabase/supabase.provider";
import { ProviderAuthService } from "./auth.service";

export const authProviderService = new ProviderAuthService(supabaseAuthProvider);
