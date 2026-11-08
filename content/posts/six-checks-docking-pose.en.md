---
title: "Six checks before you trust a docking pose"
short_title: "Six checks on a pose"
description: "A docking score is a ranking hint, not a result. Six quick checks that separate a pose worth reporting from an artefact of preparation."
date: 2026-10-28
section: tutorials
product: molstudio
tags: [docking, validation, poses, tutorial]
---

Every docking programme will return a pose, and every pose comes with a number. The number is the part people
quote; the pose is the part that has to survive a reviewer. These six checks take about five minutes per
compound and catch most of the failures that make a docking figure impossible to defend.

## 1. Is the ligand inside the box?

Obvious, and still the most common cause of nonsense. If the box was placed by eye, confirm that the ligand
volume sits inside it — a pose that only touches the edge of the search space has not really been optimised.

In MolStudio the box is drawn in the viewer, so this is a two-second visual check before the run rather than a
diagnosis after it.

## 2. Did the protocol reproduce the reference ligand?

If the structure contains a co-crystal ligand, redock it first. Remove it, then dock it back with exactly the
protocol you plan to use and check the RMSD to the crystal pose.

- **Under ~2 Å** — the protocol can find the right answer on this receptor. Continue.
- **Over ~2 Å** — treat every result with suspicion. Something in the preparation (protonation, missing
  residues, metal ions, waters) or in the box is wrong.

This is the single most valuable control in a docking study, and it costs one run.

## 3. Are the hydrogen bonds geometrically plausible?

Distance alone is not enough. A hydrogen bond at 3.9 Å is not a hydrogen bond; a donor pointing away from the
acceptor is not one either. In the 2D interaction view, look at the listed distances and then confirm the
geometry in 3D:

| Interaction | Typical distance | What to check |
|---|---|---|
| Strong H-bond | 2.6–3.2 Å | donor–acceptor alignment |
| Weak / long H-bond | 3.2–3.5 Å | does it still point at the acceptor? |
| Salt bridge | 2.5–4.0 Å | charge state of both partners |
| π–π stacking | 3.5–4.5 Å | ring centroid distance and offset |

A pose whose only interactions are 3.8 Å "hydrogen bonds" is held together by the scoring function, not by
chemistry.

## 4. Is there any steric clash?

Look for ligand atoms that sit inside the van der Waals radius of a protein atom, and for the ligand passing
through a loop. Small overlaps are absorbed by the soft scoring potential; a real clash means the pose is
impossible regardless of its score.

## 5. Does the pose explain what you already know?

If the series has SAR, the pose should be consistent with it. A compound known to be inactive through this
target should not fill the pocket perfectly. A compound that loses 100-fold when a substituent is removed
should have that substituent making a contact.

Docking is at its most useful when it explains an existing measurement, not when it invents a new lead from
nothing.

## 6. Does the ranking survive a second run?

Re-run the top compound with a different seed and higher exhaustiveness.

- Same pose, similar score — the result is stable.
- Different pose, similar score — the scoring function cannot distinguish them, and you should report the
  ambiguity rather than pick the prettier picture.
- Same pose, very different score — the search had not converged; the first number was noise.

## What the score is, and is not

The Vina affinity is a fast empirical scoring function. It is useful for ordering compounds docked into the
same receptor with the same preparation. It is not a binding free energy, it does not include entropy, and it
has a well-known bias toward larger, more lipophilic ligands.

Practical consequences:

- compare within a series, never across two different receptors;
- normalise by heavy-atom count when a series spans a wide size range;
- treat differences under ~0.5 kcal/mol as noise;
- report the interactions, and let the score be the ranking, not the conclusion.

## A short checklist

- [ ] Ligand fully inside the box
- [ ] Reference ligand reproduces its crystal pose
- [ ] Hydrogen bonds plausible in distance *and* angle
- [ ] No steric clash
- [ ] Pose consistent with the SAR you already have
- [ ] Ranking stable across seeds

If all six pass, the pose is worth a figure. If four pass and two are ambiguous, say so — a well-described
limitation is more convincing than an overconfident picture.

The docking workflow used here, including the interaction diagram and the session export, is part of MolStudio;
the free tier has no time limit.
