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
templates/                     Jinja2 templates (base, home, list, post, page, 404)
assets/css/site.css            all styling
assets/js/site.js              nav toggle, TOC scrollspy, copy buttons
assets/og/*.png                social cards, generated per post
tools/build_site.py            the generator
tools/og_image.py              1200x630 card renderer (Pillow)
```

Generated output (never edit by hand): `index.html`, `zh/`, `notes/`, `tutorials/`, `about/`, `projects/`,
`404.html`, `sitemap.xml`, `feed.xml`, `robots.txt`.

Sections:

- **notes** (`/notes/`, nav label *Writing*) — essays, build logs, tool opinions. No product badge.
- **tutorials** (`/tutorials/`) — step-by-step walkthroughs.
- **projects** (`/projects/`) — a normal page listing what is being built, and what is not.

## Writing a post

```powershell
python tools/build_site.py --new why-i-use-rdkit --section notes
```

That creates `content/posts/why-i-use-rdkit.en.md`. Fill the front matter and the body, then:

```powershell
python tools/build_site.py
git add -A
git commit -m "post: why i use rdkit"
git push
```

GitHub Pages rebuilds in about a minute.

Front matter:

| Key | Meaning |
|---|---|
| `title` | used in `<h1>`, `<title>` and the social card |
| `short_title` | optional, used in the breadcrumb |
| `description` | meta description, 120–160 characters |
| `date` | `YYYY-MM-DD` |
| `section` | `notes` or `tutorials` |
| `product` | optional: `molstudio`, `molinsight`, `both`. Adds a badge and turns the closing box into a download CTA. Omit it for general posts. |
| `tags` | list, emitted as `keywords` |
| `featured` | `true` pins the post under *Start here* on the homepage |
| `updated` | optional; sets `dateModified` |
| `draft` | `true` keeps the file out of the build |

House style: first person, one idea per section, numbers instead of adjectives, and no claim about the
software that is not true for the current release. Every `##` heading becomes a table-of-contents entry.

## Chinese editions

Add `content/posts/<slug>.zh.md` with the same `date`, `section` and `product`. The build emits
`/zh/<section>/<slug>/`, adds the `hreflang` pair and links the two versions. A post without a `.zh.md`
simply has no Chinese page; the Chinese index stays valid as long as at least one post is translated.

## Checks

```powershell
python tools/build_site.py --check
```

Fails if the committed HTML differs from a fresh build. The same check runs in GitHub Actions on every push,
so a forgotten rebuild cannot reach the site. Social cards are excluded from the check (they are regenerated
but compared by content only when the text changes).

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
- `feed.xml` carries the 20 most recent English posts.
- Titles are written for search intent ("why desktop software in 2026"), not for the brand.
