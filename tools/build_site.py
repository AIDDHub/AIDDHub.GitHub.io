#!/usr/bin/env python3
"""Build the AIDDHub GitHub Pages site from Markdown sources.

Usage
-----
    python tools/build_site.py             # write the site into the repo root
    python tools/build_site.py --check     # fail if the committed HTML is stale
    python tools/build_site.py --new my-slug --section tutorials

Layout
------
    content/posts/<slug>.en.md   English article (required)
    content/posts/<slug>.zh.md   Chinese translation (optional)
    content/pages/<name>.<lang>.md

Front matter keys
-----------------
    title        article title
    description  meta description (120-160 chars works best)
    date         YYYY-MM-DD
    section      notes | tutorials
    product      molstudio | molinsight | both   (optional, omit for general posts)
    featured     true to pin the post on the homepage (optional)
    tags         [list, of, tags]
    updated      YYYY-MM-DD (optional)
    draft        true to keep the file out of the build
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:  # optional: social cards are a nice-to-have, not a build requirement
    import og_image
except Exception:  # pragma: no cover - Pillow or fonts missing
    og_image = None

SITE = {
    "name": "AIDDHub Notes",
    "brand": "AIDDHub",
    "tagline": "Tutorials & case studies",
    "url": "https://aiddhub.github.io",
    "main": "https://www.aiddhub.com",
    "main_label": "aiddhub.com",
    "email": "support@aiddhub.com",
}

PRODUCTS = {
    "molstudio": {"label": "MolStudio", "href": SITE["main"] + "/molstudio"},
    "molinsight": {"label": "MolInsight", "href": SITE["main"] + "/molinsight"},
    "both": {"label": "MolStudio + MolInsight", "href": SITE["main"] + "/molstudio"},
}

SECTIONS = ("notes", "tutorials")

SECTION_TEXT = {
    "notes": {
        "en": {
            "title": "Writing",
            "blurb": "Essays, build notes and observations on computational chemistry software — decisions, "
                     "trade-offs, and the parts that turned out to be harder than expected.",
        },
        "zh": {
            "title": "随笔",
            "blurb": "关于计算化学软件的文章：设计决策、取舍，以及那些比预想更难的部分。",
        },
    },
    "tutorials": {
        "en": {
            "title": "Tutorials",
            "blurb": "Step-by-step walkthroughs. Each one starts from a real task, shows the clicks, and ends with "
                     "a figure or a table that belongs in a report.",
        },
        "zh": {
            "title": "教程",
            "blurb": "分步操作指南。每篇都从实际任务出发，写清点击路径，最后给出可以直接放进汇报的图或表。",
        },
    },
}

TEXT = {
    "en": {
        "lang_attr": "en",
        "og_locale": "en_US",
        "tagline": "Notes on chemistry software",
        "nav": {"home": "Home", "notes": "Writing", "tutorials": "Tutorials", "projects": "Projects", "about": "About"},
        "footer": {"resources": "Pages", "products": "Projects", "pricing": "Pricing", "download": "Download"},
        "footer_blurb": "Notes on desktop software for medicinal chemistry: molecular modelling, docking, SAR "
                        "analysis, and the engineering behind them.",
        "home": {
            "h1": "Notes on chemistry software",
            "lede": "AIDDHub builds desktop tools for molecular modelling and SAR analysis. This is where the work "
                    "gets written down: walkthroughs, build notes, and the occasional opinion.",
            "writing_title": "Writing",
            "now_title": "Now",
        },
        "list": {"empty": "Nothing published here yet."},
        "post": {"min_read": "min read", "updated": "Updated", "toc": "On this page",
                 "previous": "Previous", "next": "Next",
                 "corrections": "Corrections and questions are welcome at"},
        "notfound": {"text": "That page does not exist. The index is probably what you want.",
                     "home": "Back to the homepage"},
    },
    "zh": {
        "lang_attr": "zh-CN",
        "og_locale": "zh_CN",
        "tagline": "化学软件笔记",
        "nav": {"home": "首页", "notes": "随笔", "tutorials": "教程", "projects": "项目", "about": "关于"},
        "footer": {"resources": "页面", "products": "项目", "pricing": "价格", "download": "下载"},
        "footer_blurb": "关于药物化学桌面软件的笔记：分子建模、分子对接、构效分析，以及背后的工程问题。",
        "home": {
            "h1": "化学软件笔记",
            "lede": "AIDDHub 做分子建模与构效分析的桌面工具。这里记录工作本身：操作教程、开发笔记，"
                    "偶尔也写点看法。",
            "writing_title": "文章",
            "now_title": "近况",
        },
        "list": {"empty": "这里还没有内容。"},
        "post": {"min_read": "分钟阅读", "updated": "更新于", "toc": "本页目录",
                 "previous": "上一篇", "next": "下一篇",
                 "corrections": "勘误与问题请联系"},
        "notfound": {"text": "这个页面不存在。你可能想找的是文章列表。", "home": "返回首页"},
    },
}

BADGE_CLASS = {"notes": "note", "tutorials": "tutorial"}
SECTION_LABEL = {
    "notes": {"en": "Note", "zh": "随笔"},
    "tutorials": {"en": "Tutorial", "zh": "教程"},
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def asset_version() -> str:
    digest = hashlib.sha256()
    for name in ("css/site.css", "js/site.js"):
        digest.update((ASSETS / name).read_bytes())
    return digest.hexdigest()[:8]


def split_front_matter(text: str, path: Path) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise SystemExit(f"{path}: missing YAML front matter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise SystemExit(f"{path}: unterminated YAML front matter")
    meta = yaml.safe_load(parts[1]) or {}
    return meta, parts[2].lstrip("\n")


def md_render(body: str) -> tuple[str, list]:
    renderer = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"toc_depth": "2-3", "permalink": False}},
    )
    html_body = renderer.convert(body)
    return html_body, renderer.toc_tokens


def toc_html(tokens: list) -> str:
    if not tokens:
        return ""

    def walk(items):
        chunks = ["<ul>"]
        for item in items:
            chunks.append('<li><a href="#%s">%s</a>' % (item["id"], html.escape(item["name"])))
            if item.get("children"):
                chunks.append(walk(item["children"]))
            chunks.append("</li>")
        chunks.append("</ul>")
        return "".join(chunks)

    return walk(tokens)


def reading_minutes(text: str, lang: str) -> int:
    plain = re.sub(r"<[^>]+>", " ", text)
    if lang == "zh":
        chars = len(re.findall(r"[\u4e00-\u9fff]", plain))
        return max(1, round(chars / 420))
    words = len(plain.split())
    return max(1, round(words / 220))


def date_label(value: date, lang: str) -> str:
    if lang == "zh":
        return f"{value.year} 年 {value.month} 月 {value.day} 日"
    return value.strftime("%B ") + str(value.day) + value.strftime(", %Y")


def as_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def url_path(*parts: str, lang: str = "en") -> str:
    prefix = "/zh" if lang == "zh" else ""
    tail = "".join("/" + part for part in parts)
    return (prefix + tail + "/").replace("//", "/")


def absolute(path: str) -> str:
    return SITE["url"] + path


def write(dest: Path, rel: str, body: str) -> str:
    target = dest / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8", newline="\n")
    return rel


GENERATED_DIRS = ("about", "notes", "tutorials", "cases", "projects", "zh")
GENERATED_FILES = ("index.html", "404.html", "sitemap.xml", "feed.xml", "robots.txt")


def clean_output(dest: Path) -> None:
    """Remove previous output so a moved or renamed post cannot leave a stale page."""
    for name in GENERATED_DIRS:
        shutil.rmtree(dest / name, ignore_errors=True)
    for name in GENERATED_FILES:
        target = dest / name
        if target.exists():
            target.unlink()


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #

def load_posts() -> dict[str, dict[str, dict]]:
    posts: dict[str, dict[str, dict]] = {}
    pattern = re.compile(r"^(?P<slug>[a-z0-9-]+)\.(?P<lang>en|zh)\.md$")
    for path in sorted((CONTENT / "posts").glob("*.md")):
        match = pattern.match(path.name)
        if not match:
            raise SystemExit(f"{path}: expected <slug>.en.md or <slug>.zh.md")
        slug, lang = match.group("slug"), match.group("lang")
        meta, body = split_front_matter(path.read_text(encoding="utf-8"), path)
        if meta.get("draft"):
            continue
        section = meta.get("section", "notes")
        if section not in SECTIONS:
            raise SystemExit(f"{path}: section must be one of {SECTIONS}")
        product = meta.get("product") or None
        if product and product not in PRODUCTS:
            raise SystemExit(f"{path}: product must be one of {tuple(PRODUCTS)}")
        published = as_date(meta["date"])
        updated = as_date(meta["updated"]) if meta.get("updated") else None
        body_html, tokens = md_render(body)
        title = meta["title"]
        posts.setdefault(slug, {})[lang] = {
            "slug": slug,
            "lang": lang,
            "title": title,
            "short_title": meta.get("short_title") or re.split(r"\s+[—–|]\s+", title)[0],
            "description": meta["description"],
            "section": section,
            "product": product,
            "featured": bool(meta.get("featured")),
            "tags": meta.get("tags") or [],
            "date": published,
            "updated": updated,
            "iso": published.isoformat(),
            "updated_iso": updated.isoformat() if updated else None,
            "date_label": date_label(published, lang),
            "updated_label": date_label(updated, lang) if updated else None,
            "minutes": reading_minutes(body_html, lang),
            "body": body_html,
            "toc": toc_html(tokens),
            "path": url_path(section, slug, lang=lang),
            "url": absolute(url_path(section, slug, lang=lang)),
            "label": SECTION_LABEL[section][lang],
            "badge_class": BADGE_CLASS[section],
            "product_label": PRODUCTS[product]["label"] if product else None,
        }
    for slug, editions in posts.items():
        if "en" not in editions:
            raise SystemExit(f"content/posts/{slug}: an English edition is required")
        editions["en"]["translation"] = editions.get("zh")
        if "zh" in editions:
            editions["zh"]["translation"] = editions["en"]
    return posts


def load_profile() -> dict:
    path = CONTENT / "profile.yml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def profile_for(lang: str) -> dict:
    data = load_profile()

    def pick(key):
        value = data.get(key)
        if isinstance(value, dict):
            return value.get(lang) or value.get("en") or ""
        return value

    return {
        "name": data.get("name", SITE["brand"]),
        "handle": data.get("handle", ""),
        "avatar": data.get("avatar", ""),
        "tagline": pick("tagline"),
        "intro": pick("intro"),
        "keywords": pick("keywords") or [],
        "now": pick("now") or [],
        "links": data.get("links") or [],
    }


def load_pages() -> dict[str, dict[str, dict]]:
    pages: dict[str, dict[str, dict]] = {}
    pattern = re.compile(r"^(?P<slug>[a-z0-9-]+)\.(?P<lang>en|zh)\.md$")
    for path in sorted((CONTENT / "pages").glob("*.md")):
        match = pattern.match(path.name)
        if not match:
            raise SystemExit(f"{path}: expected <slug>.en.md or <slug>.zh.md")
        slug, lang = match.group("slug"), match.group("lang")
        meta, body = split_front_matter(path.read_text(encoding="utf-8"), path)
        if meta.get("draft"):
            continue
        body_html, _ = md_render(body)
        pages.setdefault(slug, {})[lang] = {
            "slug": slug,
            "lang": lang,
            "title": meta["title"],
            "description": meta.get("description", ""),
            "body": body_html,
            "path": url_path(slug, lang=lang),
            "inputs": meta.get("inputs") or [],
        }
    return pages


# --------------------------------------------------------------------------- #
# structured data
# --------------------------------------------------------------------------- #

def org_node() -> dict:
    return {
        "@type": "Organization",
        "@id": SITE["main"] + "/#organization",
        "name": "AIDDHub",
        "url": SITE["main"],
        "email": SITE["email"],
        "description": "Desktop software for molecular modelling, docking and SAR analysis.",
    }


def jsonld_for_home(lang: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": SITE["url"] + "/#website",
                "url": absolute(url_path(lang=lang) if lang == "en" else "/zh/"),
                "name": SITE["name"],
                "inLanguage": "en" if lang == "en" else "zh-CN",
                "publisher": {"@id": SITE["main"] + "/#organization"},
            },
            org_node(),
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def jsonld_for_list(section: str, lang: str, posts: list[dict]) -> str:
    path = url_path(section, lang=lang)
    crumbs = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": absolute("/")},
        {"@type": "ListItem", "position": 2, "name": SECTION_TEXT[section][lang]["title"], "item": absolute(path)},
    ]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": absolute(path),
                "url": absolute(path),
                "name": SECTION_TEXT[section][lang]["title"],
                "description": SECTION_TEXT[section][lang]["blurb"],
                "inLanguage": "en" if lang == "en" else "zh-CN",
                "isPartOf": {"@id": SITE["url"] + "/#website"},
                "mainEntity": {
                    "@type": "ItemList",
                    "itemListElement": [
                        {"@type": "ListItem", "position": index + 1, "url": post["url"], "name": post["title"]}
                        for index, post in enumerate(posts)
                    ],
                },
            },
            {"@type": "BreadcrumbList", "itemListElement": crumbs},
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def jsonld_for_post(post: dict, section: str) -> str:
    node = {
        "@type": "TechArticle" if section == "tutorials" else "Article",
        "@id": post["url"] + "#article",
        "headline": post["title"],
        "description": post["description"],
        "datePublished": post["iso"],
        "dateModified": post["updated_iso"] or post["iso"],
        "inLanguage": "en" if post["lang"] == "en" else "zh-CN",
        "mainEntityOfPage": post["url"],
        "articleSection": SECTION_TEXT[section][post["lang"]]["title"],
        "keywords": ", ".join(post["tags"]),
        "author": {"@type": "Organization", "name": "AIDDHub", "url": SITE["main"]},
        "publisher": org_node(),
        "isPartOf": {"@id": SITE["url"] + "/#website"},
    }
    crumbs = [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": absolute("/" if post["lang"] == "en" else "/zh/")},
        {"@type": "ListItem", "position": 2, "name": SECTION_TEXT[section][post["lang"]]["title"],
         "item": absolute(url_path(section, lang=post["lang"]))},
        {"@type": "ListItem", "position": 3, "name": post["title"], "item": post["url"]},
    ]
    data = {"@context": "https://schema.org", "@graph": [node, {"@type": "BreadcrumbList", "itemListElement": crumbs}]}
    return json.dumps(data, ensure_ascii=False, indent=2)


def jsonld_for_page(name: str, lang: str, title: str, description: str) -> str:
    path = url_path(name, lang=lang)
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "AboutPage",
                "@id": absolute(path),
                "url": absolute(path),
                "name": title,
                "description": description,
                "inLanguage": "en" if lang == "en" else "zh-CN",
                "isPartOf": {"@id": SITE["url"] + "/#website"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home",
                     "item": absolute("/" if lang == "en" else "/zh/")},
                    {"@type": "ListItem", "position": 2, "name": title, "item": absolute(path)},
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #

class Builder:
    def __init__(self, dest: Path):
        self.dest = dest
        self.posts = load_posts()
        self.pages = load_pages()
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES)),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.globals.update(
            site=SITE,
            section_href=self.section_href,
        )
        self.version = asset_version()
        self.written: list[str] = []
        self.images: list[str] = []

    # -- link helpers ------------------------------------------------------ #

    def section_href(self, section: str, lang: str | None = None) -> str:
        return url_path(section, lang=lang or "en")

    def base_context(self, lang: str, nav_active: str) -> dict:
        home = url_path(lang=lang) if lang == "en" else "/zh/"
        nav = [
            {"key": "home", "href": home, "label": TEXT[lang]["nav"]["home"]},
            {"key": "notes", "href": self.section_href("notes", lang), "label": TEXT[lang]["nav"]["notes"]},
            {"key": "tutorials", "href": self.section_href("tutorials", lang),
             "label": TEXT[lang]["nav"]["tutorials"]},
            {"key": "projects", "href": url_path("projects", lang=lang), "label": TEXT[lang]["nav"]["projects"]},
            {"key": "about", "href": url_path("about", lang=lang), "label": TEXT[lang]["nav"]["about"]},
        ]
        strings = {}
        strings.update(TEXT[lang]["home"])
        strings.update(TEXT[lang]["list"])
        strings.update(TEXT[lang]["post"])
        return {
            "lang_attr": TEXT[lang]["lang_attr"],
            "og_locale": TEXT[lang]["og_locale"],
            "nav": nav,
            "nav_text": TEXT[lang]["nav"],
            "nav_active": nav_active,
            "home_href": home,
            "about_href": url_path("about", lang=lang),
            "projects_href": url_path("projects", lang=lang),
            "asset_version": self.version,
            "footer": TEXT[lang]["footer"],
            "footer_blurb": TEXT[lang]["footer_blurb"],
            "tagline": TEXT[lang]["tagline"],
            "strings": strings,
            "section_href": lambda key: self.section_href(key, lang),
            "alternates": [],
            "lang_switch": None,
            "jsonld": None,
            "og_type": "website",
            "og_title": None,
            "og_image": None,
            "body_class": "",
        }

    @staticmethod
    def alternates_for(paths: dict[str, str]) -> list[tuple[str, str]]:
        pairs = []
        if "en" in paths:
            pairs.append(("en", absolute(paths["en"])))
        if "zh" in paths:
            pairs.append(("zh-CN", absolute(paths["zh"])))
        if "en" in paths:
            pairs.append(("x-default", absolute(paths["en"])))
        return pairs

    def lang_switch(self, paths: dict[str, str], lang: str) -> dict | None:
        other = "zh" if lang == "en" else "en"
        if other not in paths:
            return None
        return {
            "href": paths[other],
            "hreflang": TEXT[other]["lang_attr"],
            "label": "中文" if other == "zh" else "English",
        }

    def render(self, template: str, rel: str, **context) -> None:
        page = self.env.get_template(template).render(**context)
        self.written.append(write(self.dest, rel, page))

    def make_og(self, rel: str, *, title: str, label: str, footer: str, lang: str) -> str | None:
        if og_image is None:
            return None
        try:
            og_image.render(title=title, label=label, footer=footer, lang=lang, out=self.dest / rel)
        except Exception as exc:  # never fail a build over a card
            print(f"warning: og image {rel} failed: {exc}")
            return None
        self.images.append(rel)
        return SITE["url"] + "/" + rel

    # -- pages ------------------------------------------------------------- #

    def build_home(self, lang: str) -> None:
        home = url_path(lang=lang) if lang == "en" else "/zh/"
        posts = sorted(
            (p[lang] for p in self.posts.values() if lang in p),
            key=lambda item: item["date"], reverse=True,
        )
        other_paths = {"en": "/"}
        if any("zh" in p for p in self.posts.values()):
            other_paths["zh"] = "/zh/"
        context = self.base_context(lang, "home")
        profile = profile_for(lang)
        context.update(
            title=f"{profile['name']} — computational chemistry notes"
                  if lang == "en" else f"{profile['name']} — 计算化学笔记",
            description=profile["intro"] or SITE["name"],
            canonical=absolute(home),
            alternates=self.alternates_for(other_paths),
            lang_switch=self.lang_switch(other_paths, lang),
            jsonld=jsonld_for_home(lang),
            recent=posts,
            profile=profile,
            section_href=lambda key: self.section_href(key, lang),
        )
        context["og_image"] = self.make_og(
            f"assets/og/home-{lang}.png",
            title=profile["name"],
            label=SITE["tagline"],
            footer="aiddhub.github.io",
            lang=lang,
        )
        self.render("home.html", f"{'zh/' if lang == 'zh' else ''}index.html", **context)

    def build_list(self, section: str, lang: str) -> None:
        posts = sorted(
            (p[lang] for p in self.posts.values() if lang in p and p[lang]["section"] == section),
            key=lambda item: item["date"], reverse=True,
        )
        paths = {}
        for edition in ("en", "zh"):
            if any(edition in p and p[edition]["section"] == section for p in self.posts.values()):
                paths[edition] = url_path(section, lang=edition)
        context = self.base_context(lang, section)
        context.update(
            title=f"{SECTION_TEXT[section][lang]['title']} — {SITE['name']}",
            description=SECTION_TEXT[section][lang]["blurb"],
            canonical=absolute(url_path(section, lang=lang)),
            alternates=self.alternates_for(paths),
            lang_switch=self.lang_switch(paths, lang),
            jsonld=jsonld_for_list(section, lang, posts),
            posts=posts,
            section=SECTION_TEXT[section][lang],
            section_href=lambda key: self.section_href(key, lang),
        )
        rel = f"{'zh/' if lang == 'zh' else ''}{section}/index.html"
        self.render("list.html", rel, **context)

    def build_post(self, edition: dict) -> None:
        slug = edition["slug"]
        lang = edition["lang"]
        section = edition["section"]
        siblings = sorted(
            (p[lang] for p in self.posts.values() if lang in p and p[lang]["section"] == section),
            key=lambda item: item["date"], reverse=True,
        )
        index = next(i for i, item in enumerate(siblings) if item["slug"] == slug)
        prev_post = siblings[index + 1] if index + 1 < len(siblings) else None
        next_post = siblings[index - 1] if index > 0 else None

        paths = {}
        for code in ("en", "zh"):
            if code in self.posts[slug]:
                paths[code] = self.posts[slug][code]["path"]

        context = self.base_context(lang, section)
        context.update(
            title=f"{edition['title']} — {SITE['name']}",
            description=edition["description"],
            canonical=edition["url"],
            alternates=self.alternates_for(paths),
            lang_switch=self.lang_switch(paths, lang),
            jsonld=jsonld_for_post(edition, section),
            og_type="article",
            og_title=edition["title"],
            post=edition,
            section_title=SECTION_TEXT[section][lang]["title"],
            section_href=lambda key: self.section_href(key, lang),
            toc=edition["toc"],
            prev_post=prev_post,
            next_post=next_post,
            body_class="article-page",
        )
        label = edition["label"]
        if edition["product_label"]:
            label = f"{label} · {edition['product_label']}"
        context["og_image"] = self.make_og(
            f"assets/og/{slug}-{lang}.png",
            title=edition["title"],
            label=label,
            footer=edition["date_label"],
            lang=lang,
        )
        rel = f"{'zh/' if lang == 'zh' else ''}{section}/{slug}/index.html"
        self.render("post.html", rel, **context)

    def build_page(self, name: str, lang: str, data: dict) -> None:
        paths = {code: url_path(name, lang=code) for code in ("en", "zh") if code in self.pages.get(name, {})}
        context = self.base_context(lang, name)
        context.update(
            title=f"{data['title']} — {SITE['name']}",
            description=data["description"],
            canonical=absolute(url_path(name, lang=lang)),
            alternates=self.alternates_for(paths),
            lang_switch=self.lang_switch(paths, lang),
            jsonld=jsonld_for_page(name, lang, data["title"], data["description"]),
            page=data,
            section_href=lambda key: self.section_href(key, lang),
        )
        rel = f"{'zh/' if lang == 'zh' else ''}{name}/index.html"
        self.render("page.html", rel, **context)

    def build_404(self) -> None:
        context = self.base_context("en", "")
        context.update(
            title=f"Page not found — {SITE['name']}",
            description="That page does not exist.",
            canonical=absolute("/404.html"),
            lang_switch=None,
            strings={"text": TEXT["en"]["notfound"]["text"], "home": TEXT["en"]["notfound"]["home"]},
        )
        self.render("notfound.html", "404.html", **context)

    # -- feeds ------------------------------------------------------------- #

    def build_sitemap(self) -> None:
        entries = []

        def add(paths: dict[str, str], lastmod: str) -> None:
            alts = self.alternates_for(paths)
            links = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{code}" href="{href}" />' for code, href in alts
            )
            for path in paths.values():
                entries.append(
                    f"  <url>\n    <loc>{absolute(path)}</loc>\n    <lastmod>{lastmod}</lastmod>{links}\n  </url>"
                )

        today = date.today().isoformat()
        home_paths = {"en": "/"}
        if any("zh" in p for p in self.posts.values()):
            home_paths["zh"] = "/zh/"
        add(home_paths, today)

        for section in SECTIONS:
            paths = {}
            for code in ("en", "zh"):
                if any(code in p and p[code]["section"] == section for p in self.posts.values()):
                    paths[code] = url_path(section, lang=code)
            if paths:
                add(paths, today)

        for slug, editions in sorted(self.posts.items()):
            paths = {code: ed["path"] for code, ed in editions.items() if code in ("en", "zh")}
            lastmod = max(ed["updated"] or ed["date"] for ed in editions.values()).isoformat()
            add(paths, lastmod)

        for name, editions in sorted(self.pages.items()):
            paths = {code: ed["path"] for code, ed in editions.items() if code in ("en", "zh")}
            if paths:
                add(paths, today)

        body = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(entries)
            + "\n</urlset>\n"
        )
        self.written.append(write(self.dest, "sitemap.xml", body))

    def build_feed(self) -> None:
        posts = sorted(
            (p["en"] for p in self.posts.values()),
            key=lambda item: item["date"], reverse=True,
        )[:20]
        stamp = (posts[0]["updated"] or posts[0]["date"]).isoformat() + "T00:00:00Z" if posts else \
            datetime.now(timezone.utc).isoformat()
        items = []
        for post in posts:
            items.append(
                "  <entry>\n"
                f"    <title>{html.escape(post['title'])}</title>\n"
                f"    <link href=\"{post['url']}\"/>\n"
                f"    <id>{post['url']}</id>\n"
                f"    <updated>{(post['updated'] or post['date']).isoformat()}T00:00:00Z</updated>\n"
                f"    <published>{post['date'].isoformat()}T00:00:00Z</published>\n"
                f"    <summary>{html.escape(post['description'])}</summary>\n"
                "  </entry>"
            )
        body = (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<feed xmlns="http://www.w3.org/2005/Atom">\n'
            f"  <title>{html.escape(SITE['name'])}</title>\n"
            f'  <link href="{SITE["url"]}/feed.xml" rel="self"/>\n'
            f'  <link href="{SITE["url"]}/"/>\n'
            f"  <id>{SITE['url']}/</id>\n"
            f"  <updated>{stamp}</updated>\n"
            "  <author><name>AIDDHub</name><email>support@aiddhub.com</email></author>\n"
            + "\n".join(items)
            + "\n</feed>\n"
        )
        self.written.append(write(self.dest, "feed.xml", body))

    def build_robots(self) -> None:
        body = (
            "User-agent: *\n"
            "Allow: /\n"
            "\n"
            f"Sitemap: {SITE['url']}/sitemap.xml\n"
        )
        self.written.append(write(self.dest, "robots.txt", body))

    # -- entry ------------------------------------------------------------- #

    def build(self) -> list[str]:
        clean_output(self.dest)
        missing = sorted(slug for slug, editions in self.posts.items() if "zh" not in editions)
        if missing:
            print("warning: no Chinese edition for: " + ", ".join(missing))
        has_zh = any("zh" in editions for editions in self.posts.values())
        for lang in ("en", "zh"):
            if lang == "zh" and not has_zh:
                continue
            self.build_home(lang)
            for section in SECTIONS:
                self.build_list(section, lang)
        for editions in self.posts.values():
            for edition in editions.values():
                if edition["lang"] in ("en", "zh"):
                    self.build_post(edition)
        for name, editions in self.pages.items():
            for edition in editions.values():
                self.build_page(name, edition["lang"], edition)
        self.build_404()
        self.build_sitemap()
        self.build_feed()
        self.build_robots()
        return self.written


# --------------------------------------------------------------------------- #
# scaffolding
# --------------------------------------------------------------------------- #

POST_TEMPLATE = """---
title: "Your title here"
description: "One or two sentences that make someone click. 120-160 characters."
date: {today}
section: {section}
product: molstudio
tags: [docking]
---

