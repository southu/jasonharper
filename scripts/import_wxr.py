#!/usr/bin/env python3
"""Import a WordPress WXR export into static HTML at locked permalinks.

Reads the HostGator export from disk. Does not copy the export into git.
"""

from __future__ import annotations

import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path

WP = "{http://wordpress.org/export/1.2/}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"
EXCERPT = "{http://wordpress.org/export/1.2/excerpt/}"

REPO = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO / "url-lock.json"
WXR_CANDIDATES = [
    Path("/opt/projects/jasonharper/export/jasonharper.wordpress.xml"),
    Path("/opt/projects/jasonharper/export/jasonharper.wordpress.2026-08-27.000.xml"),
]
RESERVED = {"api", "assets", "scripts", ".git"}

CAPTION_RE = re.compile(r"\[caption([^\]]*)\](.*?)\[/caption\]", re.I | re.S)
GALLERY_RE = re.compile(r"\[gallery([^\]]*)\]", re.I)
ATTR_RE = re.compile(r'(\w+)="([^"]*)"')
INTERNAL_LINK_RE = re.compile(
    r"https?://(?:www\.)?jasonharper\.com(/[^\"'\s<]*)?", re.I
)
BLOCK_START = re.compile(
    r"^\s*<(address|article|aside|blockquote|div|dl|fieldset|form|h[1-6]|header|hr|main|nav|ol|p|pre|section|table|ul|figure|figcaption)(\s|>|/)",
    re.I,
)
TAG_RE = re.compile(r"<[^>]+>")


def esc(s: str) -> str:
    """Escape HTML text without turning apostrophes into entities."""
    return html.escape(s or "", quote=False)


def esc_attr(s: str) -> str:
    return html.escape(s or "", quote=True)


def text(el: ET.Element | None, default: str = "") -> str:
    if el is None or el.text is None:
        return default
    return el.text


