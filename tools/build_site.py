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
    section      tutorials | cases
    product      molstudio | molinsight | both
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

SECTIONS = ("tutorials", "cases")

SECTION_TEXT = {
    "tutorials": {
        "en": {
            "title": "Tutorials",
            "blurb": "Step-by-step walkthroughs for MolStudio and MolInsight. Each one starts from a real task, "
                     "shows the clicks, and ends with a figure or a table you can put in a report.",
        },
        "zh": {
            "title": "教程",
            "blurb": "MolStudio 与 MolInsight 的分步操作指南。每篇都从实际任务出发，写清点击路径，"
                     "最后给出可以直接放进汇报的图或表。",
        },
    },
    "cases": {
        "en": {
            "title": "Case studies",
            "blurb": "Longer evaluations: how a tool behaves on a real series, where it saves time, and where "
                     "it does not. Comparisons include the trade-offs rather than a feature checklist.",
        },
        "zh": {
            "title": "案例",
            "blurb": "更长的评测：同一批数据在不同工具里的表现、省时间的地方，以及不适合的地方。"
                     "对比会写清取舍，而不是只堆功能清单。",
        },
    },
}

TEXT = {
    "en": {
        "lang_attr": "en",
        "og_locale": "en_US",
        "tagline": "Tutorials & case studies",
        "nav": {"home": "Home", "tutorials": "Tutorials", "cases": "Case studies", "about": "About"},
        "footer": {"resources": "Resources", "products": "Products", "pricing": "Pricing", "download": "Download"},
        "footer_blurb": "Hands-on notes on molecular modelling, docking and SAR analysis, written by the people "
                        "who build MolStudio and MolInsight.",
        "home": {
            "eyebrow": "Notes from the developers",
            "h1_a": "Practical tutorials for",
            "h1_b": "molecular modelling",
            "lede": "Worked examples, honest comparisons and step-by-step recipes for MolStudio and MolInsight "
                    "— the desktop apps for docking, matched molecular pairs, R-groups, scaffolds and QSAR. "
                    "Everything here runs on a normal Windows or Linux machine, with no Python environment to set up.",
            "cta_primary": "Browse tutorials",
            "cta_secondary": "Get the apps",
            "card_title": "What you'll find here",
            "card_items": [
                ["Docking, end to end.", "Receptor prep, box setup, Vina, 2D interaction diagrams."],
                ["SAR that survives review.", "MMP with p-values, R-group matrices, scaffold vs side-chain."],
                ["Tool comparisons.", "Where each app fits next to DataWarrior, RDKit or a spreadsheet."],
            ],
            "stats": [["10 min", "first docking job"], ["47", "chart types"], ["35", "molecular descriptors"],
                      ["0", "lines of code"]],
            "featured_title": "Start with these",
            "featured_sub": "The three walkthroughs readers ask for first.",
            "see_all": "All tutorials",
            "latest_title": "Latest notes",
            "latest_sub": "New walkthroughs, updates and answers to reader questions.",
            "products_title": "The software behind these notes",
            "products_sub": "Two desktop apps, sold as one-time licences with a free tier.",
            "product_molstudio": "Molecular modelling workstation: 3D builder, protein preparation, docking with "
                                 "AutoDock Vina, 2D interaction diagrams, plots and saved sessions.",
            "product_molinsight": "SAR analysis workbench: 47 chart types, matched molecular pairs, R-group matrices, "
                                  "clustering and SOM, QSAR with an applicability domain.",
            "product_page": "Product page",
            "product_download": "Download",
            "about_title": "About AIDDHub",
            "about_sub": "An independent studio building desktop tools for medicinal chemistry and structural biology.",
            "about_cta": "Read more",
        },
        "list": {"filter_all": "All", "empty": "Nothing published in this section yet."},
        "post": {"min_read": "min read", "updated": "Updated", "toc": "On this page",
                 "previous": "Previous", "next": "Next",
                 "cta_title": "Try it on your own data",
                 "cta_text": "The free tier covers everything in this walkthrough, with no time limit.",
                 "cta_button": "Download"},
        "notfound": {"text": "That page does not exist. The tutorials index is probably what you want.",
                     "home": "Back to the homepage"},
    },
    "zh": {
        "lang_attr": "zh-CN",
        "og_locale": "zh_CN",
        "tagline": "教程与案例",
        "nav": {"home": "首页", "tutorials": "教程", "cases": "案例", "about": "关于"},
        "footer": {"resources": "内容", "products": "软件", "pricing": "价格", "download": "下载"},
        "footer_blurb": "分子建模、分子对接与构效关系分析的实操笔记，作者是 MolStudio 与 MolInsight 的开发者。",
        "home": {
            "eyebrow": "开发者笔记",
            "h1_a": "分子建模与",
            "h1_b": "构效分析实操",
            "lede": "MolStudio 与 MolInsight 的完整操作示例：对接、骨架与 R 基团、聚类与相似性、QSAR。"
                    "所有步骤都在普通 Windows / Linux 机器上完成，不需要配置 Python 环境。",
            "cta_primary": "查看教程",
            "cta_secondary": "了解软件",
            "card_title": "这里有什么",
            "card_items": [
                ["从准备到成图。", "受体准备、盒子设置、Vina 对接、2D 相互作用图。"],
                ["经得起追问的 SAR。", "带 p 值的 MMP、R 基团矩阵、骨架与侧链分析。"],
                ["工具对比。", "与 DataWarrior、RDKit、Excel 分工的取舍。"],
            ],
            "stats": [["10 分钟", "首个对接任务"], ["47", "种图表"], ["35", "个分子描述符"], ["0", "行代码"]],
            "featured_title": "从这里开始",
            "featured_sub": "读者问得最多的三篇。",
            "see_all": "全部教程",
            "latest_title": "最新笔记",
            "latest_sub": "新增的实操、更新记录与读者提问。",
            "products_title": "这些笔记背后的软件",
            "products_sub": "两个桌面软件，一次性授权，免费版可长期使用。",
            "product_molstudio": "分子建模工作站：3D 构建、蛋白准备、AutoDock Vina 对接、2D 相互作用图、绘图与会话保存。",
            "product_molinsight": "构效分析工作台：47 种图表、MMP、R 基团矩阵、聚类与 SOM、带适用域的 QSAR。",
            "product_page": "产品页",
            "product_download": "下载",
            "about_title": "关于 AIDDHub",
            "about_sub": "独立软件工作室，专注药物化学与结构生物学的桌面工具。",
            "about_cta": "了解更多",
        },
        "list": {"filter_all": "全部", "empty": "这个分类下还没有内容。"},
        "post": {"min_read": "分钟阅读", "updated": "更新于", "toc": "本页目录",
                 "previous": "上一篇", "next": "下一篇",
                 "cta_title": "用自己的数据试一次",
                 "cta_text": "本文用到的功能都包含在免费版里，没有试用期限制。",
                 "cta_button": "下载"},
        "notfound": {"text": "这个页面不存在。你可能想找的是教程列表。", "home": "返回首页"},
    },
}

