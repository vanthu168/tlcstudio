# TikTok

Sources: `kind = tiktok` (value = handle without @). Tier official_cast. Read only.

1. Open `https://www.tiktok.com/@<handle>`, read videos from the last 48 h.
2. One item per video:
   - `source_type: tiktok`, `signal_type: post`, `publisher: @<handle>`
   - `url`: `https://www.tiktok.com/@<handle>/video/<id>`
   - `title`: caption first line, `body`: caption plus on-screen text you can read
   - `quote_verbatim`: what they say in the video, word for word, if it carries the news
     (only words you actually heard or read; otherwise leave empty)
   - `engagement`: views or likes, `media_url`: cover image if obtainable
   - `claim_nature: fact` (own statement) or `reaction`, `use_tags` include `tiktok-video`
3. Lives, duets and stitches of other people: skip unless a cast member is speaking.
