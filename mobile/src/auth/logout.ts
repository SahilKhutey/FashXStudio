import { queryClient } from "../app-shell/queryClient";
import { useAuthStore as useFeatureAuthStore } from "../features/auth/authStore";
import { useAppStore } from "../stores/app.store";
import { authProviderService } from "./auth.instance";
import { AuthError } from "./auth.errors";
import { purgeLocalSession } from "./session";
import { useAuthStore as useUiAuthStore } from "./stores/authStore";

let logoutPromise: Promise<void> | null = null;

export async function initializeAuthSession(): Promise<void> {
  const uiStore = useUiAuthStore.getState();
  uiStore.setLoading(true);
  uiStore.clearError();

  try {
    const session = await authProviderService.getCurrentSession();
    if (!session) {
      uiStore.setUnauthenticated();
      return;
    }
    uiStore.setAuthenticated(session.user.subject);
  } catch (err) {
    if (err instanceof AuthError && err.retryable) {
      uiStore.setUnauthenticated(authProviderService.getUserMessage(err));
      return;
    }
    uiStore.setUnauthenticated();
  }
}

export function performAppLogout(): Promise<void> {
  if (logoutPromise) {
    return logoutPromise;
  }

  logoutPromise = runLogout().finally(() => {
    logoutPromise = null;
  });
  return logoutPromise;
}

async function runLogout(): Promise<void> {
  try {
    await authProviderService.logout();
  } catch {
    // Local session cleanup must still proceed offline or on remote error.
  } finally {
    await purgeLocalSession();
    queryClient.clear();
    useAppStore.getState().reset();
    try {
      await useFeatureAuthStore.getState().signOut();
    } catch {
      // Feature auth store reset best-effort
    }
    useUiAuthStore.getState().setUnauthenticated();
  }
}
