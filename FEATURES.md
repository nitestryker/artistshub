# ArtistHub — Feature Tracker

## Core Features

| # | Feature | Status |
|---|---------|--------|
| 1 | Artwork editing (edit title/description/category after upload) | ✅ Done |
| 2 | Auto-refreshing messages in channels (5s polling) | ✅ Done |
| 3 | Browse Artists / User discovery page (newest + most followed) | ✅ Done |
| 4 | Artwork categories/tags + filter on Explore | ✅ Done |
| 5 | Search (artists + artwork by title/description/bio) | ✅ Done |
| 6 | Notifications (follows, likes, comments, messages) | ✅ Done |
| 7 | Cloudinary/S3 image storage (production persistence) | ⏳ Pending |
| 8 | Password reset (email-based forgot password flow) | ⏳ Pending |
| 13 | Auto Tagging + Art Style Detection (CLIP + ColorThief) | ✅ Done |

## Nice-to-Haves

| # | Feature | Status |
|---|---------|--------|
| 9  | Artist verification badges | ✅ Done |
| 10 | Featured/trending artwork on Explore | ✅ Done |
| 11 | Artwork collections/portfolios | ✅ Done |
| 12 | Direct messaging between artists | ✅ Done |

### Auto Tagging + Art Style Detection
- CLIP model (ViT-B/32) classifies images against 20 art style labels with a 0.2 confidence threshold
- ColorThief extracts up to 5 dominant colors and converts RGB values to human-readable names
- Tags generated asynchronously via AJAX — upload never blocked if AI fails
- CLIP model cached in memory after first load
- Interactive tag pill UI on upload and edit pages (add, remove, custom tags, max 10)
- Tags displayed as badge pills on artwork detail pages
- `tags` TEXT column on `artworks` table; `get_tags()` / `set_tags()` helpers on Artwork model
- New endpoint: `POST /artwork/preview-tags`
- New utility module: `app/utils/tagging.py`
- Future: expand to 100+ styles, add mood detection, similarity search via embeddings

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

### Notifications
- Bell icon in the top navbar (right of search bar) visible to logged-in users
- Red badge shows unread count (capped display at 9+)
- Triggered by: new follower, artwork liked, artwork commented on, new direct message
- Dropdown panel shows up to 20 recent notifications with sender avatar, action text, and timestamp
- Unread notifications highlighted with a subtle accent background and a blue dot indicator
- Clicking a notification navigates to the relevant page (profile, artwork detail, or DM conversation)
- "Mark all read" button clears all unread at once
- Individual notifications marked read on click
- Unread count polls every 30 seconds in the background
- Routes: /notifications/count, /notifications/list, /notifications/mark-read, /notifications/<id>/read
- Database: `notifications` table with recipient_id, sender_id, notif_type, artwork_id (nullable), read, created_at
