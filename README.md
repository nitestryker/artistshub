# ArtistHub

A social platform built for artists — share your work, build an audience, chat with other creatives, and get support from fans. Think of it as the intersection of a portfolio site, a social feed, and a community chat room.

---

## What It Is

ArtistHub is a full-featured web app where artists can post their work across categories like digital art, painting, photography, sculpture, and more. Visitors can follow artists they love, like and comment on pieces, and browse a curated explore page with trending work. It's self-hostable, open source, and designed to be deployed in minutes.

---

## Features

**Portfolio & Discovery**
- Upload artwork with a title, description, category, and tags
- AI-powered auto-tagging on upload — a CLIP vision model classifies art style and ColorThief extracts dominant color palettes, generating tag suggestions automatically
- Trending section on the Explore page surfaces the most-liked work
- Filter by category: Digital Art, Painting, Photography, Sculpture, Mixed Media, and more
- Full-text search across artwork titles, descriptions, and artist bios
- Artist directory sorted by newest or most followed

**Social**
- Follow / unfollow artists
- Like and comment on any piece
- Real-time notification bell — follows, likes, comments, and messages all show up without a page refresh
- Verified artist badges (admin-assigned)
- Personal feed that surfaces work from people you follow

**Collections**
- Curate your own named collections from any artwork on the platform
- Collections appear on your profile as a portfolio grid
- Add or remove pieces anytime

**Community Channels**
- Discord-style public text channels with image support
- Live-updating messages (polling every 5 seconds, no page reload needed)
- @mention autocomplete pulls from recent channel participants
- Moderator tools: pin messages, delete messages, kick and ban users per-channel
- Report any message directly from the chat

**Direct Messages**
- Private conversations between any two users
- Unread count badge in the nav, read receipts when a conversation is opened
- Shift+Enter for new lines, Enter to send

**Artist Support (Donations)**
- Each artist gets their own donation page at `/donate/<username>`
- Stripe-powered one-time payments and recurring subscriptions
- Donors get a badge on their profile

**Admin Dashboard**
- User management: ban, unban, change roles, delete accounts
- Channel management: create channels, view message history, manage bans
- Reports queue with resolve / dismiss / delete-content actions
- Analytics dashboard: user growth, artwork uploads, chat activity, top contributors, art medium breakdown — all with date range filters
- Error log viewer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python / Flask |
| Database | PostgreSQL (Supabase) |
| ORM | SQLAlchemy + Flask-Migrate |
| Auth | Flask-Login (session-based) |
| Image Storage | Cloudinary |
| Payments | Stripe |
| AI Tagging | CLIP ViT-B/32 + ColorThief |
| Deployment | Render (included `render.yaml`) |

---

## Running It Yourself

### Prerequisites

- Python 3.11+
- A PostgreSQL database (Supabase free tier works great)
- A Cloudinary account (free tier is fine)
- Stripe account (optional — only needed if you want donations)

### 1. Clone and install

```bash
git clone https://github.com/your-username/artistshub.git
cd artistshub
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-secret-key-here

# Cloudinary — required for image uploads
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Stripe — optional, only needed for donations
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Set up the database

If you're using Supabase, run the migration file found at `supabase/migrations/` in the Supabase SQL editor. Otherwise, Flask-Migrate handles everything:

```bash
flask db upgrade
```

### 4. Run

```bash
python run.py
```

The app will be available at `http://localhost:5000`. The first user you register can be manually promoted to admin by setting `is_admin = true` in the database.

---

## Deploying to Render

A `render.yaml` is included. Connect your GitHub repo to Render, set the environment variables listed above in the Render dashboard, and it deploys automatically. The included config runs 2 Gunicorn workers.

---

## Making Yourself an Admin

After registering your account, run this against your database:

```sql
UPDATE users SET is_admin = true WHERE username = 'your-username';
```

Admins can then create channels, manage users, and access the full dashboard at `/admin`.

---

## Project Structure

```
artistshub/
├── app/
│   ├── admin/          # Admin dashboard and moderation tools
│   ├── artwork/        # Upload, edit, like, comment
│   ├── auth/           # Login and registration
│   ├── channels/       # Community chat channels
│   ├── collections/    # User-curated portfolios
│   ├── dm/             # Direct messages
│   ├── donate/         # Stripe donation pages
│   ├── main/           # Home feed, explore, search, profiles
│   ├── notifications/  # Activity notification system
│   ├── social/         # Follow/unfollow
│   ├── templates/      # Jinja2 HTML templates
│   └── utils/
│       ├── cloudinary_upload.py
│       └── tagging.py  # CLIP + ColorThief AI tagging
├── config.py
├── run.py
├── requirements.txt
└── render.yaml
```

---

## License

MIT — do whatever you want with it.
