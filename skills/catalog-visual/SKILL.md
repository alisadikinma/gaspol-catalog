---
name: catalog-visual
description: Fifth phase of gaspol-catalog, run only after catalog-gate layer one PASSES. Use to author one 16:9 image prompt per slide and assemble the sendable file — bikin prompt gambar slide penawaran, render slide katalog, buat visual deck B2B, susun PDF penawaran, tempel pita babak dan logo. Bakes each slide's exact headline and numbers into the prompt verbatim, carries the render guards that stop duplicated text and fabricated numbers, leaves logo and chapter rail as paste-after-render slots, and hands the PNGs back to catalog-gate layer two, which blocks on its own. Image MCP is optional; the prompts are the deliverable.
---

# catalog-visual

> The render defect is born in the prompt, not in the deck. This phase writes prompts
> that cannot produce the known defects, then hands the result back to the gate that
> checks whether it worked anyway.

**Announce:** "Running catalog-visual — one prompt per slide, then back to catalog-gate layer two."

## Precondition — layer one PASS

`review.md` layer one verdict = **PASS**. Do not author prompts for a deck that has
not passed the text layer. Rendering an unreviewed deck multiplies the cost of every
fix: a wrong word is one edit in `deck.md` and one regenerated PNG, and a wrong
storyline is the whole deck twice.

If layer one is BLOCKING, return to `catalog-variant` or `catalog-master` with its fix
list. Do not start here.

## Load (the brain)

- `../../references/b2b/b2b-visual-contract.md` — **the authority.** Zero faces, 16:9,
  bright-corporate tone, the 60/40 canvas contract, one-colour-one-job palette rules,
  the four render guards (A duplicated text, B fabricated numbers and phrases, C the
  three silent leaks, D logo and lockup), E chapter rail and full-bleed, and the PDF
  distribution rules.
- `../../references/b2b/b2b-deck-architecture.md` — which act each slide belongs to,
  which slides carry a chapter rail and which carry none, the impact slide, the
  cliffhanger glyph.
- `deck.md` and `review.md` from `catalog-gate` — the source text, verbatim.

## Reuse (installed skills — optional, degrade gracefully)

| Skill | For | If absent |
|---|---|---|
| `carousel-gen` (`ai-image-carousel-prompt-gen`) | the prompt machinery — author the prompt, the consumer fulfils it | Use the five-section template below. It is self-sufficient. |
| `gaspol-design` | palette, font, and chart choice | Fall back to the palette rules in `b2b-visual-contract.md`. Note the fallback in the run output. |

Neither is a hard stop. Note in the output which path was taken, because a deck
themed by fallback and a deck themed by `gaspol-design` are not identical and the
next revision needs to know which it is.

## Step 1 — author one prompt per slide

For EVERY slide in `deck.md`, write `prompts/slide-NN.md` in five sections:

```
LAYOUT:      variant + grid placement. ~60% canvas visual, ~40% text — the
             single most decisive control in the whole file.
VISUAL:      editorial / infographic / diagram. Objects and evidence.
             NO HUMAN FACE on any slide, cover included.
STYLE+PALETTE: bright and corporate-precise, never cinematic-dark. One structure
             colour, one accent colour, neutral body — one colour, one job.
             [RUNTIME PLACEHOLDER: palette + font from the user]
TEXT:        the slide's EXACT headline and EVERY number, VERBATIM in quotes,
             each with its font weight and size.
CONSTRAINTS: the render guards below, in full, every time.
```

### The guard block — paste into every prompt, never abbreviate

Each of these exists because a real deck shipped with the defect:

- **Exactly once.** Every text block appears **once**. Name the container explicitly —
  "the label sits inside the card and is not repeated outside it". Image models repeat
  text; on one measured deck it hit nearly half the slides.
- **No number that is not in the text.** Bake the exact figures from `deck.md` and
  forbid any other number appearing on the canvas.
- **One language.** Forbid a second language unless the deck itself is bilingual.
- **The headline prints.** Never write "no other text" as a blanket instruction — it
  deletes the headline that was supposed to print. Say which text prints, then forbid
  the rest.
