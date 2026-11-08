---
title: "Projects"
description: "Two desktop programs for medicinal chemistry, the blog you are reading, and an honest list of what is not built yet."
---

Everything here is built by one person, on Windows and Linux, and runs offline.

## MolStudio

A molecular modelling and docking workstation.

- 3D builder, receptor preparation, AutoDock Vina docking
- 2D interaction diagrams with distances, π–π stacking and salt bridges
- Plots, sessions you can reopen, SDF / CSV / PNG / SVG export
- Windows and Linux, native installer

**Status:** v1.0 shipped. Free tier with no time limit; a one-time licence unlocks the full workflow.

[Product page](https://www.aiddhub.com/molstudio) · [Download](https://www.aiddhub.com/molstudio#download)

## MolInsight

An SAR analysis workbench for the part of the week when someone asks *why* a substituent is better.

- 47 chart types, including small multiples, facets and 3D
- Matched molecular pairs with pair counts, spread and significance
- R-group matrices, scaffold and side-chain analysis
- Clustering, similarity networks and self-organising maps
- QSAR with ridge / PLS / kernel ridge / KNN / GBM, plus applicability domain

**Status:** v1.0 shipped. Free tier handles 100 compounds per session; a one-time licence removes the limit.

[Product page](https://www.aiddhub.com/molinsight) · [Download](https://www.aiddhub.com/molinsight#download)

## This site

Static HTML generated from Markdown by a small Python script. No framework, no database, no analytics script.
The build is checked in CI so the published pages cannot drift from the sources.

The source is public: [github.com/AIDDHub/AIDDHub.github.io](https://github.com/AIDDHub/AIDDHub.github.io).

## What is not built yet

Saying this out loud is cheaper than implying otherwise.

- **macOS.** Not planned for the near term. A proper port is a second platform to support, not a recompile.
- **A team edition.** No admin console, no SSO, no floating licences.
- **Cloud sync.** Deliberately absent. Files on disk, your backup policy.
- **A plugin API.** Would be nice; would also freeze interfaces I still want to change.

If one of those is a blocker for you, the honest answer is that this is not the right tool yet — and I would
rather say that now than after you have paid.
