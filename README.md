# jasonharper.com

Preview origin for jasonharper.com. Not WordPress. HostGator stays live until Jason cuts over.

Live preview: https://jasonharper.vercel.app — no DNS change to jasonharper.com.

Home `/` is a project showcase (VYGO, Ready Signal, RXA at OneMagnify, Design Parenting, in that order), not the CrossFit blog index. CrossFit posts, pages, categories, tags, feed, and media stay at their original URLs.

URL-lock samples on the preview origin (HTTP 200, original paths, no rename or redirect):

- post `/its-still-hard/`
- page `/about-me/`
- category `/category/crossfit/`
- image `/wp-content/uploads/2016/04/Overhead-walking-lunge.jpg`

Content is imported from the HostGator WXR export into static HTML at locked permalinks (`/{slug}/`, `/category/{slug}/`, `/tag/{slug}/`). The export itself is not in git.

Locks: every post URL exact. Media keeps filename and public path (`/wp-content/uploads/...`). No DNS change from this repo. HostGator still serves the same media paths.

Re-import (export must already be on disk, outside the repo):

```
python3 scripts/import_wxr.py
python3 scripts/unpack_uploads.py
```

Media files are served at their original public paths (`/wp-content/uploads/YYYY/MM/filename`). Names and paths are not rewritten.
