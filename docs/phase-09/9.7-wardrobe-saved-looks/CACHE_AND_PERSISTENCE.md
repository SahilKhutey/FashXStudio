# Cache and Persistence

- Backend is the source of truth; wardrobe state is not persisted in `AsyncStorage` or Zustand persistence.
- `wardrobeKeys` scopes queries by `userId`.
