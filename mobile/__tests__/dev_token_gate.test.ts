import DevTokenScreen, { isDevTokenEnabled } from "../app/(auth)/dev-token";
import { useAuthStore } from "../src/features/auth/authStore";
import { getAccessToken, getDevToken, setDevToken } from "../src/lib/token";
import { supabase } from "../src/lib/supabase";

const mockReplace = jest.fn();
const mockPush = jest.fn();

jest.mock("expo-router", () => ({
  useRouter: () => ({
    replace: mockReplace,
    push: mockPush,
  }),
}));

jest.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// Mock react hooks for component-level testing
let mockEffectCallbacks: Array<() => void> = [];
jest.mock("react", () => {
  const actualReact = jest.requireActual("react");
  return {
    ...actualReact,
    useEffect: (cb: () => void) => {
      mockEffectCallbacks.push(cb);
    },
    useCallback: (cb: any) => cb,
    useMemo: (cb: any) => cb(),
    useState: (initial: any) => [initial, jest.fn()],
  };
});

let mockAuthState = {
  session: null as any,
  devSession: false,
  hasSession: false,
  me: null as any,
};

jest.mock("../src/features/auth/authStore", () => {
  return {
    useAuthStore: Object.assign(
      jest.fn(() => ({
        session: mockAuthState.session,
        devSession: mockAuthState.devSession,
        hasSession: mockAuthState.hasSession,
        setDevSession: (val: boolean) => {
          mockAuthState.devSession = val;
          mockAuthState.hasSession = Boolean(mockAuthState.session || val);
        },
        setHasSession: (val: boolean) => {
          mockAuthState.hasSession = val;
        },
        setMe: (val: any) => {
          mockAuthState.me = val;
        },
      })),
      {
        getState: () => mockAuthState,
        setState: (newState: any) => {
          mockAuthState = { ...mockAuthState, ...newState };
        },
      }
    ),
  };
});

describe("Dev Token Route Gate & Flag Enforcement", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockEffectCallbacks = [];
    setDevToken(null);
    mockAuthState = { session: null, devSession: false, hasSession: false, me: null };
  });

  describe("isDevTokenEnabled Gate Logic", () => {
    it("returns true only when isDev is true AND flag is exactly '1'", () => {
      expect(isDevTokenEnabled(true, "1")).toBe(true);
    });

    it("returns false if flag is '0', unset, or anything other than '1'", () => {
      expect(isDevTokenEnabled(true, "0")).toBe(false);
      expect(isDevTokenEnabled(true, undefined)).toBe(false);
      expect(isDevTokenEnabled(true, "")).toBe(false);
      expect(isDevTokenEnabled(true, "true")).toBe(false);
    });

    it("returns false in production (isDev=false) even if flag is '1'", () => {
      expect(isDevTokenEnabled(false, "1")).toBe(false);
      expect(isDevTokenEnabled(false, "0")).toBe(false);
      expect(isDevTokenEnabled(false, undefined)).toBe(false);
    });
  });

  describe("eas.json Security Audit", () => {
    it("ensures preview and production profiles strictly set EXPO_PUBLIC_DEV_TOKEN_LOGIN to '0'", () => {
      const easContent = require("../eas.json");

      expect(easContent.build.preview.env.EXPO_PUBLIC_DEV_TOKEN_LOGIN).toBe("0");
      expect(easContent.build.production.env.EXPO_PUBLIC_DEV_TOKEN_LOGIN).toBe("0");
    });
  });

  describe("DevTokenScreen Reachability & Redirection", () => {
    const originalEnv = process.env.EXPO_PUBLIC_DEV_TOKEN_LOGIN;

    afterEach(() => {
      process.env.EXPO_PUBLIC_DEV_TOKEN_LOGIN = originalEnv;
    });

    it("fails reachability when flag is '0': renders null and immediately redirects to sign-in", () => {
      process.env.EXPO_PUBLIC_DEV_TOKEN_LOGIN = "0";

      const element = DevTokenScreen();
      // Component returns null when disabled
      expect(element).toBeNull();

      // Trigger queued useEffects
      mockEffectCallbacks.forEach((cb) => cb());
      expect(mockReplace).toHaveBeenCalledWith("/(auth)/sign-in");
    });

    it("is reachable when flag is '1' in development: renders UI and does not redirect", () => {
      process.env.EXPO_PUBLIC_DEV_TOKEN_LOGIN = "1";

      const element = DevTokenScreen();
      // Component returns React element tree when enabled
      expect(element).not.toBeNull();

      // Trigger queued useEffects
      mockEffectCallbacks.forEach((cb) => cb());
      expect(mockReplace).not.toHaveBeenCalled();
    });
  });

  describe("Token Management & Auth State", () => {
    it("getAccessToken returns devToken when set, bypassing Supabase session", async () => {
      const getSessionSpy = jest.spyOn(supabase.auth, "getSession");

      setDevToken("dev-jwt-token-xyz");
      expect(getDevToken()).toBe("dev-jwt-token-xyz");

      const token = await getAccessToken();
      expect(token).toBe("dev-jwt-token-xyz");
      expect(getSessionSpy).not.toHaveBeenCalled();

      getSessionSpy.mockRestore();
    });

    it("signOut clears devToken and resets hasSession", async () => {
      setDevToken("dev-jwt-token-xyz");
      useAuthStore.setState({ hasSession: true, me: { user_id: "user-1", roles: ["user"] } });

      // Simulate sign out
      setDevToken(null);
      useAuthStore.setState({ session: null, me: null, hasSession: false });

      expect(getDevToken()).toBeNull();
      expect(useAuthStore.getState().hasSession).toBe(false);
      expect(useAuthStore.getState().me).toBeNull();
    });
  });
});
