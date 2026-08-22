# B2B Buyer Rubric (scored judgment)

> The **scored** complement to the binary linter in `b2b-deck-rubric.md`. Where the
> linter answers "does this slide pass?", this answers "how convincing is the offer,
> and where exactly is it weak?". `catalog-gate` runs both.
>
> Shape inherited from the investor scorecard in `gaspol-pitch`
> (`references/vc-review-rubric.md`): a scored dimension table, a per-slide dual
> test, conviction layers, cross-slide consistency, narrative gates. **Content is
> not inherited** — every dimension below traces to a finding in
> `research/buyer-brain.md`, and its source marker is cited so the trace is auditable.

## 1. The 10-dimension scorecard (score each 1–5 → total /50)

Score 1 = absent or misleading, 3 = adequate, 5 = best-in-class. For every dimension
below 3, write the ONE concrete fix.

| # | Dimension | What a 5 looks like | What a 1–2 looks like | Traces to |
|---|---|---|---|---|
| 1 | **Prospect sees their own problem** | Findings come from the prospect's own documents, quantified, with the source named | Generic industry problems the prospect never recognizes as theirs | `[S16]` findings-as-questions; `[S15]` "posisi tidak jelas" |
| 2 | **Unit the buyer already counts in** | Cost stated per vehicle per day, per trip, per rit — the unit they use on their own calculator | Efficiency percentages and abstract totals | `[S1]` per-kendaraan-per-hari |
| 3 | **Predictability, not just cost** | Addresses variance the buyer cannot plan around, not only the price level | Only argues "cheaper" | `[S2]` volatility is the stated problem |
| 4 | **Mechanism is legible** | The buyer can retell how it works; evidence-locked transitions, two independent signals | A component list, or "AI" as the mechanism | `[S15]` proof-first state machine |
| 5 | **Evidence of running operation** | A deployment running today, with what is proven separated from what is newly assembled | Maturity of a new module blurred into maturity of the platform | `[S16]` two-layer proof slide; `[S17]` |
| 6 | **Risk exit is named** | A dated stop point with acceptance criteria the **client** writes | "Trust us" or an unbounded pilot | `[S16]` client-signed criteria |
| 7 | **Adoption reality** | Addresses the driver/operator literacy boundary with visual encoding, not training promises | Assumes written procedures will be followed | `[S15]` literacy boundary |
| 8 | **Price arithmetic survives a calculator** | Anchor, discount, and total reconcile exactly; discount has a real reason | Rounded numbers, percent that does not match the rupiah | `[S16]` §7.1 anchoring |
| 9 | **Completion certainty** | Duration and an end date, plus a final instalment tied to field handholding | Open-ended phases, payment on go-live | `[S16]` §7.2 duration, §7.3 terms |
| 10 | **Honesty rails held** | No savings/ROI promise; assumptions stated before the big number; units never mixed | Promised savings, engineered-backwards assumptions, omzet added to cash loss | `[S16]` §6 |

**Grade bands:** 45–50 A (send it) · 40–44 B (strong, minor fixes) · 34–39 C
(real gaps) · 27–33 D (not yet) · <27 F (rebuild the offer).

**Gate:** total < 34 **OR** any single dimension = 1 → **BLOCKING**.

Dimension 1 is the load-bearing one. An offer deck that scores well everywhere else
while the prospect never sees themselves in it does not close, and no amount of
mechanism polish repairs that.

## 2. Dual test (per slide)

Every slide must do at least one of two jobs **for the buyer**. A slide that does
neither is a cut candidate.

- **A — Reduce the buyer's risk?** Does it retire a specific risk they carry
  (adoption, data, continuity, budget, being blamed internally)?
- **B — Increase the value of the outcome for them?** Does it grow what they get —
  more control, earlier information, fewer disputes, a defensible record?
- **C — Neither?** → flag MERGE or CUT.

Note the inversion from the investor version, which asks whether a slide reduces
**investor** risk. Here the risk being retired belongs to the person reading.

## 3. Four buyer conviction layers (coverage check)

A closing offer builds conviction on all four. Mark each Covered / Thin / Missing and
name the slide that carries it. A **Missing** layer is a structural hole.

1. **Masalah** — the prospect recognizes the problem as theirs, in their numbers.
2. **Mekanisme** — they understand how it works well enough to retell it.
3. **Bukti** — they believe it already runs somewhere real.
4. **Risiko** — they know their way out if it does not work.

`Risiko` is the layer most often missing, and it is the one procurement actually
needs, because management needs internal cover for a go/no-go decision `[S16]`.

## 4. Cross-slide consistency

Reconcile the numbers *across* the deck — there is always one finance person
dividing them on a calculator while you talk `[S16]`.

- [ ] **Anchor ↔ discount ↔ total** — the percent times the anchor equals the stated
      rupiah saving, and anchor minus saving equals the total, exactly.
- [ ] **Line items ↔ total** — the itemized table sums to the headline price.
- [ ] **Scope ↔ timeline** — every module priced appears in the timeline, and nothing
      in the timeline is unpriced or unexcluded.
- [ ] **Timeline ↔ deadline** — the start date is genuinely a consequence of the
      order deadline, not decoration.
- [ ] **Claims ↔ out-of-scope** — anything the impact slide implies but does not
      promise appears on the out-of-scope line.
- [ ] **Units never mixed** — omzet, profit, cash loss, and saving stay separate and
      are never summed `[S16]`.

Any unreconciled number is BLOCKING on its own. The damage does not stop at that
line: it spreads to the findings, which are the offer's actual strength `[S16]`.

## 5. Proof-of-operation gate *(replaces the investor "earned secret" gate)*

- The deck must carry **≥ 1 verifiable claim of a running deployment**.
- **Running vs asserted test:** for each claim ask "what would let the committee
  check this without taking our word for it?" A claim with no checkable form is
  marketing.
- **Maturity separation is mandatory.** What runs today and what is being assembled
  for the first time appear as two explicitly labelled layers, in the slide body —
  never in the speaker notes `[S16]`.
- 0 running-operation claims → **BLOCKING**. The deck is selling a plan, not a system.
- Maturity blurred between platform and new module → **BLOCKING** `[S16]` `[S17]`.

## 6. Narrative gates

- **Ops-manager retell** — after one pass, can an operations manager retell the offer
  to their owner? If the headlines alone do not enable that, the spine is muddy.
  (The investor version asks whether a partner can retell it to another partner; the
  audience changes, the test does not.)
- **One line worth repeating** — is there one sentence the ops manager will actually
  say out loud upstairs? If nothing is repeatable, nothing survives the meeting you
  are not in.
- **Objection sweep** — run the objection list in `research/buyer-brain.md`
  (`## Keberatan`). For each, is the deck's answer present, and is it structural
  rather than reassuring?

## 7. Anti-pattern sweep

Run `## Anti-pola` from `research/buyer-brain.md` against the deck. Any hit is
logged. These three are **BLOCKING on their own**:

- a promise of savings, ROI, or payback
- a big number stated before the assumption it rests on
- an operational identity of a reference customer disclosed without a contract
  permitting it (fleet counts, plates, driver names, delivery records, customer
  identities)

## Output contract (what `catalog-gate` emits from this file)

- The /50 score table with per-dimension grade + fix for anything < 3.
- Dual-test verdict per slide (A / B / cut).
- Buyer conviction coverage (4 rows, Covered / Thin / Missing, with slide named).
- Consistency checklist with any unreconciled number called out.
- Proof-of-operation verdict (count + running-vs-asserted note + maturity separation).
- Ops-manager retell + one-repeatable-line pass/fail.
- Objection sweep and anti-pattern sweep results.
