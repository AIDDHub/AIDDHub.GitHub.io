# AIDDHub Notes

Source of <https://aiddhub.github.io/> — a working blog about building desktop software for medicinal
chemistry. Static HTML generated from Markdown, served by GitHub Pages.

The products themselves live in a different repository (`AIDDHub/MolStudio`, `web/`) and deploy to
`www.aiddhub.com`. Nothing here is shared with that site.

## Structure

```
content/posts/<slug>.en.md     English post (required)
content/posts/<slug>.zh.md     Chinese translation (optional)
content/pages/<name>.<lang>.md about, projects
content/profile.yml            homepage profile: name, tagline, intro, keywords, now, links
templates/                     Jinja2 templates (base, home, list, post, page, 404)
assets/css/site.css            all styling
assets/js/site.js              nav toggle, TOC scrollspy, copy buttons
assets/og/*.png                social cards, generated per post
tools/build_site.py            the generator
tools/og_image.py              1200x630 card renderer (Pillow)
```

Generated output (never edit by hand): `index.html`, `zh/`, `notes/`, `tutorials/`, `about/`, `projects/`,
`404.html`, `sitemap.xml`, `feed.xml`, `zh/feed.xml`, `robots.txt`.

Sections:

- **notes** (`/notes/`, nav label *Writing*) — essays, build logs, tool opinions. No product badge.
- **tutorials** (`/tutorials/`) — step-by-step walkthroughs.
- **projects** (`/projects/`) — a normal page listing what is being built, and what is not.

## The homepage

The homepage is a profile page, not a product page. Everything on it comes from `content/profile.yml`:
name, handle, avatar, tagline, intro, keywords, a short *Now* list, and the links row. Edit that file and
rebuild; no template changes are needed.

Replace `assets/img/avatar-icon.png` with a square image (300×300 or larger) to use a photo. The same file is
used for the header, the footer and the social cards.

## Adding a post

> 中文操作手册（包含常见问题与 Markdown 速查）：[`docs/写内容.md`](docs/写内容.md)

The site is built from Markdown **in CI**, so publishing only needs one file.

1. Create `content/posts/my-slug.en.md` (the filename must be `<slug>.en.md`, lowercase, hyphens).
2. Write the front matter and the body — see the table below.
3. Commit and push. GitHub Actions builds the HTML and deploys it in about a minute.

No local Python is required. If you want to preview first:

```powershell
C:\miniconda3\python.exe tools\build_site.py
C:\miniconda3\python.exe -m http.server 8899
```

then open <http://127.0.0.1:8899/>.

To start from a filled-in template instead of a blank file:

```powershell
C:\miniconda3\python.exe tools\build_site.py --new my-slug --section notes
```

Front matter:

| Key | Meaning |
|---|---|
| `title` | used in `<h1>`, `<title>` and the social card |
| `short_title` | optional, used in the breadcrumb |
| `description` | meta description, 120–160 characters |
| `date` | `YYYY-MM-DD` |
| `section` | `notes` or `tutorials` |
| `product` | optional: `molstudio`, `molinsight`, `both`. Adds a small badge naming the app used in the post. Omit it for general posts. |
| `tags` | list, emitted as `keywords` |
| `updated` | optional; sets `dateModified` |
| `draft` | `true` keeps the file out of the build |

House style: neutral, specific, no sales voice. Articles end with tags, previous/next navigation and a
corrections line — not a call to action. Every `##` heading becomes a table-of-contents entry.

### Images

Put the file in `assets/img/` and reference it from the Markdown:

```markdown
![Interaction diagram](/assets/img/docking-interactions.png)
```

Keep images under ~500 KB; GitHub Pages allows 1 GB per site.

## Chinese editions

Add `content/posts/<slug>.zh.md` with the same `date`, `section` and `product`. The build emits
`/zh/<section>/<slug>/`, adds the `hreflang` pair and links the two versions. A post without a `.zh.md`
simply has no Chinese page — the build prints a warning listing those posts, so the two editions do not
drift apart unnoticed.

The two homepages are generated from the same `profile.yml`; only the `en`/`zh` values inside it differ.

## Checks

```powershell
python tools/build_site.py --check
```

Fails if the committed HTML differs from a fresh build. Useful before pushing from a machine that has the
build dependencies installed. CI does not require it — the deploy job builds the HTML itself.

Social cards are excluded from the check: they are regenerated locally, and on machines without the Windows
fonts (the Linux runner) the committed cards are kept as-is.

## Build dependencies

`markdown`, `jinja2`, `pyyaml`, `pillow`. Pillow is only needed for the cards; without it the build still
works and the pages omit `og:image`. On this machine they are in the base conda environment:
`C:\miniconda3\python.exe`.

## Deployment

Pages serves the root of `main`. `.nojekyll` disables Jekyll so files are served exactly as committed.
No `CNAME` — the default `aiddhub.github.io` domain is intentional: the product site keeps the `aiddhub.com`
authority, and this site exists to be linked from GitHub, forums and posts.

GitHub Pages does not allow custom cache headers (everything is `max-age=600`), so CSS, JS and the favicon
are referenced with `?v=<content hash>`; editing `site.css` produces a new URL.

## SEO notes

- English is the primary language; `zh` is a mirror with its own canonical and `hreflang`.
- Each post carries `TechArticle`/`Article` plus `BreadcrumbList` structured data.
- `sitemap.xml` includes `xhtml:link` alternates; `robots.txt` points at it.
- `feed.xml` carries the 20 most recent English posts; `zh/feed.xml` the 20 most recent Chinese ones. Each
  page links the feed that matches its language.
- Titles are written for search intent ("why desktop software in 2026"), not for the brand.
