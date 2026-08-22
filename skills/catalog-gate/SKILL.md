---
name: catalog-gate
description: The blocking gate of gaspol-catalog. Use to adversarially review a B2B offer deck or sales catalog before it reaches a prospect — review deck penawaran, cek katalog sebelum dikirim, review render slide, audit penawaran B2B. Runs two layers that both block - a text layer that reuses the pitch-review engine pointed at the buyer rubric, and a separate render layer that checks the produced images against the deck text. Emits review.md with a PASS or BLOCKING verdict and loops back to catalog-variant or catalog-master until it passes.
---

# catalog-gate (two-layer blocking gate)

> The load-bearing skill. It does NOT trust what the draft says about itself. It
> reviews the deck the way an operations manager who wants a reason to say no would,
> then blocks until the offer is sendable.

**Announce:** "Running catalog-gate — reviewing the text, then the render. Both layers block."

## Input

`deck.md` or `catalog/` (from `catalog-variant` or `catalog-master`, OR a deck the
user brings), plus any rendered PNGs if they exist.

## Load (the brain)

- `../../references/b2b/b2b-deck-rubric.md` — 9 binary checks per slide.
- `../../references/b2b/b2b-buyer-rubric.md` — scored buyer dimensions (/50), dual
  test, four conviction layers, consistency, proof-of-operation gate, narrative gates.
- `../../references/b2b/b2b-deck-architecture.md` — the eight-act spine.
- `../../references/b2b/b2b-honesty-rails.md` — honesty rails, anchor arithmetic,
  urgency-kit validity.
- `../../references/b2b/b2b-visual-contract.md` — the render layer's guards.
- `../../research/buyer-brain.md` — `## Keberatan` feeds the skeptic; `## Anti-pola`
  feeds the sweep.

---

## LAYER ONE — text

Invoke `pitch-review` from the sibling plugin `gaspol-pitch` with its optional
`rubric` parameter pointed at `b2b-deck-rubric.md` and `b2b-buyer-rubric.md`. The
engine is reused, never copied — a copied rubric is how two standards drift apart
without anyone noticing.

If `pitch-review` is not installed, STOP and tell the user. Do not reimplement it
here and do not review with a reduced set of layers.

Run all layers in order:

### (a) Binary lint — 9 checks per slide
For EVERY slide, pass/fail each: **Value-Anchor · Pyramid · Assertion-vs-Topic ·
One-Message · Linguistic-Fluff · 5-Second · Data-Parsing · Platform-Risk ·
Forwardable.** Any fail is logged with the slide and the exact offending text quoted.

