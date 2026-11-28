# Android Back Navigation

- `useAndroidBackHandler(enabled, onBack)` (`mobile/src/hooks/useAndroidBackHandler.ts`) subscribes to `BackHandler.addEventListener("hardwareBackPress")` on Android only when enabled (modals/camera previews), delegating standard stack pops to Expo Router.
