# AIDDHub Notes

Source of <https://aiddhub.github.io/> — tutorials and case studies for MolStudio and MolInsight.
Static HTML, generated from Markdown, served by GitHub Pages.

The product site lives in a different repository (`AIDDHub/MolStudio`, `web/`) and is deployed to
`www.aiddhub.com`. Nothing here is shared with it.

## Layout

```
content/posts/<slug>.en.md     English article (required)
content/posts/<slug>.zh.md     Chinese translation (optional)
content/pages/about.<lang>.md  standalone pages
templates/                     Jinja2 templates (base, home, list, post, page, 404)
assets/css/site.css            all styling
assets/js/site.js              nav toggle, TOC scrollspy, card filters, copy buttons
assets/og/*.png                social cards, generated
tools/build_site.py            the generator
tools/og_image.py              1200x630 card renderer (Pillow)
```

Generated output (do not edit by hand): `index.html`, `zh/`, `tutorials/`, `cases/`, `about/`,
`404.html`, `sitemap.xml`, `feed.xml`, `robots.txt`.

## Writing an article

```powershell
python tools/build_site.py --new docking-on-a-laptop --section tutorials
```

That creates `content/posts/docking-on-a-laptop.en.md`. Fill the front matter and the body, then:

```powershell
python tools/build_site.py
git add -A
git commit -m "post: docking on a laptop"
git push
```

GitHub Pages rebuilds in about a minute.

Front matter:

| Key | Meaning |
|---|---|
| `title` | article title, used in `<h1>`, `<title>` and the social card |
| `short_title` | optional, used in the breadcrumb |
| `description` | meta description, 120–160 characters |
| `date` | `YYYY-MM-DD` |
| `section` | `tutorials` or `cases` |
| `product` | `molstudio`, `molinsight` or `both` — drives the badge, the filter and the CTA |
| `tags` | list, emitted as `keywords` |
| `updated` | optional; sets `dateModified` in the structured data |
| `draft` | `true` keeps the file out of the build |

Writing rules for this site:

- every `##` heading becomes a table-of-contents entry, so keep them short;
- one idea per section, and put the number in the sentence, not in the adjectives;
- tables are fine, and they are what most readers scan first;
- no claim about the software that is not true for the current release.

## Chinese editions

Add `content/posts/<slug>.zh.md` with the same `date`, `section` and `product`. The build then emits
`/zh/<section>/<slug>/`, adds the `hreflang` pair and links the two versions. A post without a `.zh.md`
simply has no Chinese page.

## Checks

```powershell
python tools/build_site.py --check
```

Fails if the committed HTML differs from a fresh build — the same check runs in GitHub Actions on every
push, so a forgotten rebuild cannot reach the site.

## Build dependencies

`markdown`, `jinja2`, `pyyaml`, `pillow` (Pillow only for the social cards; the build still works without
it, the pages just omit `og:image`). On this machine they live in the base conda environment:
`C:\miniconda3\python.exe`.

## Deployment

Pages serves the repository root of `main`. `.nojekyll` disables Jekyll so the files are served exactly as
committed. No CNAME: the default `aiddhub.github.io` domain is intentional — the product site keeps the
`aiddhub.com` authority, and this site is here to be linked from GitHub, forums and posts.

Cache headers cannot be configured on GitHub Pages (everything gets `max-age=600`), so CSS, JS and the
favicon are referenced with `?v=<content hash>`; a change to `site.css` produces a new URL.

## SEO notes

- English is the primary language; `zh` is a full mirror with its own canonical and `hreflang`.
- Each article carries `TechArticle`/`Article` plus `BreadcrumbList` structured data.
- `sitemap.xml` includes `xhtml:link` alternates; `robots.txt` points at it.
- `feed.xml` carries the 20 most recent English posts.
- Titles are written for search intent ("how to dock without Python"), not for the brand.
