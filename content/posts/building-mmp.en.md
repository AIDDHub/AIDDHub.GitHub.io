---
title: "Building matched molecular pairs: the boring parts"
short_title: "The boring parts of MMP"
description: "The fragmentation algorithm takes an afternoon. Canonicalising cut points, symmetric fragments, small-sample statistics and a table with 40,000 rows take the rest of the month."
date: 2026-10-26
section: notes
product: molinsight
tags: [mmp, implementation, statistics, build-log]
---

Matched molecular pairs look like a small feature. Cut a molecule at a bond, do it for every molecule, group
the results by the fragment that was removed, subtract the activities. An afternoon of work.

The cutting is, in fact, an afternoon. Everything else is the feature.

## Cutting is the easy half

The textbook algorithm: for each molecule, break up to *n* acyclic single bonds, then canonicalise the two
pieces so that identical contexts hash to the same key. With a cheminformatics toolkit this is a loop and a
`MolToSmiles`.

It stops being easy at the details:

- **Symmetry.** Toluene cut at the methyl bond and cut at a ring bond can produce the same pair of fragments in
  two different orders. Without canonical ordering, every symmetric molecule doubles its pair count and
  inflates the statistics.
- **Stereo and charge.** If the cut severs a stereo bond or leaves an unpaired charge, the fragment is not a
  valid structure and the pair is not a pair. Keeping it produces transformations nobody can draw.
- **Salts and mixtures.** A hydrochloride salt imports as two components. Fragment the salt and the table fills
  with pairs between the counterion and everything else. Strip first, loudly.
- **Ring bonds.** Excluded by definition, but a surprising number of naive "one cut" transformations turn out
  to be ring openings that happen to parse.

None of this is intellectually hard. All of it separates a demo from a table a chemist will believe.

## The statistics are where the arguments start

The output everybody wants is one number per transformation: how much does this change the activity. That
number is a mean, and a mean over three pairs is not evidence.

So the table needs the pair count, the spread, the extremes, and something significance-flavoured. Which
immediately raises a question that is not enjoyable to answer: *which test?*

- A paired t-test is the obvious choice and the wrong one when the differences are heavy-tailed, which they
  are whenever one compound in the series is an outlier.
- Wilcoxon signed-rank is more robust and refuses to say anything useful at n = 4.
- Multiple testing across thousands of transformations turns any fixed threshold into a lie.

The compromise that ships: report the pair count and the spread, give a p-value from a test that does not
assume normality, and — the important part — put the pair count in the same row, so nobody can sort by p
without seeing how thin the evidence is.

> If a statistic cannot be explained in one sentence to the person reading the table, it should not be a
> column.

## The interface is the actual product

Forty thousand transformation rows is not a table, it is a denial of service. The first version rendered all
of them, and switching tabs took nine seconds.

The version that ships does three things:

1. **Aggregates before it renders.** One row per transformation, never one row per pair.
2. **Treats filtering as a first-class control.** Pair count, effect size, and the scaffold currently under
   discussion — because the interesting question is almost never "across everything".
3. **Keeps the pairs reachable.** Click a transformation, see the compounds that support it, with structures.
   Without that, the table is a claim; with it, the table is evidence.

The third point took the longest, and it is the only one that changed how the feature gets used.

## What we would do differently

Build the pair browser before the statistics. The moment a transformation can be clicked into its actual
molecules, the right numbers to show become obvious — and several carefully computed columns turn out to be
decoration.

Also: stop treating "number of cuts" as a power-user setting. Everyone turns it up, everyone gets
uninterpretable fragments, and everyone blames the algorithm. Two cuts is a good default, and the interface
now says so.

## The lesson, such as it is

The interesting engineering in a scientific tool is rarely the science. It is the canonicalisation, the
threshold that is not hidden, and the four seconds saved every time someone opens a table. None of that makes
a good screenshot, and all of it decides whether the tool gets used twice.
