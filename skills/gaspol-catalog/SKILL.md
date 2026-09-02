---
name: gaspol-catalog
description: Orchestrate B2B sales catalog and offer-deck creation end to end for operations buyers rather than investors. Use when the user wants to build, write, improve, or review a sales catalog, offer deck, proposal, or marketing kit for selling a system to companies — buat katalog penjualan, bikin deck penawaran, proposal ke perusahaan, kit marketing B2B, review penawaran sebelum dikirim. Routes through master catalog once, per-prospect variant many times, and a two-layer blocking gate that reviews the text and the rendered images. Enforces a blocking review before anything reaches a prospect.
---

# gaspol-catalog (orchestrator)

> Build an offer a company actually signs, as a repeatable pipeline — and never send
> one that has not survived both review layers.

**Announce at start:**
> "I'm using gaspol-catalog. It interviews first, fixes the storyline, then runs master catalog once, per-prospect variant per company, and a two-layer gate — text and render — that both block. Nothing reaches a prospect without a PASS."

## The audience, stated once

The buyer is the **owner or management of an operating company**. They buy a change in
working days, not a share of a market. If the reader is an investor, this is the wrong
plugin — use `gaspol-pitch`, which shares this one's review engine and nothing else.

## Routing

The pipeline is **interview → storyline → deck → gate → visual → gate → finish**, in
that order. It is a loop, not a line: `catalog-finish` writes what was learned back
into the same knowledge base `catalog-brainstorm` reads from, so each deal starts
further along than the last.

| Situation | Skill |
|---|---|
| Anything at all is starting — no brief exists yet | `catalog-brainstorm` (product mode) |
| A named prospect appeared and `catalog/brief.md` exists | `catalog-brainstorm` (prospect mode) |
| `brief.md` + `storyline.md` exist, no master catalog yet | `catalog-master` |
| A prospect's `brief.md` + `storyline.md` exist | `catalog-variant` |
| A deck exists and is about to be sent, shown, or handed over | `catalog-gate` |
| `catalog-gate` layer one returned PASS **and `brand.md` is complete** | `catalog-visual` |
| Layer one PASSED but `brand.md` is missing or still has placeholders | back to `catalog-brainstorm` for the brand intake — do not render |
| Images exist and need checking | `catalog-gate` again, for layer two |
| Both layers PASSED and it is time to send | `catalog-finish` |
| Prices or product facts changed | `catalog-brainstorm` product mode again, then `catalog-master`, then re-gate every variant that quoted them |

`catalog-brainstorm` runs **before every deck**, in one of two modes.
`catalog-master` runs **once per product**. `catalog-variant` runs **once per
prospect** and is cheap on purpose. `catalog-visual` runs **only after layer one
passes**. `catalog-gate` runs **every time**, and it runs twice on any deck that gets
rendered — once for the text, once for the images. `catalog-finish` runs **last**, and
is the only skill that writes anything back.

`catalog-brainstorm` reads the user's own knowledge base first — if one exists on the
machine — and interviews only what it could not answer. `catalog-finish` closes the
loop at the other end, writing back the corrections, the objection the buyer actually
voiced, and what shipped. The plugin ships the instruction to look, never an address:
no path, vault name, or company name is committed. With no knowledge base found it
asks everything, which is the correct first-time run, not a degraded one.

## Nothing is drafted before someone is asked

`catalog-master` and `catalog-variant` **refuse to start** without `brief.md` and
`storyline.md` from `catalog-brainstorm`. This is not ceremony: a catalog written
before the interview invents the buyer's problem, and an invented problem survives
every later review because nothing downstream has the facts to contradict it. The
gate catches a wrong number; it cannot catch a right number answering a question
nobody has.

## Nothing is rendered before the brand is asked for

`catalog-visual` **refuses to start** without a complete `brand.md` from
`catalog-brainstorm` — the seller's house standard, palette, fonts, asset paths, and
four decisions that belong to the seller rather than to this plugin.

This is the newest of the plugin's refusals and it was bought expensively. A 19-slide
deck was interviewed, drafted, reviewed, and rendered with every visual value still an
unfilled placeholder. The image model supplied its own defaults for all of them, and
the seller rejected the finished deck on sight as generic AI output — with not one
slide wrong on the facts. An unfilled placeholder is not a neutral default; it hands
the design decision to an image model.

The same intake settles four things the plugin used to decide alone and had rejected
each time: human faces, naming the incumbent vendor, the shape of the maturity
admission, and pilot-versus-simultaneous rollout.

## The gate is never skipped

`catalog-gate` has two layers and both block:

- **Layer one, text** — reuses the `pitch-review` engine from `gaspol-pitch` with the
  buyer rubric supplied through its `rubric` parameter.
- **Layer two, render** — a separate phase that checks produced images against the
  deck text. A deck has passed layer one and blocked on layer two the same day; the
  defect was in the render prompt, not in the deck. The prompts it judges are written
  by `catalog-visual`, which carries the guards that stop the known defects before
  they are rendered.

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
deployment; what may be said publicly about a reference customer. All three are
**asked in `catalog-brainstorm`**, in writing, and each remains a stop gate in
`catalog-master`. Asking early costs one interview question; being ambushed by the
same gate mid-draft costs the draft. Fabricating any of the three breaks the honesty
rails the whole rubric rests on.

## Tests

`bash tests/run-all.sh` runs every scripted gate. The fixture verdict itself — the bad
example must BLOCK, the good one must PASS — is run by an agent against
`references/b2b/examples/`, and the contract lives in `catalog-gate`'s self-test
section.
