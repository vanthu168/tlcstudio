# News sites

Sources: `kind = news_site` (value = domain) and `kind = rss`. Tier is press_1 or press_2.

1. Open the site's TLC / reality TV section or RSS feed, or web-search
   `site:<domain> <show name>` for the last 48 h.
2. Keep only articles about the five shows or watchlist people.
3. One item per article:
   - `source_type: news`, `signal_type: article`, `publisher`: site name
   - `url`: canonical article URL (no tracking params)
   - `title`: headline, `body`: first 3000 chars of the article text (no ads, no related links)
   - `published_at` from the article, `media_url`: lead image
   - `quote_verbatim`: the key sentence or the quoted words of a cast member
   - `claim_nature`: `claim` when attributed ("a source says", "X told People"),
     `fact` when it embeds the cast member's own post, `legal` when citing court records,
     `rumor` for "fans think", `opinion` for reviews/recaps
   - `evidence.permalink`: the article URL; if it embeds a social post, add `raw.embedded_urls`.
