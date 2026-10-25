---
name: catalog-visual
description: Fifth phase of gaspol-catalog, run only after catalog-gate layer one PASSES and brand.md exists. Use to author one 16:9 image prompt per slide and assemble the sendable file — bikin prompt gambar slide penawaran, render slide katalog, buat visual deck B2B, susun PDF penawaran, tempel pita babak dan logo. Follows the seller's own house standard from brand.md rather than a generic default, bakes each slide's exact headline and numbers into the prompt verbatim in the deck's own language, carries the seventeen render guards that stop duplicated text, fabricated numbers, leaked layout words, leaked slot words, leaked icon descriptions, miscounted objects, stray brand logos, faces on props, and language and spelling drift, leaves logo and chapter rail as paste-after-render slots, and hands the PNGs back to catalog-gate layer two, which blocks on its own. Image MCP is optional; the prompts are the deliverable.
---

# catalog-visual

> The render defect is born in the prompt, not in the deck. This phase writes prompts
> that cannot produce the known defects, then hands the result back to the gate that
> checks whether it worked anyway.

**Announce:** "Running catalog-visual — one prompt per slide, then back to catalog-gate layer two."

## Two preconditions, both blocking

1. **`review.md` layer one verdict = PASS.** Rendering an unreviewed deck multiplies
   the cost of every fix: a wrong word is one edit and one regenerated PNG, a wrong
   storyline is the whole deck twice. If layer one is BLOCKING, return to
   `catalog-variant` or `catalog-master` with its fix list.

2. **`brand.md` exists and has no unfilled `[RUNTIME PLACEHOLDER]`.** If it is missing
   or incomplete, STOP and run the brand intake in `catalog-brainstorm` — do not
   render, and do not fill the gaps with your own taste.

   This precondition is the whole reason this revision exists. A deck once rendered
   with every palette and layout placeholder still empty; the image model supplied its
   own defaults, and the seller rejected the finished deck outright as generic. An
   unfilled placeholder is not neutral — it hands the design decision to the model.

3. **Every prompt is a file before it is a render call.** Write
   `prompts/slide-NN.md` first, render *from* that file, and make every later revision
   by **editing the file** — never by retyping the prompt into the conversation.

   This is the single most expensive defect this plugin has measured, and it is not on
   the guard list because it is upstream of the guard list. A prompt that lives only in
   a chat turn gets retyped from memory at the next revision. What survives retyping is
   what a human remembers — the headline and the numbers. What silently dies is the
   guard block, because it is long, dull, and invisible in the output until it fails.
   A deck rendered five times that way collects five different defects, each one a
   guard that has been written down for years.

## Load (the brain)

- `../../references/b2b/b2b-brand-intake.md` — **read first.** The seller's own house
  standard outranks every default below it.
- `../../references/b2b/b2b-visual-contract.md` — **the authority.** The DEFAULT vs
  KANON split, the 60/40 canvas contract, one-colour-one-job, the seventeen render guards
  A–Q, ref-conditioning, generator hygiene, and the PDF distribution rules.
- `../../references/b2b/b2b-deck-architecture.md` — which act each slide belongs to,
  which slides carry a chapter marker and which carry none, the impact slide.
- `brand.md`, `deck.md`, and `review.md` — the source, verbatim.
- The nearest `ref/contoh.md` (deck folder or any parent): renders the human rejected and
  approved, one line each with the reason. **Open every image it lists with Read before
  writing a prompt.** A new prompt must not reproduce what a rejected image shows. Missing
  file → note "no contoh.md" in the run output and go on.

## Reuse (installed skills — optional, degrade gracefully)

| Skill | For | If absent |
|---|---|---|
| `carousel-gen` (`ai-image-carousel-prompt-gen`) | the prompt machinery | Use the template below. It is self-sufficient. |
| `gaspol-design` | palette, font, and chart choice **only where `brand.md` is silent** | Fall back to the palette rules in the visual contract. Note the fallback in the run output. |

Neither is a hard stop, but neither overrides `brand.md`. A house standard beats a
design skill beats a plugin default, in that order, always.

## Step 1 — author one prompt per slide

**Tooling first.** Do not hand-write prompt files. Write the project's `slides.json`
(audience, client, ref_dir, and per slide: n, sid, layout, visual, text lines, refs, ai,
people, extra), then run `deckkit prompts slides.json`. It writes `prompts/slide-NN.md`
and `prompts/manifest.json`, with the preset's style and the full guard block in every
file. The preset comes from the seller's house standard (see `b2b-brand-intake.md`,
"Seller house standard"), resolved through `brand.md`. No house standard resolved →
say so in the run output and fall back to the theming in `b2b-visual-contract.md`.
Command forms and options: `docs/deckkit.md` and `docs/tool-routing.md`.

