# App Lifecycle and Recovery

- `useAppLifecycle` (`mobile/src/hooks/useAppLifecycle.ts`) tracks `AppState` transitions (`onForeground`, `onBackground`, `onInactive`) so active VTO polling and camera sessions pause/resume cleanly.
