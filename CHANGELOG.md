# Changelog

All notable changes to ArtistHub are documented here.

---

## [Unreleased] — 2026-04-10

### Added

#### Channel Moderation & Interaction Overhaul
- **Role badges** — Admin (amber), Moderator (blue), and Donor (gold) badges displayed next to usernames on every message
- **Pinned Messages** — Admins and moderators can pin any message via the hover action bar; pinned messages show an amber left border and 📌 icon in the feed
- **Pinned Messages Sidebar** — Pin icon button in the channel header opens a sidebar listing all pinned messages with author, content, image thumbnail, and who pinned it; live count badge on the button; mods/admins can unpin directly from the panel
- **Members Sidebar** — People icon in the channel header opens a list of every user who has sent a message in the current session with avatar and profile link
- **@ Mention System** — Typing `@` in the compose bar opens a mention picker; with no query it shows recent channel participants; with a query it searches all users platform-wide; keyboard navigation with Arrow Up/Down, Enter, Tab, Escape; click to select; `@username` inserted at cursor with trailing space; mentions render as clickable highlighted links; mentions directed at you appear in your accent colour
- **Slash Command Picker** — Typing `/` opens an autocomplete picker that filters as you type; Tab auto-completes when only one match remains; Escape dismisses
- **Slash Commands** (Admins/Moderators only):
  - `/help` — Prints all available commands as a system message visible only to you
  - `/kick <username> [reason]` — Temporarily expels a user; optional reason displayed in the system notice
  - `/ban <username> [reason]` — Permanently bans a user from the channel
  - `/unban <username>` — Lifts an existing channel ban
  - Unknown commands produce an inline error visible only to you
  - Non-privileged users attempting mod commands see a permission-denied error
- **Per-Message Hover Actions** — Action buttons appear when hovering over any message:
  - Flag (report) icon — any user on messages that are not their own
  - Pin / Unpin — admins and moderators only
  - Delete — admins and moderators only; removes message for everyone with a system notice
  - Quick-kick shortcut (K) — fills the compose bar with `/kick @username`
  - Quick-ban shortcut (B) — fills the compose bar with `/ban @username`
- **System Messages** — Kick, ban, unban, pin, unpin, delete, command errors, and `/help` output all generate colour-coded inline notices in the chat feed:
  - Kick: yellow background
  - Ban: red background
  - Unban: green background
  - Pin / Unpin: blue info style
  - Delete: red error style
  - Command errors and `/help`: blue info style
- **Report a Message** — Flag icon opens a modal to select a reason (spam, inappropriate, harassment, copyright, other) and add optional notes; reports are saved and appear in the admin Reports tab
- **Ban State** — Banned users see a red banner at the top of the channel; the compose bar is disabled with an explanatory placeholder; ban status polled every 30 seconds so unbanning takes effect immediately without a page reload; a toast notification confirms the state change
- `PinnedMessage` model and `pinned_messages` database table — tracks pinned messages per channel with the pinner and timestamp; unique constraint on (channel_id, message_id)
- `MessageReport` model and `message_reports` database table — stores per-message reports with reason, notes, status, and relationships to reporter, message, and channel; unique constraint on (reporter_id, message_id)

#### User Roles
- `is_moderator` Boolean column added to the `users` table (default false)
- `is_donor` Boolean column added to the `users` table (default false)
- `is_privileged()` helper method on `User` returns `True` for admins and moderators
- Auto-migration on startup adds `is_moderator` and `is_donor` to existing databases
- Admin panel role selector updated to include Moderator option alongside User and Admin

#### New Channel API Endpoints
- `POST /channels/<id>/pin/<msg_id>` — Pin a message (mod/admin)
- `POST /channels/<id>/unpin/<msg_id>` — Unpin a message (mod/admin)
- `POST /channels/<id>/delete-message/<msg_id>` — Delete a message (mod/admin)
- `POST /channels/<id>/kick` — Kick a user from the channel (mod/admin)
- `POST /channels/<id>/ban-user` — Ban a user from the channel (mod/admin)
- `POST /channels/<id>/unban-user` — Unban a user from the channel (mod/admin)
- `POST /channels/<id>/report-message/<msg_id>` — Report a message (any authenticated user)
- `GET /channels/mention-search` — Search users for the @ mention picker
- `GET /channels/<id>/check-ban` — Poll ban status for the current user

---

## [2026-04-09]

### Added

#### Notifications System
- Bell icon in the top navbar between the search bar and the Upload button; visible to logged-in users only
- Red badge shows unread count (displayed as "9+" when over 9)
- Unread count refreshes automatically every 30 seconds via background polling
- Clicking the bell opens a dropdown panel showing up to 20 recent notifications
- Notifications triggered by: a user follows you, someone likes your artwork, someone comments on your artwork, you receive a new direct message
- Each notification shows: sender avatar, sender username, action text, and relative timestamp
- Unread notifications highlighted with a subtle accent tint and a blue dot indicator
- Clicking a notification navigates to the relevant page and marks it as read
- "Mark all read" button in the panel header when unread notifications exist
- Self-notifications suppressed
- `notifications` table added to the database
- Routes: `/notifications/count`, `/notifications/list`, `/notifications/mark-read`, `/notifications/<id>/read`
- `migrate_notifications.py` script for adding the table to existing databases