For EVERY slide in `deck.md`, the resulting `prompts/slide-NN.md` carries six sections.

**Two documents, one direction.** `deck.md` may carry a short visual note per slide —
the design intent, written in the deck's language, for a human to argue with.
`prompts/slide-NN.md` is the render contract: generated **from** that note, carrying
the full guard block. The note never renders anything and the prompt never invents
intent. When they disagree, the note wins and the prompt is regenerated from it — a
prompt edited to match a render that already happened is the pipeline running
backwards.

Each prompt file ends with a **revision log** (a final `REVISION LOG` heading):
one line per regeneration, what changed and which defect forced it. `deckkit prompts`
keeps every existing log line when it rewrites a file and adds a dated line from the
slide's `log` field. Without that line the same guard gets deleted again next
month by someone tidying up a long prompt. `deckkit gen` never sends the log to the
image model: it names old defect text, which the model could print. The
instructions may be written in English; **every string that will be printed is quoted
in the deck's own language, character for character.**

```
LAYOUT:      geometry only — "upper third, left-aligned", "right half, three stacked
             cards". ~60% canvas visual, ~40% text unless brand.md says otherwise.
             NO ROLE WORDS: never write HEADLINE, SUBTITLE, CAPTION, PRODUCT LOGO,
             BODY. The model prints them (guard G).
VISUAL:      objects, scene, evidence. Shapes of icons only — never what an icon
             means (guard H). Never a set of objects whose count must be exact
             (guard F): print the number as large text instead.
STYLE:       from brand.md — palette with each colour's one job, font, tone, ground.
             Cite the house standard the layout came from.
TEXT:        DAFTAR LENGKAP TEKS DI KANVAS INI — every printed string in quotes,
             in the deck's language, each with its weight, size and position, and
             every dashboard/chart label counted as a string (guard L). Closes with:
             "no other text may appear on this canvas." (guard I)
LANGUAGE:    ATURAN BAHASA — KRITIS. Name the language. Forbid translation and any
             second language. (guard J)
CONSTRAINTS: the guard block below, in full, every time.
REFS:        file paths from brand.md for a specific face, an in-scene logo, or a
             prospect evidence photo — plus the note that refs suspend no guard.
```

### The guard block — paste into every prompt, never abbreviate

Each exists because a real deck shipped with the defect. Full rationale in
`b2b-visual-contract.md` §A–§L.

- **Exactly once** — every text block appears once; name its container explicitly.
- **No number not in the text** — bake the exact figures, forbid every other number.
- **Never count** — no set of objects whose quantity must be right. Print the number.
- **No role words** — geometry, not `HEADLINE` / `PRODUCT LOGO`.
- **No icon meanings** — the shape, never the sentence explaining it.
- **Whitelist, then close** — list what prints, *then* forbid the rest. Never the
  bare instruction "no other text": it deletes the headline that was meant to print.
- **One language, named** — the deck's language, no translation, no second language.
- **Qualifiers print whole** — a hedge or source note is text like any other.
- **The `ILUSTRASI` stamp is a listed string** — once per slide, with its position.
  It is the first thing lost when a prompt is upgraded; re-check it every revision.
- **Dashboard contents are text** — every label inside a fake screen is quoted, or
  the model invents city names and figures that read as the prospect's own data.
- **Empty logo slot** — the wordmark is never drawn by the model. Paste it after
  rendering, inside the bottom band. The single exception is a logo that is an object
  in the scene (shop signage, an app header), which is done with `refs`, never with
  a description.
- **No chapter marker in the prompt** — pasted after render, never generated.
- **No page number anywhere in this phase** — not in the prompt, and not pasted in
  Step 3 either. Its slot in the bottom band stays empty through every render and
  every revision. A generated number drifts each time one slide is re-rendered, and
  a pasted number goes stale the moment the human reorders, drops, or adds a slide
  during review. Numbers are stamped in Step 5, and only after the human approves.
- **Full-bleed by pixel columns** — "the first and last pixel column", not "edge to
  edge", which does not reliably work.
- **An empty slot is a shape, not a role** (guard M) — "an empty light-grey rounded
  rectangle, no text, no letters, no icon inside", plus an explicit ban on the word
  `LOGO` appearing on the canvas. Naming the slot by its role gets the role printed
  inside it.
