---
title: "The tools I actually use"
short_title: "Tools I actually use"
description: "A working list, with the things I stopped using and why: RDKit, ChEMBL, Qt, Obsidian, DataWarrior, PyMOL, Cloudflare, and one very old spreadsheet."
date: 2026-09-30
section: notes
tags: [tooling, workflow]
---

Tool lists age badly, so this one comes with a date and a rule: only things I opened in the last month, and
only things I would miss.

## Chemistry

**RDKit.** The default answer for anything structural, and deservedly so. I reach for it to check a
canonicalisation, to prototype a descriptor, or to answer "what does this SMARTS actually match" before
committing it to code. Nothing else comes close for the breadth of formats and reactions.

**ChEMBL.** Not software, a dataset, but it is the first place I look when I need a real series to test an
idea against. A public dataset with plausible SAR beats a synthetic one every time.

**DataWarrior.** Still the fastest way to open an unfamiliar SDF and look at it. Free, ugly in places, and
extremely good at the one thing I need at the start of a project: seeing the whole set.

**PyMOL.** For figures. Not because it is pleasant, but because every reviewer recognises its output.

**Open Babel.** Occasionally, for a format conversion RDKit refuses. It has been years since it was my first
choice, and it is still on the machine.

## Building

**Python** for everything that is not the UI. It is the language of the ecosystem, and fighting that is a
hobby, not a strategy.

**Qt** for the desktop layer. Mature, predictable, and it does the boring things — docking panels, tables,
high-DPI scaling — without drama.

**C++ only where measured.** Profiling first, rewriting second. Half the "performance problem" I have chased
turned out to be a Python loop over 2,000 molecules, not an algorithm.

**GitHub Actions** for the checks that catch me: does the site still build, do the tests still pass on a
machine that is not mine.

## Writing and thinking

**Obsidian**, one folder of plain Markdown, no plugins that matter. If it stopped working tomorrow I would
still have the files, which is the entire point.

**A paper notebook** for anything with a structure in it. Drawing a mechanism on a trackpad is a way to avoid
thinking.

## Things I stopped using

- **Excel as a database.** I still open it; I no longer let it hold the only copy of an assay table.
- **Jupyter notebooks as the product.** Excellent for exploring, terrible for anything that has to run twice
  next month. The moment a notebook has users, it wants to be a script with an argument parser.
- **Docker for desktop apps.** It solves a packaging problem I do not have and creates a support problem I do.
- **A second monitor full of dashboards.** I replaced it with one page of numbers I actually check.

## The one that surprised me

Cloudflare. I expected a CDN; what I got was a place to put a static site, a download bucket and a mail
forwarder for less than the cost of a coffee a month, with no server to patch. For a one-person software
studio that is the entire infrastructure budget, and it has not fallen over yet.

## What is missing

A good way to look at a 3D structure and an assay table at the same time without alt-tabbing. That is roughly
the reason MolStudio exists, and I still have not fully solved it.
