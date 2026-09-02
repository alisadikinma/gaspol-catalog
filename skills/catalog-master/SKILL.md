---
name: catalog-master
description: First phase of gaspol-catalog, run once per product. Use to build the master sales catalog and enablement kit a marketing team reuses across every prospect — buat katalog produk, katalog penjualan, bikin kit marketing, menu modul dan harga, one-pager, skrip penjualan. Produces the capability catalog, the à-la-carte module menu with prices, the five-part enablement kit, a one-pager, contact scripts, and the ROI calculator spec. Stops and asks rather than inventing prices, a product maturity claim, or what may be said publicly about a reference customer.
---

# catalog-master

> Run once per product, not once per prospect. Everything `catalog-variant` produces
> later is a specialization of what this phase decides.

**Announce:** "Running catalog-master — building the master catalog and enablement kit."

## Input

- `catalog/brief.md` and `catalog/storyline.md` from `catalog-brainstorm`
  (product mode) — **required, see the entry gate below**
- Product capability inventory (what the system actually does today)
- The reference customer's public content contract
- `../../research/buyer-brain.md`
- Module list and prices — **from a human, see the stop gates below**

## ENTRY GATE — no brief, no draft

If `catalog/brief.md` or `catalog/storyline.md` is absent, **STOP and run
`catalog-brainstorm` in product mode first.** Do not reconstruct the interview from
the capability inventory: an inventory says what the system does, and a catalog has
to say what the buyer loses by not having it. Only the interview carries that.

If the brief exists but its GAP list still contains any of the three stop gates below,
that is the same stop — resolve it as an interview answer, not as a draft assumption.

## Load (the brain)

- `../../references/b2b/b2b-deck-architecture.md` — the six-act spine
  (**COVER → MASALAH → SOLUSI → PRODUK → HARGA → PENUTUP**) and its three optional inserts
- `../../references/b2b/b2b-honesty-rails.md` — rails, anchors, urgency kit, modular
  menu rules
- `../../references/b2b/b2b-phased-sale.md` — the two deployment models; the one this
  seller chose is recorded in `brand.md`, not assumed here
- `../../references/b2b/enablement-kit.md` — the five-part output shape
- `../../research/buyer-brain.md` — decision triggers, objections, buyer vocabulary,
  trusted evidence, procurement patterns, anti-patterns

## Reuse (installed skills — call, do not reimplement)

| Skill | For |
|---|---|
| `positioning` | competitive alternatives, unique attributes, market category |
| `pricing-strategy` | willingness to pay, tier configuration, monetization model |
| `monetizing-innovation` | second opinion on packaging and price integrity |
| `sales-narrative` | the eight-step narrative arc the catalog follows |
| `crossing-the-chasm` | beachhead segment and whole-product definition |
| `100m-offers` | offer construction, guarantee shape, value stacking |

If a required skill above is missing, STOP and tell the user. Run
`bash tests/deps-present.sh` to see which. Do not stub it and do not fabricate its
output.

## THREE STOP GATES (Iron Law — never invent these)

Before writing a single slide, resolve all three. Each is a **stop and ask**, not a
note to the reader.

### Gate 1 — module list and prices
A catalog without prices is not a catalog. Ask for: every module offered, its price,
the anchor price it is discounted from if any, and the real reason for the discount.

Do NOT derive a price from cost, from a competitor, or from a plausible-sounding
round number. A price the vendor cannot defend in the room is worse than no price on
the page.

### Gate 2 — deployment model
Ask directly: does the product serve multiple customers from one deployment, or does
each customer mean a separate deployment?

The answer changes the timeline, the price, and the support story. If multi-tenancy is
not real yet, it is **not claimed** — and the per-customer deployment reality is
written into the timeline honestly, because a buyer discovers it in week two anyway.

### Gate 3 — reference-customer disclosure
Read the reference customer's content contract before naming them anywhere. Ask what
may be said, in writing.

Typical prohibitions: fleet counts, vehicle numbers, driver names, delivery records,
live positions, that customer's own customers, and service lines outside the approved
public scope. Without a written permission, the reference is written **anonymous and
descriptive**, never named.

Also ask whether the prospect competes with the reference customer in the same market.
If so, the reference stays anonymous for that prospect regardless of permission.

## Procedure

1. **Position the product** — call `positioning` and `crossing-the-chasm`. Name the
   beachhead segment and the competitive alternatives buyers actually consider, which
   are usually "how we do it now", not a named competitor.
2. **Separate maturity into layers** — what runs in production today, what has been
   assembled once, what has never been built. This split drives every later claim and
   is non-negotiable per `b2b-honesty-rails.md` rail 12. **The split is
   non-negotiable; its presentation is not.** Rail 12 used to mandate a dedicated
   confession slide and a real deck shipped with one, headlined on our own weakness,
   until the seller deleted it. Default to a small maturity marker attached to the
   module on the solution slide; `brand.md` records if the seller wants another form.
3. **Build the offer** — call `100m-offers` and `pricing-strategy`. Configure the
   à-la-carte menu. It **must** contain one line that cannot be removed; without it
   buyers assemble a package that cannot function and then blame the system.
4. **Write the master catalog**, 12–16 slides, **following the assertion order in
   `storyline.md`** rather than inventing a new one — that order was fixed against
   the interview and reordering it here silently discards what the interview
   established. Any assertion still marked `GAP` is not drafted; it goes back to
   `catalog-brainstorm` for an answer. The spine is the six-act one. The
   ISSUES act here is generic-by-segment rather than prospect-specific, because this
   artifact goes out before any prospect's documents exist. Cover carries duration and
   deadline, never price.
5. **Write the five-part enablement kit** per `enablement-kit.md`. Objection handling
   comes from `## Keberatan` in the buyer research, quoted rather than paraphrased.
6. **Write the one-pager** — one page, left behind after a meeting or sent by message.
7. **Write the contact scripts** — opener, discovery questions, objection responses,
   closing ask. Buyer vocabulary from `## Bahasa pembeli`; the banned-vendor-phrase
   list travels with it.
8. **Write the ROI calculator spec** — inputs (fleet size, routes, fuel price),
   outputs (today versus after). **Specification only.** Building it is out of scope
   for this plugin, and the spec must state that the numbers entered belong to the
   prospect and are never pre-filled with invented defaults.
9. **Hand to `catalog-gate`.** Nothing leaves this skill unreviewed.

## Output

```
catalog/
  context-brief.md
  master-catalog.md          12–20 slides, six-act spine
  module-menu.md             à-la-carte + prices + the unremovable line
  talk-tracks.md
  one-pager.md
  system-instructions.md
  feedback-log.md            starts empty, by design
  roi-calculator-spec.md
```

## Hard rules

0. `catalog-brainstorm` runs before this skill. No `brief.md` + `storyline.md`, no
   draft — and the storyline's order is followed, not improvised.
1. `catalog-gate` is never skipped. A PASS verdict is what releases this to a
   marketing team.
2. Cover carries no price.
3. Every urgency device must genuinely apply, and the countdown is tied to the send
   date — a different send date means the CTA slide is regenerated.
4. Hardware brands and model numbers never appear in client-facing material. The
   sensor choice and its calibration are the advantage a catalog integrator could copy
   in a day; naming the model turns intellectual property into a shopping list.
5. Nothing in `references/` is edited to fit a product. Product facts are runtime
   input; the references are the generic canon.
