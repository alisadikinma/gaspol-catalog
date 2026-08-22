# B2B Offer-Deck Rubric (binary linter)

> The **binary** brain for `catalog-gate` layer one. Every check is pass/fail — no
> scoring here; scoring lives in `b2b-buyer-rubric.md`.
>
> Seven of the nine checks are inherited verbatim from the investor linter in
> `gaspol-pitch` (`references/investor-deck-rubric.md`, PART C) — the mechanics of a
> slide failing to communicate do not change with the audience. Only the examples
> change. `Forwardable` is inherited and **promoted from bonus to mandatory**.
> `Platform-Risk` is the one check rewritten from scratch.

## How to run

For EVERY slide, mark each of the nine checks pass/fail. Any fail is logged with
the slide number and the **exact offending text quoted**. A check that cannot be
evaluated because the slide lacks the material is a fail, not a skip.

## The nine checks

### 1. Value-Anchor
Can a reader extract, without guessing: whose job changes · which artifact does it ·
which situation · which problem it removes?

- **PASS** — "Selisih bahan bakar ditelusuri per perjalanan, bukan per bulan"
- **FAIL** — "Modul pemantauan bahan bakar" (a component name, not an outcome)

### 2. Pyramid Principle
Does the slide lead with its conclusion, then evidence, then the granular figure at
the bottom? Buyers read top-down and stop early.

- **FAIL** — a slide that builds up to its point in the last line

### 3. Assertion-vs-Topic
Is the headline an active argument, not a label? A label headline forces the reader
to do the work the deck was supposed to do.

- **PASS** — "Dua puluh tiga persen order tidak bisa dijawab posisinya saat pelanggan menelepon"
- **FAIL** — "Masalah" · "Solusi" · "Harga" · "Manfaat" · "Teknologi"

### 4. One-Message
Does the slide carry two ideas stitched with "dan" / "serta" / "sekaligus"? If yes →
FAIL, split into two slides.

- **FAIL** — "sistem mencatat posisi dan bahan bakar dan absensi dan bukti pengiriman"

### 5. Linguistic-Fluff
Banned vendor slop. Any occurrence → FAIL.

`solusi end-to-end terintegrasi` · `solusi menyeluruh` · `world-class` · `berbasis AI
terdepan` · `transformasi digital` · `sinergi` · `revolusioner` · `terdepan di
kelasnya` · `one-stop solution` · `state-of-the-art` · `next-generation` ·
`kelas dunia` · `mutakhir`

The test behind the list: **can the buyer verify it, and does it map to one job they
recognize?** A phrase failing both is fluff even if it is not on the list.

### 6. 5-Second Rule
Is the core point graspable in five seconds with no clutter? Count elements: a slide
with more than one chart, more than one table, or more than seven bullets fails on
sight.

### 7. Data-Parsing
Numbers strictly formatted: `Rp 298.800.000`, `23%`, `4 bulan`, `1.790 order`. No
spelled-out numbers, no junk Unicode, no mixed thousand separators inside one deck.

Every percentage carries **one line saying what it is a percentage of**. A bare
percent reads as invented.

### 8. Platform-Risk *(rewritten for this audience)*
Does the deck leave the buyer exposed to the vendor, with no declared way out?

Fail on ANY of:

- who owns the operational data is not stated
- no export path off the system is named
- no service level or response commitment is stated
- the deck depends on one closed third-party service (a map provider, a messaging
  gateway, a single hardware supplier) with no named fallback
- continuity if the vendor stops operating is unaddressed

Its investor-deck ancestor asked "is this over-reliant on one closed API?". The buyer
version asks the same question **from the buyer's side of the table**: not "is the
vendor fragile" but "what happens to me if it is".

### 9. Forwardable *(inherited, promoted to mandatory)*
Read the deck cold, with zero spoken context. Does the argument stand?

This check is bonus in the investor rubric and **mandatory here**, because the
premise is different in kind: an offer document circulates without its presenter. It
is opened in a meeting by someone who was not in the room. Every slide has to stand
alone, and a defence that lives only in the speaker notes does not exist.

## Deck-economy discipline

Target ≤ 16 slides. For each slide: **keep** / **merge** (two thin slides → one) /
**cut** (fails the scored dual-test) / **split** (carries two messages).

A deck that needs an appendix to make its case has buried its case.

## Headline rule

Reading ONLY the headlines, in order, must reconstruct the whole argument. Headlines
are complete sentences, at most two lines, with the insight at the front.

## Contextualized numbers

Never a floating number. Every figure carries what it is measured against — a
baseline, a period, a denominator, or the document it came from.

## Output contract (what `catalog-gate` emits from this file)

A per-slide table: slide number · the nine checks · every fail with the exact
offending text quoted.
