---
title: "Why I still ship desktop software in 2026"
short_title: "Why desktop software"
description: "Web apps are the default for scientific software. I keep writing desktop programs anyway — here is what that buys, what it costs, and why I stopped apologising for it."
date: 2026-11-02
section: notes
tags: [desktop, software, opinion]
featured: true
---

Every few months someone asks why MolStudio is not a web app. It is a fair question: the browser is where
software goes now, the deployment story is trivial, and nobody has to install anything.

I have built web things too. I still keep shipping desktop programs, and I would like to write down why,
including the parts that hurt.

## The chemistry decides more than the fashion

A docking run is not a request. It is twenty minutes of CPU on one machine, with progress you want to watch,
parameters you want to tweak halfway through, and an output that is a folder of poses, not a JSON blob.

The same is true of a 200,000-compound table: sorting, filtering and clustering it in the browser is possible,
but the moment the user wants to drag it into a plotting window on a second monitor, or run a model that takes
four minutes, the browser stops being an advantage and starts being a constraint.

The workflows I care about are local, iterative and compute-heavy. Desktop is not nostalgia here; it is the
shape of the problem.

## What a local install actually buys

**No upload.** Structures, assay tables and models stay on the machine. For anyone working under a
confidentiality agreement — which is most people with a real series — that is not a feature, it is the
precondition for using the tool at all.

**It works on a plane, in a basement, and behind a hospital firewall.** Industrial and academic networks are
full of proxies that block whatever the vendor needs. A file that installs and runs is easier to approve than
a domain that has to be allowlisted.

**No latency budget.** Opening a 50 MB SDF takes as long as the disk takes. Nothing has to be paginated for
the sake of a network round trip.

**The software keeps working when my server does not.** This one is personal. I like that the thing I shipped
in March still opens in November, on a machine I have never seen, without me paying for uptime.

## What it costs

I am not going to pretend the trade-offs are small.

- **Distribution is a tax.** Installers per platform, code signing, a download host, and a support conversation
  every time an antivirus vendor changes its mind.
- **Updates are a negotiation.** With a web app, everyone is on the new version. With a desktop app, someone is
  always on the version from eighteen months ago, and their bug report is about code you no longer remember.
- **No telemetry means no data.** I find out about crashes when someone emails me. That is a worse feedback loop
  than any dashboard.
- **You cannot fix anything at 2 a.m.** No hotfix on the server; a rebuild, a re-upload, and an email asking
  people to reinstall.

Those are real costs, and they are the reason most new scientific software is a web app.

## Where I draw the line

I do not think the web is wrong. I think the browser is a distribution channel, not a model for computation.
When a tool is mostly a form, a dashboard or a shared database, it belongs on the web and it should stay there.
When the core of the tool is a molecule in a viewport and a solver on the CPU, the browser is a wrapper around
a native engine with extra steps.

So: native program, ordinary files on disk, no account, no sync. If that ever stops being the right shape for
the work, I will change my mind. It has happened before.

## The unglamorous advantage

There is one more reason, and it is not technical. A desktop program is finished when the user stops needing
you. There is no engagement metric, no retention curve, no incentive to make the tool stickier than the
problem requires.

I like that constraint. It makes the design question smaller and, for me, easier to answer: does this help
someone get a defensible answer today, and can they walk away afterwards?
