# REST API vs URL lock delta

Harvested 2026-08-27T08:17:29Z from `https://jasonharper.com/wp-json/wp/v2/` (and collection routes `posts`, `pages`, `categories`, `tags`).

URL lock file: `url-lock.json` (repository root). Companion summary: `url-lock-summary.md`.

## Content slugs (posts, pages, categories, tags)

Compared each live REST collection item `link` (trailing slash stripped) against the corresponding array in `url-lock.json`.

**No differences were found.** Every post, page, category, and tag permalink returned by the live REST API is present in the URL lock, and every lock entry in those four collections is present in the live REST API.

### posts

- Live REST API: 85
- URL lock: 85
- Present in live API, absent from lock: none
- Present in lock, missing from live API: none

### pages

- Live REST API: 9
- URL lock: 9
- Present in live API, absent from lock: none
- Present in lock, missing from live API: none

### categories

- Live REST API: 9
- URL lock: 9
- Present in live API, absent from lock: none
- Present in lock, missing from live API: none

### tags

- Live REST API: 15
- URL lock: 15
- Present in live API, absent from lock: none
- Present in lock, missing from live API: none

## REST collection route slugs

`rest-inventory.json` lists public `/wp/v2` collection route slugs (reachable unauthenticated with HTTP 200 or 405). The URL lock records public HTML permalinks, not REST routes, so route names such as `media` and `comments` are not lock entries.

Public REST route slugs (also listed in `rest-inventory.json`):

- `blocks` — `https://jasonharper.com/wp-json/wp/v2/blocks` — methods: GET, POST
- `categories` — `https://jasonharper.com/wp-json/wp/v2/categories` — methods: GET, POST
- `comments` — `https://jasonharper.com/wp-json/wp/v2/comments` — methods: GET, POST
- `jp_pay_order` — `https://jasonharper.com/wp-json/wp/v2/jp_pay_order` — methods: GET, POST
- `jp_pay_product` — `https://jasonharper.com/wp-json/wp/v2/jp_pay_product` — methods: GET, POST
- `media` — `https://jasonharper.com/wp-json/wp/v2/media` — methods: GET, POST
- `navigation` — `https://jasonharper.com/wp-json/wp/v2/navigation` — methods: GET, POST
- `pages` — `https://jasonharper.com/wp-json/wp/v2/pages` — methods: GET, POST
- `posts` — `https://jasonharper.com/wp-json/wp/v2/posts` — methods: GET, POST
- `search` — `https://jasonharper.com/wp-json/wp/v2/search` — methods: GET
- `statuses` — `https://jasonharper.com/wp-json/wp/v2/statuses` — methods: GET
- `tags` — `https://jasonharper.com/wp-json/wp/v2/tags` — methods: GET, POST
- `taxonomies` — `https://jasonharper.com/wp-json/wp/v2/taxonomies` — methods: GET
- `types` — `https://jasonharper.com/wp-json/wp/v2/types` — methods: GET
- `wp_pattern_category` — `https://jasonharper.com/wp-json/wp/v2/wp_pattern_category` — methods: GET, POST

These REST route slugs are not themselves entries in `url-lock.json` (the lock stores site permalinks). That is expected and is not a content-permalink mismatch.

Lock-only non-collection fields that are not REST `wp/v2` collection routes: `feed` (`https://jasonharper.com/feed/`) and `sitemap` (`https://jasonharper.com/wp-sitemap.xml`).
