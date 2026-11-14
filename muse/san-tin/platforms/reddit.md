# Reddit

Sources: `kind = subreddit` from /hunt-sources. Tool: Composio Reddit (read only).

1. List `new` and `hot` posts of the subreddit from the last 24 h.
2. Keep a post if `score >= min_score` (when set) and the title or body matches
   `match_regex` (when set, case-insensitive).
3. One item per post:
   - `source_type: reddit`, `signal_type: thread`, `publisher: r/<sub>`
   - `url`: the post permalink `https://www.reddit.com/r/<sub>/comments/<id>/...`
   - `score`, `comments`, `hot: true` when in the hot list top 10, `flair`
   - `body`: selftext. Image or gallery posts: `media_url` / `media_urls` (i.redd.it links, in order).
     A link post: put the external link in `raw.link_url` and the article title in `title`.
   - `top_comments`: up to 10, `{body, score}`, NO usernames.
   - `claim_nature`: usually `reaction`, `rumor` or `opinion`. Use `fact` only when the post is
     a screenshot of a cast member's own post (then also send that original post if reachable).
4. Re-send hot posts every run so score and comments stay fresh (duplicates are free).
