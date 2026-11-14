# YouTube

Sources: `kind = youtube` (value = channel handle or id). Tier official_network.

1. Open the channel's Videos and Shorts tabs, keep uploads from the last 72 h.
2. One item per video:
   - `source_type: youtube`, `signal_type: post`
   - `publisher: "YouTube: <value>"` (exactly the value from hunt-sources, needed for tier matching)
   - `url`: `https://www.youtube.com/watch?v=<id>` (Shorts: `/shorts/<id>` is fine)
   - `title`; `body`: the FULL description from the watch page (`/watch?v=<id>`, also for
     Shorts), up to 3000 chars. If the description is empty or only repeats the title, add the
     on-screen caption/hashtags you can read; never invent text.
   - `published_at`: REQUIRED. Take it from the channel RSS feed
     (`https://www.youtube.com/feeds/videos.xml?channel_id=<UC...>`, field `published`) or the
     watch page `uploadDate`/`publishDate`. "2 hours ago" style text: convert to ISO time.
   - `show`: REQUIRED for every item you send (see "Show mapping" below).
   - `engagement`: view count, `comments`: comment count when visible
   - `media_url`: `https://i.ytimg.com/vi/<id>/hqdefault.jpg`
   - `claim_nature`: `announcement` for trailers/premiere news, otherwise `fact`
   - `use_tags`: include `trailer`, `sneak-peek` or `episode-clip` as fits.

## Show mapping (14/11/2026)

- Channel `90 Day Fiancé` -> `show: "90 Day Fiancé"` always.
- Channel `TLC`: decide from title, description and hashtags, in this order:
  1. Show name or hashtag: #90DayFiance, #TheOtherWay, #BeforeThe90Days, #HEA, #PillowTalk,
     #90DayTheSingleLife -> `90 Day Fiancé`; #1000lbSisters -> `1000-Lb Sisters`;
     #SisterWives -> `Sister Wives`; #WelcomeToPlathville -> `Welcome to Plathville`;
     #7LittleJohnstons -> `7 Little Johnstons`.
  2. A cast name from the watchlist (people list) -> that person's show.
  3. None of the above (other TLC shows, e.g. #TheMadPooper) -> DO NOT SEND the video.
     Only count it in the run report as "skipped: off-watchlist".
- Never send a YouTube item with `show` empty or `Khác`.

Schedule: since 14/11/2026 YouTube is checked inside the hourly news run, but each channel
only when it is due (`cadence_min` from hunt-sources, default 360 = every 6 h). Track the
last check time yourself; if unsure, check it.
