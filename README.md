<div align="center">

<br />

```
 █████╗ ██████╗ ████████╗██╗███████╗████████╗███████╗██╗  ██╗██╗   ██╗██████╗ 
██╔══██╗██╔══██╗╚══██╔══╝██║██╔════╝╚══██╔══╝██╔════╝██║  ██║██║   ██║██╔══██╗
███████║██████╔╝   ██║   ██║███████╗   ██║   ███████╗███████║██║   ██║██████╔╝
██╔══██║██╔══██╗   ██║   ██║╚════██║   ██║   ╚════██║██╔══██║██║   ██║██╔══██╗
██║  ██║██║  ██║   ██║   ██║███████║   ██║   ███████║██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ 
```

**A social platform where artists share work, build audiences, and find their community.**

<br />

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Cloudinary](https://img.shields.io/badge/Images-Cloudinary-3448C5?style=flat-square&logo=cloudinary&logoColor=white)](https://cloudinary.com)
[![Stripe](https://img.shields.io/badge/Payments-Stripe-635BFF?style=flat-square&logo=stripe&logoColor=white)](https://stripe.com)
[![Deploy on Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=flat-square&logo=render&logoColor=white)](https://render.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

<br />

</div>

---

<br />

## What is ArtistHub?

ArtistHub is a full-featured social platform built for artists — a place to post work, grow a following, chat with other creatives in real-time, and accept donations from fans. It combines the portfolio features of Behance, the social layer of Instagram, and the community feel of Discord into a single self-hostable app.

Upload a painting, get AI-generated style tags, collect likes and comments, and chat with your followers — all without leaving the platform.

<br />

---

<br />

## Feature Overview

<br />

### Gallery & Portfolio

Artists get a full profile page with their work in a masonry grid. Every piece supports a title, description, category, and tags — with an AI tagging system (CLIP vision model + ColorThief) that analyzes images on upload and suggests art style labels and dominant color names automatically. Collections let artists curate named portfolios grouped into a grid on their profile.

<br />

### Explore & Discovery

| | Feature | Detail |
|---|---|---|
| **⟡** | Trending row | Top 6 most-liked artworks surfaced at the top of Explore |
| **⟡** | Category filter | Digital Art · Painting · Photography · Sculpture · Mixed Media · Street Art · and more |
| **⟡** | Artist directory | Browse all artists sorted by newest or most followed |
| **⟡** | Full-text search | Searches artwork titles, descriptions, and artist bios simultaneously |
| **⟡** | Infinite scroll | Feed, Explore, and profiles all paginate via AJAX — no page reloads |

<br />

### Social Layer

Follow artists, like artwork, leave comments. A notification bell tracks all activity — new followers, likes, comments, and direct messages — with a live unread count polling every 30 seconds. Verified artist badges are admin-assignable.

<br />

### Community Channels

Public chat channels with a feel close to Discord. Messages update live every 5 seconds. Images can be attached to any message. Moderators get a full toolkit:

```
pin messages      → stays pinned at the top of the channel for all users
delete messages   → removed instantly via an in-memory sync registry  
kick users        → session-level removal with an optional reason
ban users         → permanent channel ban, manageable from admin panel
@mention          → autocomplete pulls from recent channel participants
report messages   → notifies all admins immediately
```

<br />

### Direct Messages

Private one-to-one conversations between any two users. Enter to send, Shift+Enter for a new line. Read receipts mark messages as seen when a conversation is opened. Unread counts appear in the nav.

<br />

### Donations via Stripe

Every artist gets a personal donation page at `/donate/username`. Fans can make one-time payments or set up recurring subscriptions. Donors receive a profile badge. Stripe payment intents, subscriptions, and webhooks are fully wired.

<br />

### Admin Dashboard

```
/admin/users      →  search · ban/unban · change roles · delete accounts
/admin/channels   →  create channels · view history · manage bans
/admin/reports    →  review flagged content · resolve or dismiss
/admin/analytics  →  growth charts · top artwork · art medium breakdown
/admin/error-logs →  server error viewer with clear/delete
```

<br />

---

<br />

## Stack

```
Backend          Flask  (Python 3.11)
Database         PostgreSQL via Supabase
ORM              SQLAlchemy + Flask-Migrate
Auth             Flask-Login · bcrypt password hashing · session-based
Images           Cloudinary  (CDN-backed, persistent storage)
Payments         Stripe  (one-time donations + recurring subscriptions)
AI Tagging       CLIP ViT-B/32 (style classification) + ColorThief (color palette)
Forms            Flask-WTF with CSRF protection
Deployment       Render  (render.yaml included)
```

<br />

---

<br />

## Getting Started

### Prerequisites

- Python 3.11+
- A PostgreSQL database — [Supabase](https://supabase.com) free tier works perfectly
- A [Cloudinary](https://cloudinary.com) account for image hosting
- A [Stripe](https://stripe.com) account if you want donations enabled

<br />

### 1 — Clone and install

```bash
git clone https://github.com/your-username/artistshub.git
cd artistshub
pip install -r requirements.txt
```

<br />

### 2 — Configure environment

Create a `.env` file in the project root:

```env
# Required
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=a-long-random-secret-key

# Required for image uploads
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Optional — only needed for donation pages
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

<br />

### 3 — Set up the database

**Using Supabase?** Run the migration file in your Supabase SQL editor:

```
supabase/migrations/20260409185033_create_all_app_tables.sql
```

**Using your own Postgres?** Flask-Migrate handles it:

```bash
flask db upgrade
```

<br />

### 4 — Run

```bash
python run.py
```

Visit `http://localhost:5000`. Register your account, then promote yourself to admin directly in the database:

```sql
UPDATE users SET is_admin = true WHERE username = 'your-username';
```

From there you can create channels and manage everything from `/admin`.

<br />

---

<br />

## Deploying to Render

A `render.yaml` is included in the repo. Connect your GitHub repository in the [Render dashboard](https://render.com), set the environment variables above, and it deploys automatically. The config runs two Gunicorn workers on the free plan.

<br />

---

<br />

## Project Structure

```
artistshub/
│
├── app/
│   ├── admin/              Dashboard, analytics, moderation tools
│   ├── artwork/            Upload, edit, like, comment, AI tag preview
│   ├── auth/               Login and registration
│   ├── channels/           Real-time community chat
│   ├── collections/        Curated artwork portfolios
│   ├── dm/                 Private direct messaging
│   ├── donate/             Stripe-powered artist donation pages
│   ├── main/               Home feed, explore, search, profiles, settings
│   ├── notifications/      Activity notification system
│   ├── social/             Follow / unfollow
│   ├── templates/          Jinja2 HTML templates
│   └── utils/
│       ├── cloudinary_upload.py
│       └── tagging.py      CLIP + ColorThief AI pipeline
│
├── supabase/
│   └── migrations/         Full SQL schema for Supabase setup
│
├── config.py
├── run.py
├── requirements.txt
└── render.yaml             One-click Render deployment config
```

<br />

---

<br />

## AI Auto-Tagging

When artwork is uploaded, ArtistHub runs two models against the image before the form is submitted:

**CLIP ViT-B/32** classifies the image against 20 art style labels with a 0.2 confidence threshold — detecting styles like impressionism, concept art, pixel art, watercolor, and street art.

**ColorThief** extracts up to 5 dominant colors from the image and maps RGB values to human-readable color names like *dusty rose* or *slate blue*.

Tag suggestions arrive via a `POST /artwork/preview-tags` AJAX call — the upload is never blocked if the AI step fails. Artists can accept, remove, or add their own tags up to a maximum of 10. The CLIP model is cached in memory after first load, so subsequent uploads are fast.

<br />

---

<br />

## Roadmap

```
[ ]  Password reset via email
[ ]  WebSocket-based real-time chat  (replace polling)
[ ]  Expanded CLIP label set  (100+ styles)
[ ]  Mood and subject detection via embeddings
[ ]  Artwork similarity search
```

<br />

---

<br />

<div align="center">

Built for artists, by artist who wanted something better to exist.

**MIT License** · contributions welcome

<br />

</div>
