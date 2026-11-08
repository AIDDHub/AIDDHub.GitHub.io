---
title: "Matched molecular pairs and R-group tables: from spreadsheet to SAR"
short_title: "MMP and R-group tables"
description: "Turn a structure-activity spreadsheet into matched molecular pair statistics with p-values and an R-group matrix you can defend in a review."
date: 2026-11-05
section: tutorials
product: molinsight
tags: [mmp, r-group, sar, cheminformatics]
---

The sentence that most often derails an SAR review is "this substituent looks better". Twenty minutes of
arrow-pushing later, nobody can say whether the effect is real, how many compounds support it, or whether it
reverses on a different scaffold.

Matched molecular pairs (MMP) answer that question with arithmetic instead of intuition. This walkthrough takes
a normal assay table and produces three things you can put in a report: pair statistics with a significance
estimate, an R-group matrix, and one sentence that survives the follow-up question.

## Start from a clean table

You need one structure column and at least one numeric activity column. Before running anything:

- convert IC50 to pIC50, so that "higher is better" holds everywhere;
- drop censored values (`> 10 µM`) or keep them in a separate column — a censored number is not a measurement;
- check that stereochemistry is defined; a racemate and a pure enantiomer are different compounds.

On import, MolInsight calculates 35 molecular descriptors (MW, LogP, TPSA, HBA/HBD and the rest) and shows them
next to your columns. Those descriptors are what you will compare against potency in the next step.

**Choose the activity column before you run MMP.** Every difference in the output is computed on that column,
and re-running against a different column produces a completely different table.

## Look at the whole set first

A scatter plot of LogP against pIC50 takes ten seconds and tells you whether the series has an obvious trend
before you attribute anything to a substituent. If a series has no signal at all, MMP will happily produce a
long list of transformations with p-values near 1 — evidence of nothing.

Useful first plots:

- pIC50 against LogP and against MW, to see how much of the series is driven by size and lipophilicity;
- a small-multiples view by scaffold, to check whether the series is really one series;
- a histogram of the activity column, to see whether the range is wide enough to talk about potency at all.

## Run the MMP analysis

`Analyze → MMP`.

| Setting | Value | Why |
|---|---|---|
| Max cuts | 2 | one cut finds terminal substitutions, two adds linker replacements |
| Max cut bonds | 5 | larger fragments stop being interpretable |
| Property | pIC50 | the column you are explaining |
| Scope | all | run on everything, then filter by scaffold in the table |

The output is one row per transformation, written as `[R1]>>[R2]`, with:

| Column | What it tells you |
|---|---|
| Pairs | how many compounds support this transformation |
| Mean Δ | average change in the property across all pairs |
| Std. dev. | how consistent that change is |
| Min / Max Δ | the worst case, which is often the interesting one |
| Significance p | probability of seeing this Δ by chance given the pair count |

## How to read the p-values

This is the part that separates a defensible table from a pretty one.

- **Pairs = 3 with p = 0.003 is not a discovery.** With three pairs you are one outlier away from the opposite
  conclusion. Sort by pair count first, then by effect size, then look at p.
- **A sign flip across scaffolds is a result, not a bug.** The same CH3 → CF3 change that gains 0.8 log units on
  one core and loses 0.4 on another is telling you the effect is context-dependent. That is worth a sentence in
  the report; a single averaged number hides it.
- **p is a filter, not a finding.** It tells you which rows are worth a chemist's attention. The explanation
  still comes from the structures and the interactions.

> A practical rule: require at least 5 pairs and |mean Δ| ≥ 0.3 log units before a transformation goes into a
> slide. Everything else goes in the appendix.

## Build the R-group matrix

`Analyze → R-group / Scaffold-side-chain`, then pick the core.

The matrix shows the common core on the left, one column per substitution position, and each cell coloured by
the mean property change of the compounds carrying that R group. Sparse cells are greyed out rather than
silently averaged.

What it is good for:

- seeing at a glance which position matters — a column with a strong colour gradient is an optimisation point,
  a column of pale cells is not;
- spotting the combination that nobody made yet: a good R1 with a good R2 usually appears as a missing cell in
  the corner;
- checking whether an apparent trend is one compound or a whole row.

What it is not good for: imputing activity for combinations that do not exist in the data. An empty cell means
"not measured", not "predicted".

## Write the conclusion

One sentence, with the numbers in it:

> On scaffold X, a fluoro at R1 raises the mean pIC50 by 0.8 (n = 6, p < 0.01), while R2 polar substituents show
> no consistent effect (p = 0.42); the next step is to extend R1 and keep R2 small to preserve solubility.

That sentence contains the effect size, the sample size, the significance, and the caveat. It is also the only
part of the analysis most readers will remember.

## Common mistakes

- **Too many cuts.** Three or more cuts fragment the molecules into pieces that no chemist would call a
  substitution, and the table fills with noise.
- **Mixing assays.** Two IC50 protocols, or one Ki column and one IC50 column, produce differences that have
  nothing to do with the substituent.
- **Ignoring the pair count.** A large table sorted by mean Δ puts the least supported transformations at the
  top, because small samples produce large averages.
- **Reporting the average only.** The min/max columns are where the mechanism usually hides.