- **Every branded object is explicitly blank** (guard N) — laptop lids, phones,
  monitors, packaging. Naming the object is not enough; its blankness must be asked
  for, or the model attaches a real manufacturer's mark on its own.
- **Zero faces reaches into the props** (guard O) — cards, screens, posters, frames.
  State what is on the prop ("a plain white card with two thin lines, no photo, no
  face"), or a face arrives inside the object the characters are holding.
- **A brand word beside its mark prints once** (guard P) — when a logo tile sits inline
  with a company name, say so: "the word <name> is written EXACTLY ONCE on the whole
  canvas, right after its mark."
- **Spelling is checked letter by letter** (guard Q) — after render, re-read every
  whitelisted string against the deck character for character, not for presence.
  Non-English suffixes drop off the last word of a long sentence and the sentence still
  looks right.

## Step 1b — the recurring character, before any slide

If `brand.md` names a recurring character (a mascot, an AI assistant figure), render
its **character sheet** first — full body and close-up on one canvas — from its own
prompt file, get the owner's word on it, and attach it as a ref on every slide that
shows the character. See "Tokoh, wajah, dan jumlah gambar acuan" in the visual
contract: an AI figure must read as AI at slide distance, several faces go into one
strip image because generators cap the ref count, and real team members may be drawn
as cartoons with their photos as likeness refs only.

## Step 2 — render, if an image generator exists

Confirm the model id through the server's own model-listing tool rather than assuming
one. **Raise the poll timeout before rendering, not after a failure** — a dense slide
has exceeded 420 seconds and succeeded at 540, and a timed-out render still spends
its quota.

- **Generator present** → run `deckkit gen prompts/manifest.json --ver rN`; it renders
  every slide from its prompt file into `renders/rN/NN.png`. A render whose prompt has
  changed since is reported `stale` and never overwritten: move it to `prompts/_rejected/`
  or use a new `--ver`. Then run a first-pass
  inspection with a fresh subagent prompted "assume there are issues — find them",
  checking specifically for the seventeen guard classes plus overflow, clipping, and
  garbled glyphs. Regenerate on defect, at most twice, then flag for manual fix.
  **Move every rejected render to `prompts/_rejected/` with a filename saying what
  was wrong** — never overwrite it. Without the rejected file, the same defect gets
  re-argued at the next revision.
- **Generator absent, or no client configured** → note "no image generator, paste each
  prompt manually" at the top of `prompts/` and stop after the prompts. Rendering stays
  optional and the layer-two verdict is `NOT RUN`. **This is not a failure.** The prompts
  are the deliverable and `catalog-gate` layer two will correctly report `NOT RUN`.

This first pass is **not** the gate. It catches gross breakage cheaply. The gate still
runs, in full, afterwards.

## Step 3 — assemble what the model must not draw

Every post-render step has a tool. Find the task in `docs/tool-routing.md` before
writing any script; the page number and band steps below still wait for Step 5.

Three things are composited after rendering, never generated. Anything pasted **inside
the scene** (a logo on a monitor, a vehicle side, an app header; a face photo in a
frame) uses the single-colour slot technique in `b2b-visual-contract.md`, "Tempel
sesudah render": the prompt asks for a flat area in one colour the palette never uses,
a script finds it, checks the expected slot count, pastes the real file, and confirms
zero leftover pixels of that colour. Flags, badges and sample-evidence cards are drawn
by the same script, never re-rendered. **The page number is
not one of them** — its slot stays empty here; see Step 5.

1. **Chapter marker** — shape and position from `brand.md`; the visual contract's
   left vertical band is only the default. Content slides only: cover, timeline, next,
   CTA, and closing carry none — their act is already finished. Font size scales to
   canvas width, never an absolute pixel value. When QA measures it, measure the
   **proportion of dark pixels**, not average luminance.
2. **Logos** — the real files, pasted into the bottom band.
3. **PDF distribution chrome** — a **repeating diagonal watermark across the whole
   page**, not one corner stamp, which disappears the moment someone photographs part
   of a slide. Measured settings that work: each instance **10–14% of canvas width**,
   tiled to roughly **three columns by four rows**, rotated 30°, odd rows offset half a
   column, **8–12% opacity**. Fit the text by its size **after** rotation — a single
   mark sized to 58% of the width reads as a printing fault and gets clipped at the
   corners once turned. Pick the colour **per page** from the luminance of the centre
   band (about 15–85% of width, 20–80% of height): white on dark pages, the structural
   colour on light ones. A dark mark on a dark page is no watermark at all. The
   confidentiality line goes in a band **outside the slide area** — extend the page
   slightly downward — because inside the frame it collides with something now or in
   the next revision.

## Step 4 — hand back to the gate

Submit the PNGs to **`catalog-gate` layer two**. That layer blocks on its own and is
why this phase exists separately: a deck has passed layer one and blocked on layer two
the same day, because the text was right and the prompt was wrong.

On any render defect, fix **the prompt**, regenerate that slide, and re-submit. Do not
edit `deck.md` to match what the image happened to render — that inverts the pipeline
and silently rewrites a passed deck to fit a mistake.

## Step 5 — page numbers and the PDF, only after the human approves

**No PDF exists before this step.** Review happens on the un-numbered PNGs. The PDF is
built once, on the human's explicit word, in the same run that stamps the numbers and
lays the watermark. A PDF built "so it is ready" is stale at the first reorder, and it
gets forwarded.

Page numbers are the **last** thing stamped, in a separate run, and **only after the
human who owns the deck has reviewed the rendered slides and explicitly said they are
approved.** Until that word is given, every slide ships to review with the page-number
slot empty — including every re-render in between.

- **Ask, never assume.** A PASS from `catalog-gate` layer two is not approval. Silence
  is not approval. An approval of one slide is not approval of the order. Ask once,
  plainly: "Urutan dan isi slide sudah final? Boleh saya tempel nomor halaman?"
- **Stamp from the approved order**, not from file names: numbers run 1..N in the
  order the human approved, with no gaps and no repeats.
- **Any change after stamping resets this step.** A slide added, removed, moved, or
  re-rendered means the numbers are stripped (restamp from the clean, un-numbered
  render) and the human is asked again.
- Keep the un-numbered renders. Stamp into a separate output so a later reorder never
  has to paint over an old number.
- The tools refuse until told: `deckkit stamp SRC DST --approved` and
  `deckkit band SRC DST --text "..." --numbers --approved`. Pass `--approved` only after
  the human's explicit word.

## Revision rounds

A list of per-slide changes from the deck's owner is not a shortcut past the phases.
Apply it to `deck.md`, run `catalog-gate` layer one on the changed text, then render.
Read **"Putaran revisi"** in `b2b-visual-contract.md` before touching a prompt: term
renames across slides, caveats lost in a merge, a promise restated more broadly than
its terms, a "cheaper" claim that inverts for another package, objects that print their
own name, and what "done" means.

## Output

```
prompts/
  slides.json           the deck spec, input of `deckkit prompts`
  manifest.json         slide, prompt file and refs, input of `deckkit gen`
  slide-NN.md           one per slide, six sections, full guard block, revision log
  README.md             generator present/absent · house standard or fallback theming
  slide-NN.png          only if an image generator rendered them
  _rejected/            every discarded render, named for its DEFECT — never _v2,
                        _v3, or a date. A version name keeps the order; only a defect
                        name keeps the reason.
```

Then → `catalog-gate` layer two → `catalog-master` / `catalog-variant` on BLOCKING.

## Hard rules

1. Layer one PASS **and** a complete `brand.md`. Either one missing, no prompts.
2. `brand.md` outranks this skill; this skill outranks the plugin defaults. Never the
   other way round.
3. Human faces follow `brand.md`. Default is zero. Where a face is approved, it is
   conditioned from the portrait file via `refs` — a described face is a different
   person every render.
4. Brand chrome is runtime input. Never bake a specific logo, colour value, font name,
   or handle into a prompt or into `references/`.
5. Logo, chapter marker, and watermark are composited, never generated — except a logo
   that is an object inside the scene, which is `refs`.
6. Every number in a prompt is copied verbatim from `deck.md`. A number that appears
   only on the canvas is a fabricated number, and the gate treats it as one.
7. Never ask the model to draw a countable set. Print the number.
8. An unrendered deck reports layer two as `NOT RUN`. Never as PASS.
9. **No render without its prompt file.** Every generation and every regeneration runs
   from `prompts/slide-NN.md`. Retyping a prompt into the conversation drops the guard
   block, and the guard block is the only part of the prompt nobody notices missing
   until the render comes back wrong.
10. **No PDF and no page number before the human says so.** Not as a draft, not "to
    check the layout". Review runs on un-numbered PNGs.
11. **A revision round runs the same phases.** Text change → layer one → render. A
    reviewer run after rendering costs a second render.
12. **"Done" means the file the human opens has changed** — on every slide the change
    applies to, not on the one it was tested on.
