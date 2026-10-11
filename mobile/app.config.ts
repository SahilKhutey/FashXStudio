import { ExpoConfig, ConfigContext } from "expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "FashX",
  slug: "fashx",
  scheme: "fashx",
  version: "0.1.0",
  orientation: "portrait",
  userInterfaceStyle: "automatic",
  runtimeVersion: { policy: "appVersion" },
  ios: {
    bundleIdentifier: "com.fashxstudio.app",
    infoPlist: {
      NSCameraUsageDescription:
        "FashX uses the camera so you can take the photo used for virtual try-on. Photos are only used with your consent.",
    },
  },
  android: {
    package: "com.fashxstudio.app",
    permissions: ["CAMERA"],
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
      },
    ],
  ],
  experiments: {
    typedRoutes: true,
  },
  extra: {
    apiUrl: process.env.EXPO_PUBLIC_API_URL,
    supabaseUrl: process.env.EXPO_PUBLIC_SUPABASE_URL,
    supabaseAnonKey: process.env.EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
  },
});
