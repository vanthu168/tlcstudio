# Instagram

Sources: `kind = instagram` (value = handle without @). Tier official_cast.
Tool: your Instagram read access or the browser. Read only: never like, follow or comment.

1. Open the profile, read posts and reels from the last 48 h. Stories: only if visible
   without interacting; send them with `signal_type: story`.
2. One item per post:
   - `source_type: instagram`, `signal_type: post` (or `story`), `publisher: @<handle>`
   - `url`: `https://www.instagram.com/p/<code>/` or `/reel/<code>/`
     (must contain the handle owner's post, not a repost page)
   - `title`: first line of the caption (max 500), `body`: full caption
   - `quote_verbatim`: the caption sentence that carries the news
   - `media_urls`: image URLs in order when obtainable, `engagement`: likes
   - `claim_nature: fact` for their own statements, `announcement` for promos
   - `evidence.author_handle`: the handle
3. Special signals, compare with the previous run:
   - Post gone: `signal_type: deleted`, `claim_nature: deleted`, keep the old URL and quote.
   - Two cast members stop following each other: `signal_type: unfollow`,
     `claim_nature: unfollow`, url = the profile, title describes who unfollowed whom.
     Only when you checked both follow lists yourself.
