# Facebook pages and groups

Sources: `kind = facebook_page` (value = page username or id) and `kind = facebook_group`.
Tool: your Facebook read access or the browser.

STRICT: read only. Never post, comment, react, share, join a group or answer group questions.
If a group needs joining to read, skip it and say so in the run report.

1. Read posts from the last 24 h.
2. One item per post:
   - `source_type: facebook`, `signal_type: post`, `publisher`: page or group name
   - `url`: the post permalink (`/posts/<id>`, `/permalink/<id>`, or `/groups/<g>/posts/<id>`)
   - `title`: first line, `body`: post text, `media_urls`: images in order
   - `engagement`: reactions, `comments`: comment count
   - `top_comments`: up to 10 `{body, score}`, NO names
3. Classification:
   - Official cast or TLC page: `claim_nature: fact` or `announcement`.
   - Fan page or group: `rumor`, `reaction` or `opinion`. Never `fact`, even if it sounds sure.
   - Group posts are often from private people: do not copy names, profile links or photos
     of the poster. `body` text only.
