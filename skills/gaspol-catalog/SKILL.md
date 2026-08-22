---
name: gaspol-catalog
description: Orchestrate B2B sales catalog and offer-deck creation end to end for operations buyers rather than investors. Use when the user wants to build, write, improve, or review a sales catalog, offer deck, proposal, or marketing kit for selling a system to companies — buat katalog penjualan, bikin deck penawaran, proposal ke perusahaan, kit marketing B2B, review penawaran sebelum dikirim. Routes through master catalog once, per-prospect variant many times, and a two-layer blocking gate that reviews the text and the rendered images. Enforces a blocking review before anything reaches a prospect.
---

# gaspol-catalog (orchestrator)

> Build an offer a company actually signs, as a repeatable pipeline — and never send
> one that has not survived both review layers.

**Announce at start:**
> "I'm using gaspol-catalog. It runs master catalog once, per-prospect variant per company, and a two-layer gate — text and render — that both block. Nothing reaches a prospect without a PASS."

## The audience, stated once

The buyer is the **owner or management of an operating company**. They buy a change in
working days, not a share of a market. If the reader is an investor, this is the wrong
plugin — use `gaspol-pitch`, which shares this one's review engine and nothing else.

## Routing

| Situation | Skill |
|---|---|
| No master catalog exists yet for this product | `catalog-master` |
| Master catalog exists, a named prospect appeared | `catalog-variant` |
| Anything is about to be sent, shown, or handed over | `catalog-gate` |
| Prices or product facts changed | `catalog-master` again, then re-gate every variant that quoted them |

`catalog-master` runs **once per product**. `catalog-variant` runs **once per
prospect** and is cheap on purpose. `catalog-gate` runs **every time**.

## The gate is never skipped

`catalog-gate` has two layers and both block:

- **Layer one, text** — reuses the `pitch-review` engine from `gaspol-pitch` with the
  buyer rubric supplied through its `rubric` parameter.
- **Layer two, render** — a separate phase that checks produced images against the
  deck text. A deck has passed layer one and blocked on layer two the same day; the
  defect was in the render prompt, not in the deck.

Without images, layer two reports `NOT RUN` — never `PASS`.

There is no "small deck" exemption and no "we're in a hurry" exemption. One catalog
goes to dozens of companies, so one unchecked claim travels dozens of times.

## Dependencies

**Required.** Check with `bash tests/deps-present.sh`; if any is missing, STOP and
tell the user rather than stubbing it.

- `pitch-review` from the sibling plugin `gaspol-pitch` — the review engine
- 12 skills from the founder-playbook set: `mom-test`, `lean-startup`, `storybrand`,
  `made-to-stick`, `influence`, `obviously-awesome`, `100m-offers`,
  `monetizing-innovation`, `traction`, `blue-ocean-strategy`, `spin-selling`,
  `crossing-the-chasm`
- 7 sales and strategy skills: `challenger-sale`, `meddic-scorecard`,
  `sandler-system`, `never-split-difference`, `sales-narrative`, `positioning`,
  `pricing-strategy`

Install the founder-playbook set with `npx skills add getagentseal/founder-playbook -g`
and the sales set from `guia-matthieu/clawfu-skills`, taking every skill **except**
its `spin-selling`, which collides by name with the founder-playbook one already in
place.

**Optional — degrade gracefully, never hard-stop.**

- `gaspol-design` for palette, font, and chart choices. Absent, fall back to
  `references/b2b/b2b-visual-contract.md`, which is self-sufficient.
- An image MCP for rendering. Absent, emit the prompts and report layer two as
  `NOT RUN`. That is a manual-run note, not a failure.

## Three things this plugin stops and asks about

It never invents: module prices; whether the product serves many customers from one
deployment; what may be said publicly about a reference customer. Each is a stop gate
in `catalog-master`, and fabricating any of the three breaks the honesty rails the
whole rubric rests on.

## Tests

`bash tests/run-all.sh` runs every scripted gate. The fixture verdict itself — the bad
example must BLOCK, the good one must PASS — is run by an agent against
`references/b2b/examples/`, and the contract lives in `catalog-gate`'s self-test
section.
