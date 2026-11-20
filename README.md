# zareya-social

Free auto-posting for Zareya's Instagram (@zareyaagency) and Facebook Page.

- `queue/YYYY-MM-DD.json`: one post per file (slides + caption). Posted on its date, Mon/Wed/Fri 09:17 Nairobi.
- `render.py`: turns a post into 1080x1350 branded slides.
- `publish.py`: renders, hosts the images here, posts to IG + FB with the Meta Graph API, logs to `posted.json`.
- `.github/workflows/post.yml`: the schedule. Run it by hand from the Actions tab to post now.

Needs one repo secret: `META_PAGE_TOKEN` (a non-expiring Facebook Page access token).
