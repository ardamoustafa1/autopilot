# X AutoPilot — complete GitHub Actions package

Includes all 3 user-provided MP4 files and original tweet copy. No paid AI service required.

## Important behavior
- GitHub Actions *attempts* to run at :00 and :30 every hour (UTC cron, which is still :00/:30 in Istanbul). GitHub may delay or skip scheduled runs.
- 18:00 Combo 1; 18:30 Deste; 19:00 Combo 2; 19:30 Deste; repeats as a *selection schedule*.
- **Does not repeatedly post identical content.** Each unique post ID is published at most once, recorded in `state.json`. After the three unique posts have been sent, later scheduled runs skip them. Add new genuinely distinct content to extend the campaign. X may reject or limit duplicate/near-duplicate posts; Combo posts share text and could be treated as duplicates.
- Default is DRY_RUN=true and ENABLE_PUBLISHING=false. No real tweets without both explicit switches.
- Media uploads and posting require suitable X API credits/permissions; the legacy `upload.twitter.com/1.1/media/upload.json` endpoint may not be available for all X developer access tiers. If X returns 403/404, the upload integration needs adjustment for the account's supported media API.
- This is an API implementation, not a verified successful upload to your account.

## Install (replace repository files)
1. Unzip locally. Upload all files including the hidden `.github/workflows/autopilot.yml` and `videos/` to the existing GitHub repo, preserving paths. Do not upload `.env` or any secrets.
2. In GitHub repository **Settings → Secrets and variables → Actions → Secrets**, add four *repository secrets*: `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` using **rotated**, valid credentials. Vercel environment variables are not automatically shared with GitHub Actions.
3. Under **Variables** add `DRY_RUN=true` and `ENABLE_PUBLISHING=false` (repository variables, not secrets).
4. Under **Actions → X AutoPilot → Run workflow**, run once. The log should say `DRY RUN` or `Skipped already published content`. No tweet will be sent.
5. Only after checking X API access, account credits, content, and platform rules, explicitly set `DRY_RUN=false` and `ENABLE_PUBLISHING=true` in GitHub repository variables. A scheduled run will then attempt the next not-yet-published item.
6. After a successful post, GitHub Actions commits `state.json` to the repo. This requires Actions workflow write permission and branch rules allowing the bot to push. If state persistence fails, STOP the workflow before rerunning to avoid duplicates.
7. To stop, disable workflow under GitHub Actions or set `ENABLE_PUBLISHING=false`.

## Existing Vercel deployment
You can leave Vercel deployed as a status endpoint. This GitHub Actions version executes `bot.py` on GitHub runners, so it does **not** use Vercel cron, Vercel `CRON_SECRET`, or Vercel's X secrets.

## Notes
- GitHub Actions schedule on a public repository can be automatically disabled after inactivity; check Actions periodically.
- The 3 video files are included in the archive; verify they are the intended originals.
- X API posting and media upload can incur charges; check developer console before live runs.
- The same post text across two Combo videos may be considered duplicate content; change one to a distinct original caption before enabling live publishing.
- If media upload succeeds but posting fails, the media may be orphaned. Inspect logs and X account before retrying.
