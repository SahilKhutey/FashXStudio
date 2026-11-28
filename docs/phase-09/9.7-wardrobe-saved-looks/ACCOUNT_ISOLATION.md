# Account Isolation

- `wardrobeKeys.items(userId)` and `wardrobeKeys.looks(userId)` scope TanStack Query caches per authenticated user.
- `performAppLogout()` (`mobile/src/auth/logout.ts`) cancels/clears `queryClient` on logout, and `create_saved_look_for_user` enforces server-side `user_id` ownership.
