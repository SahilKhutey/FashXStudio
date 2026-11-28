# Physical Device Test Plan

Target devices: at least one physical Android device (Android 13+) and one physical iOS device (iOS 16+) running EAS preview/staging builds.

1. **Cold Launch & Auth**: Register new account, verify email, force-close app, relaunch to confirm session persistence, and test logout + second-account login isolation.
2. **Onboarding**: Complete privacy/consent, profile details, and optional measurements; kill app mid-flow and verify saved profile state on relaunch.
3. **Feed & Explore**: Search catalog, apply category/price/size filters, scroll pagination, toggle airplane mode to verify `NetworkStatusBanner` and retry.
4. **PDP & Size Chart**: Open product from Search, verify single-merchant offer price/availability, inspect size chart.
5. **Camera & VTO**: Deny camera permission once (verify settings fallback), grant permission, capture photo, preview, upload, submit VTO job, background app during processing, resume, and inspect result + simulation notice.
6. **Closet & Saved Looks**: Save product and VTO result, create a Saved Look, delete an item, and verify persistence on second device/reinstall.
7. **Merchant Redirect**: Tap outbound merchant CTA and verify HTTPS browser handoff.
8. **Accessibility**: Walk key flows with TalkBack (Android) and VoiceOver (iOS).