Opening paragraph: the task, who it is for, and what they end up with.

## What you need

- MolStudio {version}
- A PDB file (or an SDF library)

## Step 1 — Prepare the receptor

Write the walkthrough as numbered sections. Every `##` heading becomes an entry in
the table of contents.

## Step 2 — Run the job

```text
File -> Import -> PDB
```

## Reading the result

| Column | Meaning |
|---|---|
| Ligand | Name from the record title |
| Affinity | Vina score, kcal/mol |

> A tip that saves people a day.
"""


def scaffold(slug: str, section: str) -> None:
    target = CONTENT / "posts" / f"{slug}.en.md"
    if target.exists():
        raise SystemExit(f"{target} already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        POST_TEMPLATE.format(today=date.today().isoformat(), section=section, version="v1.0"),
        encoding="utf-8",
        newline="\n",
    )
    print(f"created {target}")
    print("Next: write the body, then run  python tools/build_site.py")


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify the committed HTML matches the sources")
    parser.add_argument("--new", metavar="SLUG", help="create content/posts/<slug>.en.md")
    parser.add_argument("--section", default="tutorials", choices=SECTIONS)
    args = parser.parse_args(argv)

    if args.new:
        scaffold(args.new, args.section)
        return 0

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            built = Builder(Path(tmp)).build()
            stale = []
            for rel in built:
                current = ROOT / rel
                fresh = (Path(tmp) / rel).read_bytes()
                if not current.exists() or current.read_bytes() != fresh:
                    stale.append(rel)
            if stale:
                print("stale build output:")
                for rel in stale:
                    print("  ", rel)
                print("run: python tools/build_site.py")
                return 1
        print(f"build is up to date ({len(built)} files)")
        return 0

    builder = Builder(ROOT)
    written = builder.build()
    print(f"wrote {len(written)} files and {len(builder.images)} social cards")
    for rel in written:
        print("  ", rel)
    return 0

if __name__ == "__main__":
    sys.exit(main())