#### Channel Image Sharing
- Users can attach images (jpg, jpeg, png, gif, webp) directly to channel messages
- Photo icon button in the compose bar triggers the file picker
- Live preview appears above the input before sending; X button to clear
- Inline image thumbnails (max height 48px) displayed below message text
- Clicking a thumbnail opens a full-screen lightbox; dismiss by clicking outside, the close button, or pressing Escape
- Image-only messages are valid (no text required when an image is attached)
- Real-time polling (every 5 seconds) renders newly received image messages without a page refresh
- `image_url` column (VARCHAR 500, nullable) added to the `messages` table; auto-migration on startup
- `image_src()` helper method added to the `Message` model

---

## Earlier Versions

### Admin Panel
- Full admin dashboard at `/admin/`
- **Users** — list and search users; ban/unban; change role (user/moderator/admin); delete accounts
- **Channels** — list all channels with message counts; view channel detail including messages and active bans; delete individual messages; ban/unban users from channels; delete channels
- **Reports** — view all reports with status filtering (pending/resolved/dismissed); resolve, dismiss, or delete reported content in one action
- **Analytics** — platform statistics (total users, artworks, messages, channels); 7-day and 30/60/90-day growth trends; top artworks by likes; top channels by message count; top users by artwork count; reports breakdown by category
- **Error Logs** — view the last 200 server error logs capturing method, path, status code, IP address, stack trace, and request body; delete individual logs or clear all

### Artwork Reporting
- Any logged-in user can report artwork using a reason (spam, inappropriate content, harassment, copyright violation, misinformation, other) and optional notes
- Reports saved to the `reports` table and visible in the Admin Reports tab
- Reports include pending/resolved/dismissed status workflow

### Artwork Collections / Portfolios
- Full CRUD: create, edit, delete collections
- "Collect" dropdown on artwork detail pages (only shown when the user has existing collections)
- Add and remove artwork from collections
- Collections grid shown on user profile pages with cover image auto-selected from the first artwork
- Routes: `/collections/`, `/collections/create`, `/collections/<id>`, `/collections/<id>/edit`

### Direct Messaging
- Inbox at `/messages/` with unread count badges per conversation
- Conversation view at `/messages/with/<username>`
- Enter to send; Shift+Enter for a new line
- "Message" button on every other artist's profile
- Read receipts — messages marked as read when the conversation is opened
- Unread count JSON endpoint at `/messages/unread-count`

### Community Channels
- Channel directory at `/channels/` showing name, description, and total message count
- Channel creation restricted to admins
- Real-time message polling every 5 seconds
- Left sidebar listing all channels; active channel highlighted
- Duplicate channel name prevention

### Social Features
- Follow / unfollow with AJAX responses and live follower count updates
- Follower and following counts on profile pages
- Personalized feed showing artwork only from followed artists
- Notification sent to followed user on new follow

### Artwork
- Upload with drag-and-drop preview (jpg, jpeg, png, gif, webp — max 16 MB)
- Cloudinary integration for production image storage and persistence
- 11 categories: Digital Art, Painting, Drawing & Illustration, Photography, Sculpture, Mixed Media, Printmaking, Textile & Fiber, Ceramics, Street Art, Other
- Like / unlike toggle with live count update
- Comments section on artwork detail pages
- Edit title, description, and category post-upload
- Delete (owner or admin)
- Related artworks shown on the detail page by matching category

### Explore & Discovery
- Trending section — top 6 artworks by like count at the top of Explore; hidden automatically when no artwork has any likes
- Category filter on the Explore page
- Full-text search across artists (username, bio) and artwork (title, description)
- Browse Artists page sortable by newest or most followed
- Infinite scroll with Intersection Observer on the feed, explore, and profile pages

### Artist Profiles & Verification
- Profile pages with artwork grid, collections grid, and follower/following stats
- Avatar upload and bio editing in the Settings page
- Verified badge (`is_verified`) shown next to username on profiles, artist cards, and DM conversation views
- Admin-only toggle to grant or revoke verification from any user's profile
- Cloudinary integration for avatar image uploads

### Authentication
- Email/password registration and login
- Remember Me option
- CSRF protection on all forms via Flask-WTF
- Password hashing with Werkzeug
- Session-based auth with Flask-Login

### Donations
- Public donation page per artist at `/donate/<username>`
- One-time payments via Stripe PaymentIntent API
- Recurring subscriptions via Stripe Subscription API
- Stripe API key validation with error handling displayed on the page
