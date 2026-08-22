---
name: catalog-brainstorm
description: First phase of gaspol-catalog, run before any slide exists. Use to dig out what the offer must actually say by interviewing the human first, then turning the answers into a storyline spine — gali kebutuhan dulu, wawancara sebelum bikin katalog, tanya dulu baru buat deck, susun alur cerita penawaran, storyline katalog, brainstorm penawaran B2B. Runs a probing interview contract for the product (once) or for a named prospect (per deal), pressure-tests the pain with mom-test and spin-selling, resolves the three things this plugin must never invent, and emits brief.md plus storyline.md. catalog-master and catalog-variant refuse to start without it.
---

# catalog-brainstorm

> Nobody buys a catalog that was written before anyone was asked anything. This
> phase interviews first, marks what is still missing, and only then fixes the
> storyline the deck will follow. Slides come after, never before.

**Announce:** "Running catalog-brainstorm — interviewing first, then fixing the storyline. No slides yet."

## Two modes — pick one before the first question

| Mode | When | Feeds |
|---|---|---|
| **product** | No `catalog/brief.md` exists yet for this product | `catalog-master` |
| **prospect** | Master catalog exists, a named company appeared | `catalog-variant` |

Product mode runs **once per product** and is the expensive one. Prospect mode runs
**once per deal** and is deliberately short — it inherits every product answer and
asks only what changes per company.

If the mode is ambiguous, ask. Running product mode again per prospect re-opens
settled pricing decisions and wastes the interview budget on questions already
answered.

## Load (the brain)

- `../../research/buyer-brain.md` — `## Pemicu keputusan` sets what to probe for,
  `## Keberatan` sets what to pre-empt, `## Bahasa pembeli` sets the words to ask in,
  `## Bukti yang dipercaya` sets what evidence to hunt, `## Pola pengadaan` sets the
  procurement questions, `## Anti-pola` sets what an answer must not become.
- `../../references/b2b/b2b-deck-architecture.md` — the eight-act spine the storyline
  is laid on.
- `../../references/b2b/b2b-honesty-rails.md` — an interview answer that would breach
  a rail is re-asked here, not laundered into a slide later.
- `../../references/b2b/b2b-phased-sale.md` — Survey → pilot → rollout, which the
  timeline questions assume.

## Reuse (installed skills — call, do not reimplement)

| Skill | For |
|---|---|
| `mom-test` | asking about their working days, not about our idea — past behaviour over hypotheticals |
| `spin-selling` | Situation → Problem → Implication → Need-payoff ordering of the interview itself |
| `never-split-difference` | calibrated "how" and "what" questions when an answer stays vague |
| `lean-startup` | naming the riskiest assumption in the offer and what evidence would settle it |
| `obviously-awesome` | competitive alternatives — usually "how we do it now", not a named vendor |

If a required skill is missing, STOP and tell the user. Run
`bash tests/deps-present.sh`. Do not stub it, and do not invent its output.

## Interview contract — ask the sharp version

Ask in the buyer's own vocabulary. Every answer is either **quantified and sourced**
or marked **MISSING** — a confident-sounding guess recorded here becomes a fabricated
number on a slide three phases later.

Push past the first answer. One re-ask minimum on anything vague; use
`never-split-difference` calibrated questions rather than repeating the question
louder.

### PRODUCT MODE

**Who the offer is for**
- Which operating segment, named — fleet operator, distributor, plantation, not "companies"?
- Who inside it signs, who uses it daily, who can veto it? (These are three people.)
- What do they run today instead, and what specifically stops working?

**The pain, in their unit**
- What does the problem cost per vehicle per day, per trip, per rit, per shift — in
  the unit they already count in, never in efficiency percentages?
- How often does it happen, and how do they find out it happened?
- Who currently gets blamed when it does?

**The mechanism**
- What does the system actually do, mechanically, that removes that cost?
- What runs in production today, what has been assembled once, what has never been
  built? Three separate lists — this split is load-bearing for every later claim.

**Proof**
- Which deployment is running right now, since when, and who can confirm it?
- What may be said publicly about it, in writing?

**Commercials**
- Every module, its price, the anchor it is discounted from, and the real reason for
  the discount.
- Which module cannot be removed without the package failing to function?
- Does one deployment serve several customers, or is each customer a separate
  deployment?

**Terms and procurement**
- Payment terms, contract length, what happens at renewal.
- Does this buyer go through tender, direct appointment, or a trial order first?
- What is explicitly out of scope, stated before anyone asks?

