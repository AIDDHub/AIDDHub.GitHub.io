---
title: "Why desktop software still makes sense for chemistry"
short_title: "Why desktop still makes sense"
description: "Web apps are the default for scientific software, and usually that is correct. This is about the cases where they are not: docking runs, large structure tables, and locked-down networks."
date: 2026-11-02
section: notes
tags: [desktop, software, opinion]
---

Web applications are the default for scientific software, and in most cases that is the right call: nothing to
install, one version for everyone, and a trivial deployment story.

There are still problems where that shape does not fit. Docking runs, large structure tables and workflows that
have to survive a locked-down network are the obvious ones. This note is about why the desktop is the better
answer there, and what it costs to choose it.

## The shape of the problem

A docking run is not a request. It is twenty minutes of CPU on one machine, with progress to watch, parameters
to adjust halfway through, and an output that is a folder of poses rather than a JSON response.

The same applies to a large compound table. Sorting, filtering and clustering 200,000 rows in a browser is
possible, but the moment the result needs to sit next to a plotting window for an hour, or feed a model that
takes four minutes, the browser stops being an advantage and becomes a constraint.

These workflows are local, iterative and compute-heavy. Desktop software is not nostalgia here; it matches the
shape of the work.

## What a local install buys

**No upload.** Structures, assay tables and models stay on the machine. For anyone working under a
confidentiality agreement — which is most people with a real series — that is a precondition, not a feature.

**It works offline and behind a firewall.** Industrial and academic networks are full of proxies that block
whatever a vendor needs. A signed installer is easier to approve than a domain to allowlist.

**No latency budget.** Opening a 50 MB SDF takes as long as the disk takes. Nothing has to be paginated to
protect a network round trip.

**It keeps working when the vendor's server does not.** A release from March still opens in November, on a
machine the developer has never seen.

## What it costs

The trade-offs are real and should be stated plainly.

- **Distribution is a tax.** Per-platform installers, code signing, a download host, and a support
  conversation every time an antivirus vendor changes its mind.
- **Updates are a negotiation.** With a web app everyone is on the current version. With a desktop app someone
  is always on the build from eighteen months ago, reporting a bug against code nobody remembers.
- **No telemetry means no data.** Problems are discovered by email, which is a slower feedback loop than any
  dashboard.
- **Nothing can be fixed remotely.** A hotfix becomes a rebuild, a re-upload and an email asking people to
  reinstall.

Those costs are why most new scientific software is a web app.

## Where the line is

The browser is a distribution channel, not a model for computation. When a tool is mostly a form, a dashboard
or a shared database, it belongs on the web. When the core of the tool is a molecule in a viewport and a solver
on the CPU, the browser becomes a wrapper around a native engine with extra steps.

That gives a simple rule: native program, ordinary files on disk, no account, no sync.

## The constraint worth keeping

There is one more argument, and it is not technical. A desktop program is finished when the user stops needing
it. There is no engagement metric, no retention curve, and no incentive to make the tool stickier than the
problem requires.

That constraint makes the design question smaller and easier to answer: does this help someone reach a
defensible answer today, and can they walk away afterwards?
