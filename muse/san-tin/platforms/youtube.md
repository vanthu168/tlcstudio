# YouTube

Sources: `kind = youtube` (value = channel handle or id). Tier official_network.

1. Open the channel's Videos and Shorts tabs, keep uploads from the last 72 h.
2. One item per video:
   - `source_type: youtube`, `signal_type: post`
   - `publisher: "YouTube: <value>"` (exactly the value from hunt-sources, needed for tier matching)
   - `url`: `https://www.youtube.com/watch?v=<id>` (Shorts: `/shorts/<id>` is fine)
   - `title`, `body`: description (first 3000 chars), `published_at`
   - `engagement`: view count, `comments`: comment count when visible
   - `media_url`: `https://i.ytimg.com/vi/<id>/hqdefault.jpg`
   - `claim_nature`: `announcement` for trailers/premiere news, otherwise `fact`
   - `use_tags`: include `trailer`, `sneak-peek` or `episode-clip` as fits.
