---
name: catalog-finish
description: Final phase of gaspol-catalog, run only once catalog-gate has PASSED. Use to package the sendable deliverable and capture what was learned — kirim penawaran, bundel deck final, tutup deal, catat hasil penawaran, simpan pelajaran ke knowledge base. Gates on both review layers, bundles the deck with its prompts, images, and review, then writes the reusable pattern back to the same knowledge base catalog-brainstorm read from, so the next deal asks fewer questions than this one. Leaves the deal outcome as an open question rather than inventing one.
---

# catalog-finish

> The exit gate, and the half of the loop that makes the plugin worth reusing.
> A pipeline that only reads a knowledge base never gets faster. This is where it
> gives something back.

**Announce:** "Running catalog-finish — gating on both review layers, bundling, then capturing what was learned."

## HARD GATE — both layers

Refuse to finish unless `review.md` shows:

- **Layer one (text) = PASS.** BLOCKING routes back to `catalog-variant` or
  `catalog-master` with the fix list.
- **Layer two (render) = PASS**, if images exist. A render defect routes back to
  `catalog-visual` to fix the **prompt**, not to `deck.md`.

If no images were produced, layer two reads `NOT RUN`. That deck may still ship as
text plus prompts — **and the bundle says so in writing.** "Rendered manually, render
layer not run" is an honest handover. Reporting it as passed is the exact failure the
two-layer design exists to prevent, and it is worse here than anywhere else in the
pipeline because this is the last checkpoint before a prospect sees it.

## Two modes, matching the rest of the plugin

| Mode | Finishes | Bundles |
|---|---|---|
| **product** | a master catalog run | the full enablement kit |
| **prospect** | one named deal | the deck for that company |

## Step 1 — optional polish pass

Three reviewer subagents in parallel over the deck, one lens each, and fold their
fixes:

- **Copy** — headlines are assertions not labels, numbers formatted consistently,
  buyer vocabulary held, zero vendor fluff.
- **Layout** — the 60/40 contract holds, type scale consistent, chapter rail present
  only where the architecture says it should be.
- **Commercial** — the module menu still contains the line that cannot be removed,
  anchor arithmetic still reconciles, the out-of-scope line still says what it said.

This is a **polish, not a gate** — skip it on a fast finish. It never overrides a
verdict and it never re-opens a number the human confirmed.

## Step 2 — bundle

**Product mode:**

```
catalog/            master-catalog.md · module-menu.md · one-pager.md
                    talk-tracks.md · system-instructions.md
                    roi-calculator-spec.md · feedback-log.md
prompts/            slide-NN.md (+ slide-NN.png if rendered)
review.md           both layers, verdict visible
brief.md            the confirmed answer sheet, provenance intact
storyline.md
```

**Prospect mode:** the same shape under `prospects/<slug>/`, plus
`qualification.md` and `findings.md`.

Keep `brief.md` in the bundle. It is the only record of **which answers came from a
note and which a human confirmed**, and six months from now that distinction is the
difference between a fact and a guess someone once agreed to on a Friday.

## Step 3 — final checklist

- [ ] layer one = PASS
- [ ] layer two = PASS, or `NOT RUN` **stated in the bundle**
- [ ] every slide has a `prompts/slide-NN.md`
- [ ] cover carries duration and deadline, no price
- [ ] every urgency device still genuinely applies **on the actual send date** — a
      countdown is tied to when it is sent, so a bundle finished Monday and sent
      Thursday has a wrong deadline unless the CTA slide is regenerated
- [ ] client logo pasted, not generated; chapter rail pasted, not generated
- [ ] no reference customer's operational identity present beyond what the written
      permission allows
- [ ] brand chrome is a runtime placeholder in `prompts/`, not a baked brand

## Step 4 — capture, back into the same knowledge base

Resolve the knowledge base **exactly as `catalog-brainstorm` Step 0 does** — the same
resolution order, the same rule that the address is a runtime input and never
committed. Do not invent a location, and do not write anywhere the environment's own
convention does not point.

**Ask before writing.** Then capture, in decreasing order of value:

1. **Corrections that surfaced** — a price that had moved, a permission that had
   narrowed, a maturity claim that turned out thinner than the note said. These
   **overwrite** the note they correct. Two contradicting prices in one knowledge base
   is worse than no price at all, and appending the new one beside the old one is how
   that happens.
2. **What the gate caught** — the defects that blocked this deck. A defect that blocks
   twice is a rubric gap or a habit, and it is invisible unless someone writes it
   down.
3. **What the buyer actually said** — the objection that came up in the room, in their
   words. This is the highest-value line in the whole capture: it feeds
   `## Keberatan` in the buyer research, which feeds the skeptic in `catalog-gate`,
   which is what blocks the next weak deck. Quote it; do not paraphrase it into vendor
   language.
4. **What shipped** — which storyline, which module configuration, which price, to
   which kind of operation. Enough that the next similar prospect starts from a
   pattern instead of a blank interview.
5. **One high-signal line** to wherever the environment keeps its running log, if it
   keeps one.

If no knowledge base exists, offer to start one and accept "no" without arguing.

## Step 5 — the outcome is not known yet, and is not invented

A deck ships before it wins or loses. **Do not record an outcome at ship time.**

Write the capture with the outcome left as an explicit open question — won / lost /
no decision, and the reason — and tell the user in one line that returning to fill it
in is what makes the pattern worth anything. An outcome guessed at ship time
contaminates every future run that reads it, and unlike a stale price nobody ever
discovers it is wrong.

## Reuse (optional — degrade, never hard-stop)

| Skill | For | If absent |
|---|---|---|
| a notes/knowledge MCP | writing the capture back | write the capture to a local file in the working directory and tell the user where it is |
| `gaspol-knowledge` | cross-project pattern KB | skip the KB write and say so in one line |

Never skip the capture **silently**. A capture that quietly did not happen looks
identical to one that did, right up until the next run asks the same questions again.

## Output

The finished bundle, plus a capture entry in the user's own knowledge base with the
outcome still open.

## Hard rules

1. Both layers gate. `NOT RUN` is disclosed in the bundle, never upgraded to PASS.
2. Ask before writing anything back, and write only where the environment points.
3. A correction overwrites the note it corrects.
4. The deal outcome is never invented, and never recorded at ship time.
5. No address is committed — not a path, vault name, project name, or company name.
   Enforced by `bash tests/guard-generic.sh`.
6. The reference customer's disclosure permission travels with the bundle. What may be
   said publicly is a fact with an owner and an expiry, not a property of the deck.
