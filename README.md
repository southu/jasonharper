# jasonharper.com

Preview origin for jasonharper.com. Not WordPress. HostGator stays live until Jason cuts over.

Live preview: https://jasonharper.vercel.app — no DNS change to jasonharper.com.

Content is imported from the HostGator WXR export into static HTML at locked permalinks (`/{slug}/`, `/category/{slug}/`, `/tag/{slug}/`). The export itself is not in git.

Locks: every post URL exact. Media keeps filename and public path (`/wp-content/uploads/...`). No DNS change from this repo.

Re-import (export must already be on disk, outside the repo):

```
python3 scripts/import_wxr.py
```
