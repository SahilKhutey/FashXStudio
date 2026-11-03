# RC-02 — Looks History & Digital Closet Experience

## 1. Looks History (`mobile/app/(tabs)/looks.tsx`)
The Looks screen transforms the try-on job list into a visual gallery:
- **Status Filter Chips**: *All Looks*, *Completed*, *Processing*, *Failed*.
- **Visual Previews**: Cached rendered try-on artifacts with timestamps and status badges.
- **Direct Navigation**: Tapping any card opens the try-on result (`/tryon/[jobId]`).
- **Empty State**: Contextual message encouraging the user to try on looks, with a direct link to `/explore`.

## 2. Digital Closet (`mobile/app/(tabs)/closet.tsx`)
The Closet screen renders the user's permanent fashion collection:
- **Snapshot Persistence**: Renders title, price, and image key saved at the time the user added the garment.
- **Look Badges**: Visual indicator (*✦ Look Saved*) distinguishing rendered try-on looks from catalog saves.
- **Deletion with Confirmation**: Tapping `✕` triggers a native alert dialog (*"Remove from Closet — Are you sure you want to remove this item?"*), preventing accidental data loss.
- **Empty-State Recovery**: Contextual empty state with *"Explore styles"* action navigating to `/explore`.
- **Header Summary**: Displays active count of saved styles and quick *"Add more"* action link.
