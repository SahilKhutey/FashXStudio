# 10 — Application Identifiers

## Environment-Scoped Identifiers (`mobile/app.config.ts`)
| Environment (`APP_ENV`) | App Name | Android `package` | iOS `bundleIdentifier` |
| :--- | :--- | :--- | :--- |
| `development` | `FashX Dev` | `com.fashxstudio.app.dev` | `com.fashxstudio.app.dev` |
| `staging` | `FashX Staging` | `com.fashxstudio.app.staging` | `com.fashxstudio.app.staging` |
| `production` | `FashX` | `com.fashxstudio.app` | `com.fashxstudio.app` |

## Verification
- `APP_ENV=staging npx expo config --type public` verified `name: 'FashX Staging'`, `ios.bundleIdentifier: 'com.fashxstudio.app.staging'`, `android.package: 'com.fashxstudio.app.staging'`, and `extra.appEnv: 'staging'`.
