# X AutoPilot — Combo Chain Blast / Deste

Included: all three original videos, both exact tweet texts, and a Python X API publisher. No AI is used.

## Schedule (Europe/Istanbul)

- 18:00 Combo video 1
- 18:30 Deste
- 19:00 Combo video 2
- 19:30 Deste
- Repeat every two hours, 24/7, including across midnight.

**Warning:** Repeating the same two texts and three videos 48 times daily can violate X's spam/duplicate content policies. This project is supplied with DRY_RUN=true; consider a much lower posting frequency and varied content before enabling real publishing. API posting and video uploads can incur costs and require sufficient account permissions.

## Setup

1. Install Python 3.12+ and run `python -m pip install -r requirements.txt`.
2. Copy `.env.example` to `.env`.
3. In the X Developer Console, configure **Read and Write** user permissions, then create user-context API Key/Secret and Access Token/Secret. Put them in `.env` locally. Never share these credentials.
4. Run `python bot.py` during a :00 or :30 minute to preview the planned post. With `DRY_RUN=true`, nothing is published.
5. Only after testing and checking platform rules, change to `DRY_RUN=false`.
6. On an always-on Linux host, schedule via cron: `* * * * *` is NOT appropriate. Use `0,30 * * * * cd /path/to/x-autopilot-ready && /usr/bin/python3 bot.py >> bot.log 2>&1`.
7. Ensure the host clock/timezone is correct; bot chooses Istanbul slots internally. Cron runs every local half-hour irrespective of host timezone.

### Notes

- API uses OAuth 1.0a user context, legacy chunked video upload and v2 tweet creation. X API endpoints, permissions and pricing may change; validate with current developer docs before going live.
- Successful tweet IDs are saved to SQLite to avoid reposting an already successful slot. A crash between publishing and recording the ID could still cause a duplicate; for production, add reconciliation against the user's recent posts.
- Videos must meet X's media duration, size and encoding constraints.
- If the host is off, no tweets are posted. Use an always-on server for 24/7 operation.
- The sample is intentionally not configured to auto-post on installation.
