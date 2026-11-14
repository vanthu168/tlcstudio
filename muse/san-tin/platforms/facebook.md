# Facebook pages and groups

Sources: `kind = facebook_page` (value = page username, or the numeric page id when the page
has no username) and `kind = facebook_group` (value = group id or group slug).
Run in task `tlc-facebook-hunt`. Tool: your Facebook read access (Meta tools) first, the browser
only if the tool cannot read the page.

STRICT: read only. Never post, comment, react, share, follow, like, join a group, answer group
questions, or message anyone. If a page or group cannot be read without joining or following,
skip it and say so in the run report. Never send or ask for a verification code: if Facebook asks
for one, stop the Facebook part of the run and say so.

LIST ONLY: hunt only the pages and groups in `/hunt-sources`. No broad search on Facebook, no
"pages that look relevant". To suggest a new page or group, write it in the run report; the owner
adds it on the Dash.

## Finding new posts (timeline is blocked)

Listing a page timeline through the Facebook CLI returns 403 (checked 15/11/2026); reading one
post by its permalink works. So find the post links first, then read each one:

1. Try the CLI timeline once per run. If it works, use it and skip step 2.
2. Otherwise open the page in the browser (logged-in session, read only) and collect post
   permalinks from the last 48 h. If the browser also fails, use web search restricted to the page,
   e.g. `site:facebook.com/<value>` with the last 2 days, and keep only links whose path starts
   with `/<value>/` or `/reel/` and that the post read confirms belongs to this page.
3. Read every candidate with the post-read tool. Drop it if the author is not this page or the post
   is older than 48 h.
4. In the run report, say per page which method found the links (cli, browser, search) and how
   many. A page with 0 links from every method is "no new posts", not an error.

## Pages (`facebook_page`)

1. Read posts from the last 48 h (respect `cadence_min`), found as above.
2. One item per post:
   - `source_type: facebook`, `signal_type: post`
   - `publisher: "@<value>"` exactly as in `/hunt-sources` (the gateway grades the item from it)
   - `evidence.author_handle`: the same `<value>`
   - `url`: the post permalink. Accepted shapes, best first:
     `https://www.facebook.com/<value>/posts/<id>`, `.../<value>/videos/<id>`,
     `https://www.facebook.com/permalink.php?story_fbid=<id>&id=<page id>`.
     Never send `/share/...` short links, `l.facebook.com` redirects, or the page home.
     Drop tracking parameters (`__cft__`, `__tn__`).
   - `title`: first line of the post (max 500), `body`: full post text (max 3000)
   - `quote_verbatim`: the sentence that carries the news
   - `media_urls`: images in order, taken from the post itself
   - `engagement`: reactions, `comments`: comment count
   - `top_comments`: up to 10 `{body, score}`, NO names
   - `published_at` from the post time
3. Classification:
   - Official TLC/show page or a cast member's own page: `fact` for their own statements,
     `announcement` for premieres, trailers, cast reveals.
   - A page that only reposts other outlets: `claim`, and put the original outlet in `raw.origin`.
   - Shared links to articles: send the post, and ALSO the article itself as `source_type: news`
     only if its site is in `/hunt-sources`.

## Groups (`facebook_group`)

Only groups that appear in `/hunt-sources` AND that your account can already read.

1. Use the same link finding as pages (group feed, then browser, then search). Read posts from the last 24 h, top posts by comments first, at most 20 per group per run.
2. One item per post: `source_type: facebook`, `signal_type: post`,
   `publisher: "@<value>"`, `url: https://www.facebook.com/groups/<value>/posts/<id>`.
3. Privacy: group posters are private people. Do NOT send their names, profile links, photos,
   or screenshots that show them. `body` = post text only; `top_comments` = text and score only.
   If the post is about a private person (not cast), skip it.
4. Classification: `rumor`, `reaction` or `opinion`. Never `fact`, even if it sounds sure.
   A group post that links to a cast member's own post: send the cast post instead (from the
   cast page) if that page is in the list.

## Run order and batching

- Pages first (official, then cast), groups last.
- Batches of about 8 posts: read, build items, `POST`, then record HTTP code, inserted,
  duplicates, rejected in your run note before the next batch.
- Report one line: pages read, groups read, skipped (why), items sent, inserted, duplicates,
  rejected.
