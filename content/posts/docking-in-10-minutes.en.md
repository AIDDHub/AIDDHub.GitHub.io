---
title: "Run a docking job on Windows in 10 minutes — without Python"
short_title: "Docking without Python"
description: "Prepare a receptor, dock a ligand library with AutoDock Vina and export a 2D interaction diagram in MolStudio. No conda, no MGLTools, no command line."
date: 2026-11-08
section: tutorials
product: molstudio
tags: [docking, autodock-vina, windows, tutorial]
featured: true
---

You have a protein structure and a handful of compounds, and you need a binding hypothesis by tomorrow.
The usual route — install conda, install MGLTools, convert the receptor, remember the `vina` flags you used
last year — eats the whole afternoon before the first pose exists.

This walkthrough does the same job inside MolStudio: import, prepare, dock, read the interactions, export a
figure. Everything runs locally on Windows; the Linux build is the same program, so the steps are identical.

## What you need

- MolStudio v1.0 — every step below is in the free tier
- A receptor structure, for example `3FUP.pdb` from the PDB
- Ligands as SDF, SMILES or CSV (a few dozen is plenty for a first run)

## 1. Import the receptor

`File → Import → PDB` and pick the file. MolStudio reads the structure as chains, residues, hetero groups and
waters, and shows them separately in 3D, so you can see exactly what you are about to keep or discard before
touching any preparation setting.

Two things are worth checking immediately:

- the co-crystallised ligand is present (you will use it later to place the docking box);
- there are no duplicate chains from a biological assembly you did not intend to model.

## 2. Prepare the receptor

`Applications → Preparation → Receptor Prep`.

The defaults do what most docking campaigns need: crystallographic waters removed, hydrogens added at
pH 7.4, charges assigned. **This is the step where beginners usually lose an afternoon** — not because it is
hard, but because a half-prepared receptor produces poses that look plausible and score badly, and nothing in
the output tells you why.

Do not remove the co-crystal ligand yet. You need it in the next step.

## 3. Bring in the ligands

`File → Import → SDF` (or SMILES/CSV). A batch import goes straight into the Molecule Table, where each row
shows molecular weight, LogP and the other calculated descriptors. Fix names here rather than later: the
record title becomes the ligand name in every downstream table and in the exported SDF.

## 4. Put the box in the right place

`Applications → Docking` opens the docking panel and the box controls.

- **Pick from 3D** — click the pocket in the viewer; the box centres on that point.
- **Center on ligands** — centre on the co-crystal ligand instead. This is the more reproducible choice when
  you know where the reference compound binds.

A 22–24 Å box is a sensible default. Bigger is not better: a box that covers half the protein dilutes the
search and slows it down for no gain.

| Parameter | Start with | Change it when |
|---|---|---|
| Exhaustiveness | 8 | 16–32 for a final pose, 4 for a quick look at 200 compounds |
| Number of poses | 9 | keep the top 3 for visual inspection, the rest is noise |
| CPU cores | 4 | use all idle cores for a long run |
| Seed | fixed | you need the same output twice |

## 5. Run Vina

Press run. The job reports progress and the rest of the workspace stays usable — you can sort the table or
prepare the next receptor while it works. Ten ligands at exhaustiveness 8 finish in a couple of minutes on a
normal laptop.

## 6. Read the results table

The result table has one row per pose: ligand, mode number and Vina affinity. Sorting by affinity is where
people stop, and it is the least interesting part of the output.

> The score is a fast scoring function, not a binding free energy. It is useful for ranking compounds against
> **the same receptor with the same protonation state**. Comparing scores across two different structures, or
> two preparation protocols, is not meaningful.

## 7. Look at the pose, not the number

Select the best pose and open the Interactions panel, then switch to the 2D view. MolStudio draws hydrogen
bonds with distances, hydrophobic contacts, π–π stacking and salt bridges.

Ask three questions:

1. Does the ligand occupy the same subpocket as the reference compound?
2. Are the hydrogen bonds pointing the right way, or are they 4 Å long and diagonal?
3. Is the scaffold doing the work, or is it the substituent you are about to optimise?

A pose that scores −9.0 but buries nothing is less useful than a −7.5 pose that explains the SAR you already
have.

## 8. Export what you need

- the 2D interaction diagram as PNG or SVG, ready for a slide or a report figure;
- the docked poses as SDF if you want to overlay them later;
- the whole workspace as a session, so you can reopen it next week without repeating the preparation.

## Common mistakes

| Symptom | Likely cause | Fix |
|---|---|---|
| Every ligand scores almost identically | box in a shallow, solvent-exposed surface | reposition the box, check the reference ligand |
| Poses point into the protein | receptor not minimised, hydrogens missing | redo Receptor Prep, check histidine states |
| Reproducible run gives different poses | seed not fixed | set the seed before comparing compounds |
| The best-scoring compound is the one you already know is inactive | scoring function bias toward size | normalise by heavy atoms, and read the interactions |

## Where to go next

Docking answers "can it sit here". The next question is usually "what does the series tell me" — that is
matched molecular pairs and R-group matrices, covered in the next tutorial.
