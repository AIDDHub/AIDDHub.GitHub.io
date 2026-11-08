---
title: "Implementing matched molecular pairs: the boring parts"
short_title: "The boring parts of MMP"
description: "The fragmentation algorithm took an afternoon. Canonicalising cut points, symmetric fragments, small-sample statistics and a table with 40,000 rows took the rest of the month."
date: 2026-10-26
section: notes
product: molinsight
tags: [mmp, implementation, statistics, build-log]
featured: true
---

Matched molecular pairs sound like a small feature. Cut a molecule at a bond, do it for every molecule, group
the results by the fragment you cut off, subtract the activities. An afternoon of work, I thought.

The cutting is, in fact, an afternoon. Everything else is the feature.

## Cutting is the easy half

The textbook algorithm: for each molecule, break up to *n* acyclic single bonds, then canonicalise the two
pieces so that identical contexts hash to the same key. With a cheminformatics toolkit this is a loop and a
`MolToSmiles`.

It stops being easy at the details:

- **Symmetry.** Toluene cut at the methyl bond and cut at a ring bond can produce the same pair of fragments in
  two different orders. Without canonical ordering, every symmetric molecule doubles its pair count and
  quietly inflates the statistics.
- **Stereo and charge.** If the cut severs a stereo bond or leaves an unpaired charge, the fragment is not a
  valid structure and the pair is not a pair. Silently keeping it produces transformations nobody can draw.
- **Salts and mixtures.** A hydrochloride salt imports as two components. Fragment the salt and you get pairs
  between the counterion and everything else. Strip first, loudly.
- **Ring bonds.** Excluded by definition, but a surprising number of "one cut" transformations in a naive
  implementation are ring openings that happen to parse.

None of this is intellectually hard. All of it is the difference between a demo and a table a chemist will
believe.

## The statistics are where the arguments start

The output everybody wants is one number per transformation: how much does this change the activity. That
number is a mean, and a mean over three pairs is not evidence.

So the table needs the pair count, the spread, the extremes and something significance-flavoured. Which
immediately raises a question I did not enjoy answering: *which test?*

- A paired t-test is the obvious choice and the wrong one when the differences are heavy-tailed, which they
  are whenever one compound in the series is an outlier.
- Wilcoxon signed-rank is more robust and refuses to say anything useful at n = 4.
- Multiple testing across thousands of transformations turns any fixed threshold into a lie.

What is in the product now is a pragmatic compromise: report the pair count and the spread, give a p-value
from a test that does not assume normality, and — this is the important part — put the pair count in the same
row, so that nobody can sort by p without seeing how thin the evidence is.

> If a statistic cannot be explained in one sentence to the person reading the table, it should not be a
> column.

## The interface is the actual product

Forty thousand transformation rows is not a table, it is a denial of service. The first version rendered all
of them, and the app took nine seconds to switch tabs.

The version that ships does three things:

1. **Aggregates before it renders.** One row per transformation, never one row per pair.
2. **Filters as a first-class control.** Pair count, effect size, and the scaffold you are currently thinking
   about — because the interesting question is almost never "across everything".
3. **Keeps the pairs reachable.** Click a transformation, see the compounds that support it, with structures.
   Without that, the table is a claim; with it, the table is evidence.

That third point took the longest, and it is the only one that changed how people use the feature.

## What I would do differently

I would build the pair browser first, before the statistics. The moment I could click a transformation and see
the actual molecules, the right numbers to show became obvious — and several of the columns I had carefully
computed turned out to be decoration.

I would also stop treating "number of cuts" as a power user setting. Everyone turns it up, everyone gets
uninterpretable fragments, and everyone blames the algorithm. Two cuts is a good default and the UI now says
so.

## The lesson, such as it is

The interesting engineering in a scientific tool is rarely the science. It is the canonicalisation, the
threshold you refuse to hide, and the four seconds you save every time somebody opens a table. None of that
makes a good screenshot, and all of it decides whether the tool gets used twice.