### PROSPECT MODE

Inherits every product answer. Ask only what is specific to this company:

- Legal name, territory, size of operation, and who the economic buyer is.
- Which documents they produced themselves are available? (Operations recap, rate
  card, tender document, fleet list, audit report, meeting minutes.) **Their website
  and an industry report do not count.**
- What did they say the problem was, in their words — and when?
- What are they comparing us against for this decision, including doing nothing?
- Do they compete with any reference customer in the same market?
- What is the real deadline on their side, and what happens if it slips?
- What has a vendor already promised them and failed to deliver?

## The three stop gates — surfaced here, enforced downstream

This plugin never invents: **module prices**, **the deployment model**, and **what
may be said publicly about a reference customer**. Ask all three in this phase, in
writing, and record the answer or record `MISSING`.

`catalog-master` still enforces them as stop gates. Surfacing them here means the
human is asked once, early, in an interview — instead of being ambushed mid-draft
after a day of work has already been spent.

## Pressure-test before writing the storyline

1. **mom-test sweep** — any answer that is a compliment, a hypothetical, or a
   statement about the future is not data. Mark it and re-ask about what already
   happened.
2. **Anti-pattern sweep** — check every answer against `## Anti-pola` in
   `research/buyer-brain.md`. An answer that arrives as vendor language gets
   translated into buyer language now, not at draft time.
3. **Riskiest assumption** — call `lean-startup`. Name the one assumption that, if
   wrong, makes the whole offer wrong, and name the evidence that would settle it.

## GAP list

List only what this offer is **missing to be sendable at this stage** — each gap plus
how to close it or how to frame it honestly without it. An honest "we do not have
this yet" is a valid answer and belongs on the list; it is what stops the deck from
manufacturing a substitute.

A gap on any of the three stop gates is **blocking for `catalog-master`**, and this
skill says so explicitly rather than handing over a brief that looks complete.

## Then, and only then — the storyline

Lay the interview answers onto the eight-act spine from
`b2b-deck-architecture.md` as **ordered assertions, one line per slide**. An assertion
is a sentence the buyer could disagree with — `Solusi` and `Manfaat` are topics, not
assertions, and a storyline made of topics produces a deck of labels.

Rules the storyline must already satisfy, because fixing them here is cheap and
fixing them in a rendered deck is not:

- The ISSUES act carries **their** findings, sourced to a document and a period. In
  product mode ISSUES is generic-by-segment and is marked as such; in prospect mode
  an empty ISSUES act **stops the pipeline** — no prospect document, no storyline.
- Read top to bottom, the assertions alone reconstruct the offer without a single
  supporting slide. If they do not, the order is wrong, not the wording.
- The cover assertion carries duration and deadline, **never price**.
- The closing assertion echoes the cover with only its last clause changed.
- No assertion promises savings, ROI, or payback — that is an honesty rail, and it is
  cheaper to never write it than to have `catalog-gate` block on it.
- Every number that appears in an assertion names where it came from.

Mark each assertion `FACT` (came from the interview, sourced) or `GAP` (needs an
answer before it can be drafted). A storyline may hand over with `GAP` lines; a deck
may not be drafted from them.

## Output

Product mode:

```
catalog/
  brief.md        interview answers · stop-gate answers · riskiest assumption · GAP list
  storyline.md    ordered assertions on the eight-act spine, each FACT or GAP
```

Prospect mode:

```
prospects/<slug>/
  brief.md        prospect-specific answers · documents on hand · GAP list
  storyline.md    ordered assertions, ISSUES act built from their documents
```

## Handoff

- Product mode → **`catalog-master`**, which drafts from `storyline.md` rather than
  inventing its own order.
- Prospect mode → **`catalog-variant`**, which qualifies with `meddic-scorecard` and
  then drafts.
- Either way the draft goes to **`catalog-gate`**, and the render prompts are written
  from the drafted slides — visual comes last, after the text has a PASS. A prompt
  authored from a storyline that is still `GAP` bakes the gap into a PNG.

## Hard rules

1. **No slide is written in this phase.** Producing draft slides here is the failure
   mode this skill exists to prevent.
2. Every answer is quantified and sourced, or marked `MISSING`. Never a plausible
   number.
3. The three stop gates are asked in this phase, in writing, and remain enforced by
   `catalog-master`.
4. Prospect mode with no prospect-produced document does not produce a storyline. It
   stops and asks for one.
5. The storyline is assertions, not topics, and it fixes the order the later phases
   follow. Reordering during drafting means coming back here, not improvising.