def findtext(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    return text(child)


def parse_attrs(blob: str) -> dict[str, str]:
    return {k: v for k, v in ATTR_RE.findall(blob or "")}


def format_date(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(raw[:19], fmt)
            return f"{dt.strftime('%B')} {dt.day}, {dt.year}"
        except ValueError:
            continue
    return raw


def excerpt_plain(html_body: str, limit: int = 220) -> str:
    text_only = TAG_RE.sub(" ", html_body or "")
    text_only = html.unescape(text_only)
    text_only = re.sub(r"\s+", " ", text_only).strip()
    if len(text_only) <= limit:
        return text_only
    cut = text_only[: limit + 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(".,;:") + "…"


def rewrite_internal_links(body: str) -> str:
    def repl(match: re.Match[str]) -> str:
        path = match.group(1) or "/"
        if path.startswith("/wp-content/"):
            return "https://jasonharper.com" + path
        return path

    return INTERNAL_LINK_RE.sub(repl, body)


def expand_captions(body: str) -> str:
    def repl(match: re.Match[str]) -> str:
        attrs = parse_attrs(match.group(1))
        inner = match.group(2).strip()
        align = attrs.get("align", "alignnone")
        img_match = re.search(r"(<a\b[^>]*>\s*)?<img\b[^>]*>\s*(</a>)?", inner, re.I)
        img = img_match.group(0) if img_match else inner
        caption = inner[img_match.end() :].strip() if img_match else ""
        caption = TAG_RE.sub("", caption).strip()
        fig = f'<figure class="wp-caption {esc_attr(align)}">{img}'
        if caption:
            fig += f"<figcaption>{esc(caption)}</figcaption>"
        fig += "</figure>"
        return fig

    return CAPTION_RE.sub(repl, body)


def expand_galleries(body: str, post_id: str, attachments: dict, by_parent: dict) -> str:
    def repl(match: re.Match[str]) -> str:
        attrs = parse_attrs(match.group(1))
        ids = [i.strip() for i in attrs.get("ids", "").split(",") if i.strip()]
        items = []
        if ids:
            for aid in ids:
                att = attachments.get(aid)
                if att:
                    items.append(att)
        else:
            items = by_parent.get(post_id, [])
        if not items:
            return ""
        parts = ['<div class="gallery">']
        for att in items:
            url = att["url"]
            title = esc_attr(att.get("title") or "")
            parts.append(
                f'<a href="{esc_attr(url)}"><img src="{esc_attr(url)}" alt="{title}" /></a>'
            )
        parts.append("</div>")
        return "\n".join(parts)

    return GALLERY_RE.sub(repl, body)


def wpautop(body: str) -> str:
    if not body or not body.strip():
        return ""
    body = body.replace("\r\n", "\n").replace("\r", "\n").strip()
    chunks = re.split(r"\n\s*\n", body)
    out: list[str] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        if BLOCK_START.match(chunk) or chunk.startswith("<figure") or chunk.startswith('<div class="gallery"'):
            out.append(chunk)
        else:
            out.append("<p>" + chunk.replace("\n", "<br />\n") + "</p>")
    return "\n".join(out)


def permalink_path(link: str) -> str:
    link = (link or "").strip()
    link = re.sub(r"^https?://(?:www\.)?jasonharper\.com", "", link, flags=re.I)
    if not link.startswith("/"):
        link = "/" + link
    if not link.endswith("/"):
        link += "/"
    return link


def html_page(
    title: str,
    body: str,
    kicker: str = "",
    tagline: str = "Documenting My Attempt at CrossFit",
    extra_head: str = "",
) -> str:
    safe_title = esc(title)
    nav_home_current = ' aria-current="page"' if title == "Jason Harper" else ""
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{safe_title} — Jason Harper</title>
    <link rel="stylesheet" href="/assets/site.css" />
    {extra_head}
  </head>
  <body>
    <header class="site-header">
      <div class="wrap">
        <p class="site-title"><a href="/">Jason Harper</a></p>
        <p class="site-tagline">{esc(tagline)}</p>
        <nav class="site-nav">
          <a href="/"{nav_home_current}>Home</a>
          <a href="/about-me/">About</a>
          <a href="/my-fitness-journey/">My Fitness Journey</a>
        </nav>
      </div>
    </header>
    <main class="wrap">
      {f'<p class="page-kicker">{esc(kicker)}</p>' if kicker else ""}
      {body}
    </main>
    <footer class="site-footer">
      <div class="wrap">
        <nav>
          <a href="/about-me/">About Me</a>
          <a href="/belly-shots/">Belly Shots</a>
          <a href="/beginner-crossfit-wods/">Beginner CrossFit WODs</a>
          <a href="/crossfit-results/">CrossFit Results</a>
          <a href="/crossfit-shoes/">CrossFit Shoes</a>
          <a href="/my-results/">My Stats</a>
        </nav>
        <p>Jason Harper. Not WordPress. Preview origin for jasonharper.com; HostGator stays live until cutover.</p>
      </div>
    </footer>
  </body>
</html>
"""


def write_page(rel_path: str, content: str) -> Path:
    rel = rel_path.strip("/")
    top = rel.split("/", 1)[0] if rel else ""
    if top in RESERVED:
        raise SystemExit(f"refusing to write reserved path {rel_path}")
    dest = REPO / rel / "index.html" if rel else REPO / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    return dest


def write_feed(xml: str) -> None:
    dest_dir = REPO / "feed"
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "rss.xml").write_text(xml, encoding="utf-8")
    (dest_dir / "index.html").write_text(xml, encoding="utf-8")


def assert_locked_paths_on_disk() -> None:
    if not LOCK_PATH.exists():
        print("url-lock.json missing; skip on-disk lock check", file=sys.stderr)
        return
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    missing: list[str] = []
    for url in lock.get("categories", []) + lock.get("tags", []):
        rel = url.replace("https://jasonharper.com/", "").strip("/")
        if not (REPO / rel / "index.html").exists():
            missing.append(rel)
    feed_ok = (REPO / "feed" / "rss.xml").exists() or (REPO / "feed" / "index.html").exists()
    if not feed_ok:
        missing.append("feed")
    if missing:
        raise SystemExit("locked paths missing on disk: " + ", ".join(missing))


def load_wxr(path: Path) -> dict:
    site_title = None
    site_desc = None
    categories: dict[str, str] = {}
    tags: dict[str, str] = {}
    attachments: dict[str, dict] = {}
    by_parent: dict[str, list] = defaultdict(list)
    posts: list[dict] = []
    pages: list[dict] = []

    for _event, elem in ET.iterparse(path, events=("end",)):
        tag = elem.tag
        local = tag.rsplit("}", 1)[-1]

        if local == "title" and site_title is None and elem.text:
            site_title = elem.text
            continue
        if local == "description" and site_desc is None and elem.text:
            site_desc = elem.text
            continue

        if local == "category" and elem.find(f"{WP}category_nicename") is not None:
            slug = (findtext(elem, f"{WP}category_nicename") or "").strip()
            name = (findtext(elem, f"{WP}cat_name") or "").strip()
            if slug:
                categories[slug] = name or slug
            elem.clear()
            continue

        if local == "tag" and elem.find(f"{WP}tag_slug") is not None:
            slug = (findtext(elem, f"{WP}tag_slug") or "").strip()
            name = (findtext(elem, f"{WP}tag_name") or "").strip()
            if slug:
                tags[slug] = name or slug
            elem.clear()
            continue

        if local != "item":
            continue

        ptype = (findtext(elem, f"{WP}post_type") or "").strip()
        status = (findtext(elem, f"{WP}status") or "").strip()
        post_id = (findtext(elem, f"{WP}post_id") or "").strip()
        title = findtext(elem, "title").strip()
        if ptype == "attachment":
            raw_url = (findtext(elem, f"{WP}attachment_url") or "").strip()
            url = re.sub(r"^http://", "https://", raw_url, count=1)
            parent = (findtext(elem, f"{WP}post_parent") or "").strip()
            rec = {"id": post_id, "url": url, "title": title, "parent": parent}
            if post_id:
                attachments[post_id] = rec
            if parent and parent != "0":
                by_parent[parent].append(rec)
            elem.clear()
            continue

        if ptype not in {"post", "page"} or status != "publish":
            elem.clear()
            continue

        body = findtext(elem, f"{CONTENT}encoded")
        excerpt = findtext(elem, f"{EXCERPT}encoded")
        link = (findtext(elem, "link") or "").strip()
        name = (findtext(elem, f"{WP}post_name") or "").strip()
        date = (findtext(elem, f"{WP}post_date") or "").strip()

        cats = []
        post_tags = []
        for cat in elem.findall("category"):
            domain = cat.get("domain") or ""
            nicename = cat.get("nicename") or ""
            label = (cat.text or nicename).strip()
            if domain == "category" and nicename:
                cats.append({"slug": nicename, "name": label})
            elif domain == "post_tag" and nicename:
                post_tags.append({"slug": nicename, "name": label})

        rec = {
            "id": post_id,
            "type": ptype,
            "title": title,
            "link": link,
            "path": permalink_path(link),
            "name": name,
            "date": date,
            "body": body,
            "excerpt": excerpt,
            "categories": cats,
            "tags": post_tags,
        }
        if ptype == "post":
            posts.append(rec)
        else:
            pages.append(rec)
        elem.clear()

    posts.sort(key=lambda p: p["date"], reverse=True)
    return {
        "title": site_title or "Jason Harper",
        "description": site_desc or "Documenting My Attempt at CrossFit",
        "categories": categories,
        "tags": tags,
        "attachments": attachments,
        "by_parent": by_parent,
        "posts": posts,
        "pages": pages,
    }


def render_body(item: dict, attachments: dict, by_parent: dict) -> str:
    body = item["body"] or ""
    body = expand_captions(body)
    body = expand_galleries(body, item["id"], attachments, by_parent)
    body = rewrite_internal_links(body)
    return wpautop(body)


def tax_links(items: list[dict], kind: str) -> str:
    if not items:
        return ""
    prefix = "/category/" if kind == "category" else "/tag/"
    label = "Categories" if kind == "category" else "Tags"
    bits = [
        f'<a href="{prefix}{esc_attr(t["slug"])}/">{esc(t["name"])}</a>'
        for t in items
    ]
    return f'<p class="tax"><strong>{label}:</strong> ' + ", ".join(bits) + "</p>"


def render_entry(item: dict, attachments: dict, by_parent: dict, kicker: str) -> str:
    body = render_body(item, attachments, by_parent)
    date_html = ""
    if item["type"] == "post" and item["date"]:
        date_html = f'<p class="meta"><time datetime="{esc_attr(item["date"][:10])}">{esc(format_date(item["date"]))}</time></p>'
    inner = f"""<article class="hentry">
        <h1>{esc(item["title"])}</h1>
        {date_html}
        <div class="entry">
          {body}
        </div>
        {tax_links(item["categories"], "category")}
        {tax_links(item["tags"], "tag")}
      </article>"""
    return html_page(item["title"], inner, kicker=kicker)


def render_archive(title: str, kicker: str, items: list[dict]) -> str:
    if items:
        lis = []
        for post in items:
            excerpt = excerpt_plain(post.get("excerpt") or post.get("body") or "")
            excerpt_html = f'<p class="excerpt">{esc(excerpt)}</p>' if excerpt else ""
            lis.append(
                f"""<li>
            <a href="{esc_attr(post["path"])}">{esc(post["title"])}</a>
            <span class="meta">{esc(format_date(post["date"]))}</span>
            {excerpt_html}
          </li>"""
            )
        listing = "<ul class=\"post-list\">\n" + "\n".join(lis) + "\n        </ul>"
    else:
        listing = '<p class="empty">No posts in this archive.</p>'
    inner = f"<h1>{esc(title)}</h1>\n        {listing}"
    return html_page(title, inner, kicker=kicker)


def rfc822(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    for fmt, width in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d", 10)):
        try:
            dt = datetime.strptime(raw[:width], fmt)
            return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except ValueError:
            continue
    return raw


def render_home(_data: dict | None = None) -> str:
    inner = """<section class="home-intro">
        <p class="page-kicker">Project showcase</p>
        <h1>Jason Harper</h1>
        <p>Economist, founder, and applied-AI operator. This preview home is a project showcase — not a CrossFit blog index. The training log, pages, categories, tags, and feed stay at their original URLs.</p>
      </section>
      <ol class="project-list">
        <li class="project">
          <p class="project-kicker">01</p>
          <h2>VYGO</h2>
          <p class="meta">Production engineering for AI-built software</p>
          <p>VYGO takes a working prototype — the UX, workflows, and product learning already proven — and rebuilds the layer underneath so it can survive real users, security reviews, and operations. Audit, architect, harden, hand off the code.</p>
        </li>
        <li class="project">
          <p class="project-kicker">02</p>
          <h2>Ready Signal</h2>
          <p class="meta">Founder and President · <a href="https://www.readysignal.com/">readysignal.com</a></p>
          <p>Ready Signal is an external-data platform for forecasting and decision-making. It normalizes hundreds of economic, market, weather, and other signals so models are not stuck on internal, backward-looking history alone.</p>
        </li>
        <li class="project">
          <p class="project-kicker">03</p>
          <h2>RXA at OneMagnify</h2>
          <p class="meta">Founder · Managing Director · <a href="https://www.rxa.io/">rxa.io</a></p>
          <p>RXA is the data science firm founded in Ann Arbor in 2016 and acquired by OneMagnify in 2023. RXA at OneMagnify delivers data engineering, machine learning, and applied AI for clients who need to make faster, better decisions.</p>
        </li>
        <li class="project">
          <p class="project-kicker">04</p>
          <h2>Design Parenting</h2>
          <p class="meta">Family systems, by design</p>
          <p>Design Parenting applies the same product and systems thinking used at work to how a family actually runs — routines, attention, and the environment kids grow up in — instead of treating parenting as an unexamined default.</p>
        </li>
      </ol>
      <section class="archive-note">
        <h2><a href="/my-fitness-journey/">My Fitness Journey</a></h2>
        <p>Every existing post, page, category, tag, and image path is unchanged. The archive still starts at <a href="/category/crossfit/">CrossFit</a>, with <a href="/about-me/">About Me</a>, <a href="/what-is-crossfit/">What Is CrossFit?</a>, and the <a href="/feed/">feed</a> where they have always been.</p>
      </section>"""
    return html_page(
        "Jason Harper",
        inner,
        tagline="Projects, products, and applied AI",
        extra_head='<link rel="alternate" type="application/rss+xml" title="Jason Harper feed" href="/feed/" />',
    )


def render_feed(posts: list[dict]) -> str:
    items = []
    for post in posts:
        path = post["path"]
        link = f"https://jasonharper.vercel.app{path}"
        desc = excerpt_plain(post.get("excerpt") or post.get("body") or "")
        pub = rfc822(post.get("date") or "")
        pub_xml = f"\n      <pubDate>{esc(pub)}</pubDate>" if pub else ""
        items.append(
            f"""    <item>
      <title>{esc(post["title"])}</title>
      <link>{esc(link)}</link>
      <guid>{esc(link)}</guid>{pub_xml}
      <description>{esc(desc)}</description>
    </item>"""
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0">\n'
        "  <channel>\n"
        "    <title>Jason Harper</title>\n"
        "    <link>https://jasonharper.vercel.app/</link>\n"
        "    <description>Posts from the jasonharper.com training log, served on the preview origin.</description>\n"
        "    <language>en-us</language>\n"
        + "\n".join(items)
        + "\n  </channel>\n"
        "</rss>\n"
    )


def check_lock(data: dict) -> None:
    if not LOCK_PATH.exists():
        print("url-lock.json missing; skip lock check", file=sys.stderr)
        return
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))

    def urls(kind: str, items: list[str] | list[dict], prefix: str | None = None) -> set[str]:
        if kind in {"posts", "pages"}:
            return {i["link"].rstrip("/") + "/" for i in items}
        return {f"https://jasonharper.com{prefix}{slug}/" for slug in items}

    mapping = [
        ("posts", set(lock["posts"]), urls("posts", data["posts"])),
        ("pages", set(lock["pages"]), urls("pages", data["pages"])),
        (
            "categories",
            set(lock["categories"]),
            {f"https://jasonharper.com/category/{s}/" for s in data["categories"]},
        ),
        (
            "tags",
            set(lock["tags"]),
            {f"https://jasonharper.com/tag/{s}/" for s in data["tags"]},
        ),
    ]
    ok = True
    for name, expected, actual in mapping:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            ok = False
            print(f"{name}: missing {missing} extra {extra}", file=sys.stderr)
        else:
            print(f"{name}: {len(actual)} match lock")
    if not ok:
        raise SystemExit("imported URLs do not match url-lock.json")


def main() -> int:
    wxr = next((p for p in WXR_CANDIDATES if p.exists()), None)
    if wxr is None:
        raise SystemExit("WXR export not found on disk")
    if wxr.name.endswith(".000.xml"):
        raise SystemExit("full WXR missing; refusing to import a single split")
    print(f"importing {wxr}")
    data = load_wxr(wxr)
    check_lock(data)

    posts_by_cat: dict[str, list] = defaultdict(list)
    posts_by_tag: dict[str, list] = defaultdict(list)
    for post in data["posts"]:
        body = render_entry(post, data["attachments"], data["by_parent"], "Post")
        write_page(post["path"], body)
        for cat in post["categories"]:
            posts_by_cat[cat["slug"]].append(post)
        for tag in post["tags"]:
            posts_by_tag[tag["slug"]].append(post)

    for page in data["pages"]:
        write_page(
            page["path"],
            render_entry(page, data["attachments"], data["by_parent"], "Page"),
        )

    for slug, name in data["categories"].items():
        write_page(
            f"/category/{slug}/",
            render_archive(name, "Category", posts_by_cat.get(slug, [])),
        )
    for slug, name in data["tags"].items():
        write_page(
            f"/tag/{slug}/",
            render_archive(name, "Tag", posts_by_tag.get(slug, [])),
        )

    write_page("/", render_home(data))
    write_feed(render_feed(data["posts"]))
    assert_locked_paths_on_disk()
    (REPO / "404.html").write_text(
        html_page(
            "Not found",
            "<h1>Not found</h1><p>That URL is not on this preview origin.</p>",
        ),
        encoding="utf-8",
    )

    print(
        f"wrote {len(data['posts'])} posts, {len(data['pages'])} pages, "
        f"{len(data['categories'])} categories, {len(data['tags'])} tags"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
