# News sites

Sources: `kind = news_site` (value = domain) and `kind = rss`. Tier is press_1 or press_2.

1. Open the site's TLC / reality TV section or RSS feed, or web-search
   `site:<domain> <show name>` for the last 48 h.
2. Keep only articles about the five shows or watchlist people.
3. One item per article:
   - `source_type: news`, `signal_type: article`, `publisher`: site name
   - `url`: canonical article URL (no tracking params)
   - `title`: headline
   - `body`: the FULL article text, up to 12000 chars. Keep every paragraph and every quote
     in order, including the second half where cast quotes usually sit. Drop ads, menus,
     newsletter boxes, "read more" / related links, photo credits and comment sections.
     Only if the article is longer than 12000 chars, keep the first 12000.
   - `published_at` from the article
   - `media_url`: lead image (og:image)
   - `media_urls`: lead image first, then the images inside the article body in page order
     (max 20). Direct image links only, the largest size the page offers, no logos, icons,
     ads or author photos. Embedded Instagram/TikTok posts are links, not images: put them
     in `raw.embedded_urls`.
   - `quote_verbatim`: the key sentence or the quoted words of a cast member
   - `claim_nature`: `claim` when attributed ("a source says", "X told People"),
     `fact` when it embeds the cast member's own post, `legal` when citing court records,
     `rumor` for "fans think", `opinion` for reviews/recaps
   - `evidence.permalink`: the article URL; if it embeds a social post, add `raw.embedded_urls`.