### (b) Scored judgment
Apply `b2b-buyer-rubric.md`: the **10 buyer dimensions scored 1–5 (=/50)** with a
per-dimension fix for anything < 3; the **dual test** per slide (reduces the buyer's
risk? / increases the buyer's outcome? / cut); the **four buyer conviction layers**
(Masalah / Mekanisme / Bukti / Risiko — Covered / Thin / Missing, naming the slide).

### (c) Thresholds
The buyer rubric's gate: total < 34, or any single dimension = 1. Dimension 1 —
whether the prospect sees their own problem, in their own numbers — is load-bearing;
an offer that scores well everywhere else while the prospect never sees themselves in
it does not close.

### (d) Cross-slide consistency
Reconcile across slides: anchor × discount = stated saving, anchor − saving = total,
line items sum to headline, scope ↔ timeline ↔ deadline, claims ↔ out-of-scope line,
units never mixed. **Recompute the arithmetic; never accept it as written.** There is
always one finance person dividing these on a calculator while you talk.

### (e) Proof-of-operation gate + narrative gates
Require ≥ 1 verifiable running-deployment claim, with the running-vs-asserted test.
Require maturity separation between platform and newly assembled module, **in the
slide body**. Then run the ops-manager retell and the one-repeatable-line test.

### (f) Skeptic subagent — objection simulation
Prompt a fresh reviewer as a **skeptical operations manager**, not a venture partner:
"Assume this offer has problems. For each slide write the toughest question you would
ask your own boss about it, then name the 3 weakest claims in the whole deck."

Feed it `## Keberatan` from `research/buyer-brain.md` so the questions are the ones
buyers actually voice, not invented ones. Fold its output into the report.

### (g) Honesty rails
Run `b2b-honesty-rails.md`. These three block on their own: a promise of savings, ROI,
or payback; a big number stated before the assumption it rests on; an operational
identity of a reference customer disclosed without a contract permitting it.

### (h) Urgency-kit validity
Every urgency device must genuinely apply. A deadline that will quietly be extended, a
discount with no real reason, a countdown not tied to the send date, a start date that
is not actually a consequence of the deadline — each is BLOCKING. Once a deadline is
quietly extended, no later deadline is ever believed again.

---

## LAYER TWO — render

**A separate phase, and this is not tidiness.** A deck has passed layer one and
blocked on layer two the same day: the text was right and the render prompt was
wrong, so no amount of text review could have caught it.

Runs only once images exist — produced by `catalog-visual`, which authors the prompts
after layer one passes. For every image, compare it against its source text, line by
line, using `b2b-visual-contract.md`:

- [ ] **Duplicated text** — a block printed twice, a label rendered both inside and
      outside its container
- [ ] **Fabricated numbers** — any figure on the canvas that is not in the deck text
- [ ] **Language leak** — a second language appearing unasked
- [ ] **Missing headline** — a "no other text" instruction having deleted the headline
      that was supposed to print
- [ ] **Truncated qualifier** — a hedge or source note cut in half
- [ ] **Dropped disclaimer** — an illustration stamp or confidentiality line lost when
      the prompt was upgraded
- [ ] **Logo failure** — a client wordmark drawn by the model instead of pasted, or a
      lockup colliding with the headline
- [ ] **Human face** — any face on any slide
- [ ] **Chapter rail** — generated instead of pasted, or present on a slide that
      should have none

**Without images, layer two reports `NOT RUN`. Never `PASS`.** An unrun check is not
a passed check, and reporting it as one is the exact failure this layer exists to
prevent.

On a render defect, route back to **`catalog-visual`** to fix the **prompt** and
regenerate that slide. Never resolve a render defect by editing `deck.md` to match
what the image drew — that rewrites a deck which already passed layer one, to fit a
mistake.

---

## Output — `review.md`

```
## Layer 1 — text
### Binary lint (per slide)
| slide | the 9 checks | fails (with quoted offending text) |

### Score: NN/50 — grade <A–F>
| dimension | score | fix if <3 |
Dual-test verdict per slide · Buyer conviction layers (4 rows, slide named)

### Consistency
recomputed arithmetic; any unreconciled number called out

### Proof of operation · narrative gates
running-vs-asserted · maturity separation y/n · retell · repeatable line

### Skeptic simulation
toughest question per slide · the 3 weakest claims

### Honesty rails · urgency validity
rail hits · every urgency device: genuinely applies y/n

## Layer 2 — render
| image | 9 render checks | defects (with the deck line it contradicts) |
(or) NOT RUN — no images produced

## VERDICT: PASS | BLOCKING
(if BLOCKING) exact fix list → return to catalog-variant / catalog-master
```

## Blocking verdict + gate loop

Return **BLOCKING** if ANY of: a binary check fails · score < 34 · any single
dimension = 1 · an unreconciled number · 0 running-operation claims · maturity blurred
between platform and module · an honesty rail hit · an urgency device that does not
genuinely apply · any render-layer defect.

On BLOCKING, route back with the exact fix list and re-review — text defects to
`catalog-variant` / `catalog-master`, render defects to `catalog-visual`. Only
**PASS** releases anything to a prospect, and the release itself is
`catalog-finish`'s job, not this skill's.

**Do not soften a verdict to be polite.** That defeats the plugin. And the stakes are
higher here than on a single investor deck: one catalog goes to dozens of companies,
so one unchecked claim travels dozens of times.

## Self-test (this skill's correctness contract)

- `../../references/b2b/examples/bad-catalog.md` **MUST** be caught with a BLOCKING
  verdict, and each planted defect must name the layer that caught it:

  | Defect | Layer |
  |---|---|
  | fluff B2B (`solusi end-to-end terintegrasi`, `world-class`) | (a) Linguistic-Fluff |
  | headline labels (`Solusi`, `Harga`, `Manfaat`) | (a) Assertion-vs-Topic |
  | one slide carrying four ideas joined by "dan" | (a) One-Message |
  | price on the cover | (b) via the architecture reference |
  | slide 9 total disagreeing with slide 7 price | (d) consistency |
  | a human face on a slide | Layer 2 / (g) visual contract |
  | a new module claimed as proven at scale | (e) proof-of-operation |
  | a deadline that does not genuinely apply | (h) urgency validity |

- `../../references/b2b/examples/good-catalog.md` **MUST** return PASS.
- **This skill is correct only if it BLOCKS the bad fixture and PASSES the good one.**
  If a planted defect is not caught, fix the rubric — never the fixture.
