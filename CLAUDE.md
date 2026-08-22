# gaspol-catalog — plugin rules (for Claude)

This plugin orchestrates **B2B sales** catalog and offer-deck creation. The buyer is
the owner or management of an operating company — someone who buys a change in
working days, not a share of a market. Read this before touching any skill.

Sibling plugin `gaspol-catalog` is NOT: `gaspol-pitch` sells to investors and keeps
its own rubric. The two share one review engine and nothing else.

## Core principle — reuse, don't recreate (ponytail)

Every skill here is **THIN**. It routes to already-installed sales and strategy
skills for methodology and adds only orchestration glue plus the rubric. The review
engine itself is **not copied** from `gaspol-pitch` — `pitch-review` accepts a
caller-supplied rubric path, and this plugin hands it the B2B rubric. Domain
knowledge lives in `references/b2b/`, **never hardcoded in skill prose**.

## Reuse map — which installed skill each phase calls

| Skill | Reuses (installed skills) | Bundled references it reads |
|---|---|---|
| `catalog-master` | positioning, pricing-strategy, monetizing-innovation, sales-narrative, crossing-the-chasm, 100m-offers | `b2b-deck-architecture.md`, `b2b-honesty-rails.md`, `enablement-kit.md`, `b2b-phased-sale.md` |
| `catalog-variant` | spin-selling, challenger-sale, meddic-scorecard, made-to-stick, storybrand | `b2b-deck-architecture.md`, `b2b-honesty-rails.md` |
| `catalog-gate` | `pitch-review` (gaspol-pitch), with `rubric` pointed here | `b2b-deck-rubric.md`, `b2b-buyer-rubric.md`, `b2b-visual-contract.md`, `b2b-honesty-rails.md` |

If a **required** installed skill above is missing at runtime, STOP and tell the
user — do NOT stub it or fabricate a replacement. Run
`bash tests/deps-present.sh` to see exactly which one.

**Optional dependencies (graceful degrade, never hard-stop):**
- `gaspol-design` (palette/font/chart) — if absent, fall back to the theming canon
  in `b2b-visual-contract.md`, which is self-sufficient.
- Image MCP — if absent, emit the render prompts and report the render layer as
  `NOT RUN`. Never report it as PASS.

## references/b2b index (the brain — GENERIC only)

- `b2b-deck-rubric.md` — binary linter, 9 pass/fail checks per slide.
- `b2b-buyer-rubric.md` — scored buyer dimensions + ABC dual-test + four buyer
  conviction layers + cross-slide consistency + narrative gates.
- `b2b-deck-architecture.md` — the eight-act spine and the rules for each act.
- `b2b-honesty-rails.md` — honesty rails, urgency-kit validity, price anchoring,
  modular menu rules.
- `b2b-visual-contract.md` — no faces, 60/40 visual contract, chapter rail, render
  guards against duplicated text and fabricated numbers.
- `b2b-phased-sale.md` — Survey → single-site pilot → rollout, client-signed
  acceptance criteria, consortium SLA shape.
- `enablement-kit.md` — the five-part sales kit skeleton.
- `examples/good-catalog.md` / `examples/bad-catalog.md` — self-test fixtures
  (PASS / BLOCKING).

`research/buyer-brain.md` is NOT part of `references/` on purpose: it names real
sources and is the input that grounds the rubric, not generic canon.

## Hard rules (gotchas)

1. **Never skip `catalog-gate`.** Nothing reaches a prospect without a PASS verdict.
   The gate has two layers and both block. A deck can PASS on text and BLOCK on
   render the same day — the defect is born in the render prompt, not in `deck.md`.
2. **Bundle only generic knowledge.** Single-company, single-city, single-event, and
   single-identity knowledge is a **runtime input**, never committed to
   `references/`. CI guard: `bash tests/guard-generic.sh` must exit 0. Note the
   guard also rejects target-city names — a rubric that names a city has stopped
   being a rubric.
3. **Brand chrome is a runtime input.** Logo, palette, font, handle — leave a
   placeholder. The client's logo is never drawn by an image model; leave the slot
   empty in the prompt and paste the file after rendering.
4. **Render policy = full-slide image + QA safety net.** Bake the exact headline and
   numbers into each prompt verbatim; if rendered, run the render layer of
   `catalog-gate` and regenerate on defect.
5. **Image MCP is optional.** Always emit the prompts; PNG generation is a separable
   step. No MCP is a manual-run note, not a failure.
6. **SKILL.md frontmatter = `name` + `description` only.** No other YAML keys.
   Enforced by `bash tests/frontmatter.sh`.
7. **Three things this plugin must never invent** — it STOPS and asks instead:
   module list and prices; a prospect's fleet size or operating numbers; whether the
   product supports multiple tenants in one deployment. Fabricating any of the three
   breaks the honesty rails the whole rubric rests on.

## Skill format

`skills/<name>/SKILL.md`: a `---` fenced YAML frontmatter (`name`, `description`)
then a markdown body. Description should carry the trigger phrases that route to
the skill.

## Tests

`bash tests/run-all.sh` runs every gate. Scripts skipped with `SKIP` have not been
written yet; a skipped script is never a pass.

| Script | Enforces |
|---|---|
| `deps-present.sh` | 19 prerequisite skills resolve |
| `research-contract.sh` | buyer research has its six sections and every claim is traceable |
| `guard-generic.sh` | hard rule 2 |
| `frontmatter.sh` | hard rule 6 |
| `refs-present.sh` | the seven reference files exist and are not stubs |
| `fixture-shape.sh` | the planted defects in the bad fixture are still there |

The fixture verdict itself — bad BLOCKS, good PASSES — cannot be checked by a
script. It is run by an agent, and `references/b2b/examples/` plus the self-test
section of `catalog-gate` define the contract.

## gaspol Ticket Counter

Prefix: CAT
Last ticket: CAT-1
