# Item Removal Policy

- `ClosetScreen` (`mobile/app/(tabs)/closet.tsx`) prompts confirmation before `useRemoveFromWardrobe` (`DELETE /wardrobe/items/{itemId}`), preventing duplicate taps via `removingId`.
- Deleting a wardrobe item does not delete underlying merchant products or VTO assets.
