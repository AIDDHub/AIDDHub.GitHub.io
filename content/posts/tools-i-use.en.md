---
title: "A working tool list"
short_title: "A working tool list"
description: "What is actually installed and used day to day: RDKit, ChEMBL, Qt, Obsidian, DataWarrior, PyMOL, Cloudflare — plus the tools that were dropped and why."
date: 2026-09-30
section: notes
tags: [tooling, workflow]
---

Tool lists age badly, so this one comes with a date and a rule: only software opened in the last month, and
only software that would be missed.

## Chemistry

**RDKit.** The default answer for anything structural, and deservedly so. It is the quickest way to check a
canonicalisation, prototype a descriptor, or answer "what does this SMARTS actually match" before committing
it to code. Nothing else comes close on format and reaction coverage.

**ChEMBL.** Not software, a dataset — but it is the first place to look when a real series is needed to test
an idea against. Public data with plausible SAR beats a synthetic set every time.

**DataWarrior.** Still the fastest way to open an unfamiliar SDF and look at it. Free, occasionally ugly, and
very good at the one thing needed at the start of a project: seeing the whole set.

**PyMOL.** For figures, mainly. Not because it is pleasant to use, but because every reviewer recognises its
output.

**Open Babel.** Occasionally, for a format conversion RDKit refuses. It has not been the first choice for
years, and it is still installed.

## Building

**Python** for everything that is not the interface. It is the language of the ecosystem, and fighting that is
a hobby rather than a strategy.

**Qt** for the desktop layer. Mature and predictable, and it handles the unglamorous parts — docking panels,
tables, high-DPI scaling — without drama.

**C++ only where measured.** Profile first, rewrite second. Half the performance problems chased so far turned
out to be a Python loop over 2,000 molecules, not an algorithm.

**GitHub Actions** for the checks that catch mistakes: does the site still build, do the tests still pass on a
machine that is not this one.

## Writing and thinking

**Obsidian**, one folder of plain Markdown, no plugins that matter. If it stopped working tomorrow, the files
would still be there, which is the entire point.

**A paper notebook** for anything with a structure in it. Drawing a mechanism on a trackpad is a way to avoid
thinking.

## Tools that were dropped

- **Excel as a database.** It still gets opened; it no longer holds the only copy of an assay table.
- **Jupyter notebooks as the product.** Excellent for exploring, poor for anything that has to run again next
  month. Once a notebook has users, it wants to be a script with an argument parser.
- **Docker for desktop apps.** It solves a packaging problem that does not exist here and creates a support
  problem that does.
- **A second monitor full of dashboards.** Replaced with one page of numbers that actually get checked.

## The one that surprised us

Cloudflare. The expectation was a CDN; what it turned out to provide was a place to put a static site, a
download bucket and a mail forwarder for less than the price of a coffee a month, with no server to patch. For
a small studio that is the entire infrastructure budget, and it has not fallen over yet.

## What is still missing

A good way to look at a 3D structure and an assay table at the same time without alt-tabbing. That is roughly
the reason MolStudio exists, and it is still not fully solved.
