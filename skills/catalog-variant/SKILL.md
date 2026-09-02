---
name: catalog-variant
description: Second phase of gaspol-catalog, run once per prospect. Use to turn the master catalog into an offer deck for one named company — buat deck penawaran untuk prospek, bikin proposal per perusahaan, deck penawaran B2B, varian katalog per klien. Qualifies the deal before writing anything, mines the findings from the prospect's own documents so the ISSUES slides are theirs and not a template, picks the reference-disclosure variant by territory, and hands the result to catalog-gate.
---

# catalog-variant

> Cheap to run, run often. The slides that matter here are the ones built from the
> prospect's own numbers — everything else is inherited from the master catalog.

**Announce:** "Running catalog-variant — qualifying the deal, then building the deck from this prospect's own findings."

## Input

- `prospects/<slug>/brief.md` and `prospects/<slug>/storyline.md` from
  `catalog-brainstorm` (prospect mode) — **required, see the entry gate below**
- Prospect: legal name, territory, size of operation
- **Prospect documents** — operations recap, rate card, tender document, fleet list,
  anything they produced themselves
- `catalog/` from `catalog-master`
- `../../research/buyer-brain.md`

## Load (the brain)

- `../../references/b2b/b2b-deck-architecture.md` — the six-act spine
  (**COVER → MASALAH → SOLUSI → PRODUK → HARGA → PENUTUP**) and its three optional inserts
- `../../references/b2b/b2b-honesty-rails.md` — rails, anchors, urgency validity
- `../../references/b2b/b2b-phased-sale.md` — the phased structure this deck sells

## Reuse (installed skills — call, do not reimplement)

| Skill | For |
|---|---|
| `meddic-scorecard` | qualifying the deal **before** any slide is written |
| `spin-selling` | the discovery questions that surface the real problem |
| `challenger-sale` | reframing what the prospect believes, and taking control |
| `made-to-stick` | making the findings memorable enough to be repeated upstairs |
| `storybrand` | keeping the prospect the hero and the product the guide |

If a required skill is missing, STOP. Run `bash tests/deps-present.sh`.

## ENTRY GATE — no brief, no draft

If `prospects/<slug>/brief.md` or `storyline.md` is absent, **STOP and run
`catalog-brainstorm` in prospect mode first.** Prospect mode is short by design — it
inherits every product answer and asks only what changes per company — so this costs
minutes, and skipping it produces a deck aimed at the segment rather than at the
company.

## Procedure

### 1. Qualify first — the cheap gate

Run `meddic-scorecard` **before writing anything**. Metrics, economic buyer, decision
criteria, decision process, identified pain, champion.

If the deal does not qualify, **report why and do not build the deck.** Building a
deck for a dead deal is the most common waste in this whole pipeline, and it costs a
day of a marketing team's time to discover what a scorecard shows in ten minutes.

Report the qualification either way — a deck that ships without one hides how thin the
deal was.

### 2. Require the prospect's documents

The ISSUES act is built from **the prospect's own numbers**. If no prospect document
is available, **STOP and ask for one.** Do not fill the act from the master catalog's
generic segment issues — a deck whose findings are not the prospect's has stopped
being an offer and become a brochure, and the buyer feels the difference immediately.

What counts: an operations recap, a rate card, a tender document, a fleet list, an
audit report, minutes of a meeting where they described the problem. What does not
count: their website, an industry report, or our own assumptions about their segment.

### 3. Mine the findings

Read the documents and extract findings, one per slide. For each finding:

- quantify it in the unit the prospect already counts in — per vehicle per day, per
  trip, per rit — never in efficiency percentages
- name the document and period it came from
- carry it as a **question**, not an accusation. A finding may have a legitimate
  reason, and calling it waste in front of the person who designed the rule is the
  fastest way to lose the room
- mark it as the prospect's own number, never as our assumption

Where a number must be estimated, state the assumption **before** the number, name its
source, and invite correction. Assumptions engineered backwards from a desired total
read as a vendor matching data rather than reasoning.

### 4. Reframe

Run `challenger-sale`. The finding is not the pitch — the reframe is. What does the
prospect currently believe about this cost that the findings contradict?

### 5. Build the deck

10–20 slides, **in the assertion order fixed in `storyline.md`**, on the six-act
spine. An assertion still marked `GAP` is not drafted — it returns to
`catalog-brainstorm` for an answer. Cover carries duration and deadline, never price.
The impact slide carries no currency and no percentage. The closing echoes the cover
with only its last clause changed, and carries one instruction.

Everything not prospect-specific — mechanism, phased structure, proof layers, terms —
is inherited from `catalog/`, not rewritten.

### 6. Pick the reference-disclosure variant

Reference customers are disclosed by **territory**, and the rule is generic here
because the mapping is a runtime input that is never committed:

- If the prospect **competes with a reference customer in the same market**, that
  reference is written **anonymous and descriptive** — the kind of operation, the
  scale band, when it went live — with no name and no logo.
- If the prospect is **not** a competitor of that reference, the reference may be
  named, **provided a written permission exists**.
- With no written permission, anonymous applies everywhere.

Whichever variant is used, the reference's operational identity stays out: fleet
counts, vehicle numbers, driver names, delivery records, live positions, and that
customer's own customers.

### 7. Hand to `catalog-gate`

**Do not deliver anything to the user or the prospect before a PASS verdict.** On
BLOCKING, apply the fix list and re-submit.

## Output

```
prospects/<slug>/
  brief.md              from catalog-brainstorm (prospect mode)
  storyline.md          from catalog-brainstorm (prospect mode)
  qualification.md      MEDDIC scorecard + go / no-go with reason
  findings.md           each finding, its source document, its unit
  deck.md               10–20 slides, six-act spine
  review.md             from catalog-gate
```

## Hard rules

0. `catalog-brainstorm` prospect mode runs before this skill. No `brief.md` +
   `storyline.md`, no deck.
1. Qualification runs before the first slide, and its result is reported either way.
2. No prospect document, no deck. Stop and ask.
3. Findings are the prospect's numbers, sourced and carried as questions.
4. `catalog-gate` is never skipped.
5. Never state a prospect's operating figure that was not in a document they produced.
   Estimating one and rendering it as fact is the single fastest way to lose a deal in
   the room, because they know their own numbers and we do not.
