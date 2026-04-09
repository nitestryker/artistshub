# Changelog

All notable changes to ArtistHub are documented here.

---

## [Unreleased] — 2026-04-09

### Added

#### Channel Image Sharing
- Users can now attach images (jpg, jpeg, png, gif, webp) directly to channel messages
- Image attach button (photo icon) added to the left of the message compose bar
- Live preview of the selected image appears above the input before sending — can be cleared with an X button
- Messages with images display a compact thumbnail (max height 48px) inline below any text content
- Clicking a thumbnail opens a full-screen lightbox overlay with a dark backdrop
- Lightbox can be dismissed by clicking outside the image, clicking the close button, or pressing Escape
- Image-only messages are valid (no text required when an image is attached)
- Real-time message polling (every 5 seconds) renders newly received image messages from other users without a page refresh
- Hidden file input used for clean, accessible image selection
- Image files saved to `app/static/uploads/` with a unique filename pattern (`msg_{user_id}_{timestamp}.{ext}`)

#### Database
- `image_url` column (VARCHAR 500, nullable) added to the `messages` table
- `content` column on `messages` changed to allow empty strings (was previously NOT NULL) to support image-only messages
- Auto-migration runs on application startup to safely add `image_url` to existing databases that do not yet have it
- `image_src()` helper method added to the `Message` model — returns the resolved image URL or `None`

#### Backend
- `MessageForm` updated to include an optional `FileField` with image-type validation
- Channel `view` route updated to accept `multipart/form-data` for file uploads
- Channel `messages_json` polling endpoint updated to include `image_src` in the JSON response payload
- `_run_migrations()` function added to `app/__init__.py` — executes on every app start to apply any pending schema changes safely

---

## Earlier Versions

### Artwork Collections / Portfolios
- Full CRUD for collections: create, edit, delete
- Collect dropdown on artwork detail pages
- Collections grid shown on user profile pages
- Cover image auto-selected from the first artwork in each collection
- Routes: `/collections/`, `/collections/create`, `/collections/<id>`, `/collections/<id>/edit`

### Direct Messaging
- Inbox at `/messages/` with unread count badges
- Conversation view at `/messages/with/<username>`
- Enter key sends; Shift+Enter adds a new line
- Message button on every other artist's profile
- Read receipts — messages marked as read when conversation is opened
- Unread count JSON endpoint at `/messages/unread-count`

### Community Channels
- Channel directory at `/channels/`
- Create channels with name and description
- Real-time message polling every 5 seconds
- Duplicate channel name prevention

### Social Features
- Follow / unfollow system with AJAX responses
- Follower and following counts on profiles
- Personalized feed showing artwork from followed artists

### Artwork
- Upload with drag-and-drop preview (jpg, jpeg, png, gif, webp — max 16 MB)
- 11 categories: Digital Art, Painting, Drawing & Illustration, Photography, Sculpture, Mixed Media, Printmaking, Textile & Fiber, Ceramics, Street Art, Other
- Like / unlike toggle with live count
- Comments
- Edit title, description, and category
- Delete (owner or admin)

### Explore & Discovery
- Trending section — top 6 artworks by like count
- Category filtering on Explore page
- Full-text search for artists and artwork
- Browse Artists page sortable by newest or most followed
- Infinite scroll with Intersection Observer on feed, explore, and profiles

### Artist Profiles & Verification
- Profile pages with artwork grid, collections, follower/following stats
- Avatar upload and bio editing in Settings
- Verified badge (`is_verified`) shown next to username
- Admin-only toggle to grant/revoke verification

### Authentication
- Email/password registration and login
- Remember Me option
- CSRF protection on all forms via Flask-WTF
- Password hashing with Werkzeug

### Donations
- Public donation page per artist at `/donate/<username>`
- One-time and recurring (subscription) payments via Stripe
- Stripe API key validation with error handling