BADGE_CLASS = {"tutorials": "tutorial", "cases": "case"}
SECTION_LABEL = {
    "tutorials": {"en": "Tutorial", "zh": "教程"},
    "cases": {"en": "Case study", "zh": "案例"},
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
        section = meta.get("section", "tutorials")
        if section not in SECTIONS:
            raise SystemExit(f"{path}: section must be one of {SECTIONS}")
        product = meta.get("product", "both")
        if product not in PRODUCTS:
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
            "product_label": PRODUCTS[product]["label"],
        }
    for slug, editions in posts.items():
        if "en" not in editions:
            raise SystemExit(f"content/posts/{slug}: an English edition is required")
        editions["en"]["translation"] = editions.get("zh")
        if "zh" in editions:
            editions["zh"]["translation"] = editions["en"]
    return posts


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
            {"key": "tutorials", "href": self.section_href("tutorials", lang),
             "label": TEXT[lang]["nav"]["tutorials"]},
            {"key": "cases", "href": self.section_href("cases", lang), "label": TEXT[lang]["nav"]["cases"]},
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
        tutorials = [p for p in posts if p["section"] == "tutorials"]
        featured = tutorials[:3] if tutorials else posts[:3]
        other_paths = {"en": "/"}
        if any("zh" in p for p in self.posts.values()):
            other_paths["zh"] = "/zh/"
        context = self.base_context(lang, "home")
        context.update(
            title=f"{SITE['name']} — molecular modelling tutorials for MolStudio and MolInsight"
                  if lang == "en" else f"{SITE['name']} — MolStudio / MolInsight 实操教程",
            description=("Step-by-step tutorials and case studies for MolStudio and MolInsight: docking with "
                         "AutoDock Vina, matched molecular pairs, R-groups, scaffolds, clustering and QSAR.")
                        if lang == "en" else
                        ("MolStudio 与 MolInsight 的分步教程与案例：AutoDock Vina 对接、MMP、R 基团、"
                         "骨架分析、聚类与 QSAR。"),
            canonical=absolute(home),
            alternates=self.alternates_for(other_paths),
            lang_switch=self.lang_switch(other_paths, lang),
            jsonld=jsonld_for_home(lang),
            featured=featured,
            recent=posts,
            section_href=lambda key: self.section_href(key, lang),
        )
        context["og_image"] = self.make_og(
            f"assets/og/home-{lang}.png",
            title=f"{TEXT[lang]['home']['h1_a']} {TEXT[lang]['home']['h1_b']}",
            label=TEXT[lang]["tagline"],
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
            products=[
                {"key": "molstudio", "label": "MolStudio"},
                {"key": "molinsight", "label": "MolInsight"},
            ],
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

        product = PRODUCTS[edition["product"]]
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
            cta={
                "title": TEXT[lang]["post"]["cta_title"],
                "text": TEXT[lang]["post"]["cta_text"],
                "button": f"{TEXT[lang]['post']['cta_button']} {product['label']}",
                "href": product["href"] + "#download",
            },
            body_class="article-page",
        )
        context["og_image"] = self.make_og(
            f"assets/og/{slug}-{lang}.png",
            title=edition["title"],
            label=f"{edition['label']} · {edition['product_label']}",
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
