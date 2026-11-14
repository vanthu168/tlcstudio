# Instagram

Sources: `kind = instagram` (value = handle without @). Tier official_cast.
Tool: the browser, signed in with the SECONDARY reading account only (never the owner's
main account). Read only: never like, follow, unfollow, comment, message, post, or change
any setting. Never send or ask for a verification code: if Instagram asks for one, stop the
Instagram part of the run and say so in the report.

1. Open the profile, read posts and reels from the last 48 h. Stories: only if visible
   without interacting; send them with `signal_type: story`.
Run in task `tlc-social-hunt`. `publisher` MUST be `@<handle>` and `evidence.author_handle`
MUST be the handle: post links (`/p/`, `/reel/`) do not contain the account name, so the
gateway uses these two fields to grade the item as official_cast (A). Missing them = grade D.

2. One item per post:
   - `source_type: instagram`, `signal_type: post` (or `story`), `publisher: @<handle>`
   - `url`: `https://www.instagram.com/p/<code>/` or `/reel/<code>/`
     (must contain the handle owner's post, not a repost page)
   - `title`: first line of the caption (max 500), `body`: full caption
   - `quote_verbatim`: the caption sentence that carries the news
   - `media_urls`: image URLs in order when obtainable, `engagement`: likes
   - `claim_nature: fact` for their own statements, `announcement` for promos
   - `evidence.author_handle`: the handle
3. Special signals, compare with the previous run. Keep a private note per handle
   (in your own task memory, never in this repo) with the post URLs and follow counts you saw
   last run. No note from a previous run = skip deleted/unfollow detection this time, just
   record the note.
   - Post gone: `signal_type: deleted`, `claim_nature: deleted`, keep the old URL and quote.
   - Two cast members stop following each other: `signal_type: unfollow`,
     `claim_nature: unfollow`, url = the profile, title describes who unfollowed whom.
     Only when you checked both follow lists yourself.

## Run order and batching (lessons from 14/11/2026)

- Hunt and submit Instagram FIRST in `tlc-social-hunt`, before anything else in the task.
- Work in small batches of about 8 posts: read them, build the items, `POST` them, then
  write the batch result (HTTP code, inserted, duplicates, rejected) to your own run note
  before starting the next batch. A run that stops halfway must not lose finished batches.
- Always record the submit result. "Sent" without an HTTP code and counts is not a result.

## Images

- Get `media_urls` by opening each post or reel page itself, not from the profile grid
  thumbnails. For a carousel, take every image in order.
- Stories: send text only, no image (story image links expire within hours).
- The gateway copies images to temporary storage, so a valid direct image URL is enough.
