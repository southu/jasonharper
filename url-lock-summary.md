# jasonharper.com URL lock

Regression baseline of every public-facing URL on the live WordPress site at https://jasonharper.com, crawled 2026-08-27.

Sources: WordPress REST API (`/wp-json/wp/v2/posts|pages|categories|tags`), live HTTP GET of every collected URL (no redirect following), homepage HTML, and `robots.txt`. Permalink structure on the live site is `/{slug}/` (not `/YYYY/MM/DD/{slug}/`). Date-style samples such as `/2018/04/17/its-still-hard/` return HTTP 404 and are not in this lock.

## Counts

| Collection   | Expected | Actual | Delta |
|--------------|----------|--------|-------|
| posts        | 85       | 85     | none  |
| pages        | 9        | 9      | none  |
| categories   | 9        | 9      | none  |
| tags         | 15       | 15     | none  |

All four collections match the expected counts. Every URL in `url-lock.json` for posts, pages, categories, and tags returned HTTP 200 on a direct GET of the trailing-slash canonical.

There is no Contact page (`/contact/` returns 404). The nine published pages are About Me, Belly Shots, Beginner CrossFit WODs (plus two child pages), CrossFit Results, CrossFit Shoes, My Stats (`/my-results/`), and What Is CrossFit?. The homepage `https://jasonharper.com/` also returns 200 but is the posts index, not a WordPress page, so it is not listed under `pages`.

Machine-readable inventory: `url-lock.json`.

## Feed

- URL: `https://jasonharper.com/feed/`
- Status: HTTP 200
- Content-Type: `application/rss+xml; charset=UTF-8`
- Bare `/feed` 301s to `/feed/` (Location uses `http://`, same WordPress home-URL behaviour as other trailing-slash redirects)

## Sitemap

- Declared URL: `https://jasonharper.com/wp-sitemap.xml` (from `robots.txt`: `Sitemap: https://jasonharper.com/wp-sitemap.xml`)
- Observed: HTTP 301, `X-Redirect-By: WordPress`, Location `https://jasonharper.com/wp-sitemap.xml` (same URL) — a redirect loop
- Child sitemaps (`wp-sitemap-posts-post-1.xml`, `wp-sitemap-posts-page-1.xml`, `wp-sitemap-taxonomies-category-1.xml`, `wp-sitemap-taxonomies-post_tag-1.xml`) loop the same way
- Recorded in `url-lock.json` as the declared sitemap URL. The XML body is not retrievable without following the loop.

## Redirects

### www → apex

`GET https://www.jasonharper.com` and `GET https://www.jasonharper.com/` both return **HTTP 301**. Observed `Location` header: `http://jasonharper.com/`.

WordPress (`X-Redirect-By: WordPress`) is issuing that redirect. The Location scheme is `http`, not `https`. A follow-up GET of `http://jasonharper.com/` then 301s to `https://jasonharper.com/`.

Related host redirects:

- `http://jasonharper.com/` → 301 → `https://jasonharper.com/`
- `http://www.jasonharper.com/` → 301 → `https://www.jasonharper.com/` (then the www→apex rule above)

### Trailing-slash canonicalization

WordPress canonicalizes **to** the trailing-slash form. Bare URLs do **not** return 200 directly.

For posts and pages:

- `GET https://jasonharper.com/its-still-hard` (post, no slash) → **HTTP 301**, Location `http://jasonharper.com/its-still-hard/`
- `GET https://jasonharper.com/its-still-hard/` (post, with slash) → **HTTP 200** (no further redirect)
- `GET https://jasonharper.com/about-me` (page, no slash) → **HTTP 301**, Location `http://jasonharper.com/about-me/`
- `GET https://jasonharper.com/about-me/` (page, with slash) → **HTTP 200** (no further redirect)

The same rule was observed on:

- post `https://jasonharper.com/my-first-wod` → 301 → `http://jasonharper.com/my-first-wod/`
- page `https://jasonharper.com/what-is-crossfit` → 301 → `http://jasonharper.com/what-is-crossfit/`
- nested page `https://jasonharper.com/beginner-crossfit-wods/beginner-crossfit-program` → 301 → `http://jasonharper.com/beginner-crossfit-wods/beginner-crossfit-program/`
- category `https://jasonharper.com/category/crossfit` → 301 → `http://jasonharper.com/category/crossfit/`
- tag `https://jasonharper.com/tag/paleo` → 301 → `http://jasonharper.com/tag/paleo/`

Bare-URL Location headers use `http://jasonharper.com/.../` (WordPress home URL). The trailing-slash HTTPS URL is the document that actually returns 200.

Homepage: both `https://jasonharper.com` and `https://jasonharper.com/` return HTTP 200 (no slash redirect).

## Notes for migration

- Lock every post at its current `https://jasonharper.com/{slug}/` path. Do not assume `/YYYY/MM/DD/{slug}/` aliases exist; sampled date paths 404.
- Preserve trailing slashes on posts, pages, categories, tags, and `/feed/`.
- Preserve `/category/{slug}/` and `/tag/{slug}/` including unused tag `crossfit-2` (count 0, still HTTP 200).
- www→apex must keep HTTP 301. Today Location is `http://jasonharper.com/`; a cutover that emits `https://jasonharper.com/` would be a behaviour change.
- `/wp-sitemap.xml` currently does not serve XML. Fixing the loop is WordPress/host configuration, not part of this lock.
