import { ExpoConfig, ConfigContext } from "expo/config";

const APP_ENV = process.env.APP_ENV ?? process.env.EXPO_PUBLIC_APP_ENV ?? "development";

const IDENTIFIERS = {
  development: {
    name: "FashX Dev",
    android: "com.fashxstudio.app.dev",
    ios: "com.fashxstudio.app.dev",
  },
  staging: {
    name: "FashX Staging",
    android: "com.fashxstudio.app.staging",
    ios: "com.fashxstudio.app.staging",
  },
  production: {
    name: "FashX",
    android: "com.fashxstudio.app",
    ios: "com.fashxstudio.app",
  },
} as const;

if (!(APP_ENV in IDENTIFIERS)) {
  throw new Error(`Unknown APP_ENV: ${APP_ENV}`);
}

const selected = IDENTIFIERS[APP_ENV as keyof typeof IDENTIFIERS];

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: selected.name,
  slug: "fashx",
  scheme: "fashx",
  version: "0.1.0",
  orientation: "portrait",
  userInterfaceStyle: "automatic",
  runtimeVersion: { policy: "appVersion" },
  ios: {
    bundleIdentifier: selected.ios,
    supportsTablet: true,
    infoPlist: {
      NSCameraUsageDescription:
        "FashX uses the camera so you can take the photo used for virtual try-on. Photos are only used with your consent.",
    },
  },
  android: {
    package: selected.android,
    permissions: ["android.permission.CAMERA"],
    blockedPermissions: ["android.permission.RECORD_AUDIO"],
    allowBackup: false,
    softwareKeyboardLayoutMode: "resize",
  },
  plugins: [
    "expo-router",
    "expo-image",
    "expo-secure-store",
    [
      "expo-camera",
      {
        cameraPermission:
          "FashX uses the camera so you can take the photo used for virtual try-on.",
        recordAudioAndroid: false,
      },
    ],
    [
      "expo-image-picker",
      {
        photosPermission: false,
      },
    ],
  ],
  experiments: {
    typedRoutes: true,
  },
  extra: {
    appEnv: APP_ENV,
    apiUrl: process.env.EXPO_PUBLIC_API_BASE_URL ?? process.env.EXPO_PUBLIC_API_URL,
    supabaseUrl: process.env.EXPO_PUBLIC_SUPABASE_URL,
    supabaseAnonKey: process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  },
});
