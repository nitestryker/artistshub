# ArtistHub — Feature Tracker

## Core Features

| # | Feature | Status |
|---|---------|--------|
| 1 | Artwork editing (edit title/description/category after upload) | ✅ Done |
| 2 | Auto-refreshing messages in channels (5s polling) | ✅ Done |
| 3 | Browse Artists / User discovery page (newest + most followed) | ✅ Done |
| 4 | Artwork categories/tags + filter on Explore | ✅ Done |
| 5 | Search (artists + artwork by title/description/bio) | ✅ Done |
| 6 | Notifications (follows, likes, comments) | ⏳ Pending |
| 7 | Cloudinary/S3 image storage (production persistence) | ⏳ Pending |
| 8 | Password reset (email-based forgot password flow) | ⏳ Pending |

## Nice-to-Haves

| # | Feature | Status |
|---|---------|--------|
| 9  | Artist verification badges | ✅ Done |
| 10 | Featured/trending artwork on Explore | ✅ Done |
| 11 | Artwork collections/portfolios | ✅ Done |
| 12 | Direct messaging between artists | ✅ Done |

## Notes

### Verification Badges
- `is_verified` Boolean on User model
- Blue checkmark shown next to username on profiles, DM inbox/conversation, artist cards
- Admin-only toggle button on any user profile (visible only to `is_admin` users)

### Trending on Explore
- Top 6 artworks ordered by total like count shown in a row at the top of Explore
- Lightning bolt badge on each trending piece
- Hidden automatically when no artwork has any likes yet

### Collections / Portfolios
- Full CRUD: create, edit, delete
- "Collect" dropdown on any artwork detail page (only shown to users with existing collections)
- Collections grid shown on profile pages
- Add/remove artwork from collections
- Cover image auto-selected from first artwork in collection
- Routes: /collections/, /collections/create, /collections/<id>, /collections/<id>/edit

### Direct Messaging
- Inbox at /messages/ with unread count badges
- Conversation at /messages/with/<username>
- Enter key sends (Shift+Enter for new line)
- "Message" button on every other artist's profile
- "Messages" and "Collections" links added to user dropdown nav
- Read receipts (mark as read when conversation opened)