- **Qualifiers print whole.** A hedge or a source note is text like any other: quote it
  verbatim and require it complete. Half a qualifier is worse than none.
- **Disclaimers survive.** When a prompt is upgraded, re-check that the illustration
  stamp and confidentiality line are still in it. They are the first thing lost.
- **Empty logo slot.** The prospect's wordmark is **never drawn by the model.** Leave
  the slot empty and paste the file after rendering. A rendered wordmark is always
  malformed, and a malformed wordmark on page one is the most expensive defect in the
  deck. Place the lockup **inside the bottom band**, reversed and left-aligned — a
  top-right corner placement collides with headlines whose length no prompt can
  guarantee.
- **No chapter rail in the prompt.** The rail is pasted after render, never generated.
- **Full-bleed by pixel columns.** Say "the first and last pixel column", not
  "edge to edge" — the latter does not reliably work.

## Step 2 — render, if an image MCP exists

Detect any image-generation MCP and confirm its model id through the server's own
model-listing tool rather than assuming one.

- **MCP present** → generate `slide-NN.png` per prompt. Then run a first-pass
  inspection with a fresh subagent prompted "assume there are issues — find them":
  overflow, clipping, garbled glyphs, a number that does not match `deck.md`, broken
  layout. Regenerate on defect, at most twice, then flag for manual fix.
- **MCP absent** → write a one-line note at the top of `prompts/` — "no image MCP,
  paste each prompt manually" — and stop after the prompts. **This is not a failure.**
  The prompts are the deliverable, and `catalog-gate` layer two will correctly report
  `NOT RUN`.

This first pass is **not** the gate. It catches gross breakage cheaply so the gate is
not spent on obvious defects. The gate still runs, in full, afterwards.

## Step 3 — assemble what the model must not draw

Three things are composited after rendering, never generated:

1. **Chapter rail** — a full-height vertical band on the **left edge**, text rotated
   90°, structure colour for ISSUES and accent colour for SOLUTIONS. Content slides
   only: cover, timeline, next, CTA, and closing carry **none** — their act is already
   finished. Band width around 1.7% of canvas; the band's font size scales to canvas
   width, never an absolute pixel value, because small text is unreadable from three
   metres away in a meeting room. When QA measures band height, measure the
   **proportion of dark pixels**, not average luminance.
2. **Client logo** — the real file, pasted into the bottom band.
3. **PDF distribution chrome** — a **repeating diagonal watermark across the whole
   page**, not one corner stamp, since a corner stamp disappears the moment someone
   photographs part of a slide. Watermark colour follows each page's light or dark
   value, at roughly 5% opacity; heavier than that and it fights the content. The
   confidentiality line goes in a band **outside the slide area** — extend the page
   slightly downward — because inside the frame it collides with something now or in
   the next revision.

## Step 4 — hand back to the gate

Submit the PNGs to **`catalog-gate` layer two**. That layer blocks on its own and is
the reason this phase exists as a separate step at all: a deck has passed layer one
and blocked on layer two the same day, because the text was right and the prompt was
wrong. No amount of text review could have caught it.

On any render defect, fix **the prompt**, regenerate that slide, and re-submit. Do not
edit `deck.md` to match what the image happened to render — that inverts the whole
pipeline and silently rewrites a passed deck to fit a mistake.

## Output

```
prompts/
  slide-NN.md           one per slide, five sections, full guard block
  README.md             MCP present or absent · gaspol-design or fallback theming
  slide-NN.png          only if an image MCP rendered them
```

Then → `catalog-gate` layer two → `catalog-master` / `catalog-variant` on BLOCKING.

## Hard rules

1. Layer one PASS is the precondition. No PASS, no prompts.
2. Zero human faces, on every slide, including the cover — a founder's face makes the
   reader price an individual consultant rather than a company they can contract.
3. Brand chrome is a runtime placeholder. Never bake a specific logo, colour value,
   font name, or handle into a prompt or into `references/`.
4. Logo, chapter rail, and watermark are composited, never generated.
5. Every number in a prompt is copied verbatim from `deck.md`. A number that appears
   only on the canvas is a fabricated number, and the gate treats it as one.
6. An unrendered deck reports layer two as `NOT RUN`. Never as PASS.
