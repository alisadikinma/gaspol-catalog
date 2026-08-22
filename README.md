# gaspol-catalog

B2B sales catalog and offer-deck engine for Claude Code. The buyer is the owner or
management of an operating company, not an investor.

Pipeline: **interview → storyline → deck → gate → visual.**

Five skills:

- **`catalog-brainstorm`** — runs first, always. Interviews the human (product mode
  once per product, prospect mode once per deal), pressure-tests the pain, resolves
  the three things the plugin must never invent, and fixes the storyline spine the
  deck follows. `catalog-master` and `catalog-variant` refuse to draft without it.
- **`catalog-master`** — run once per product. Capability catalog, à-la-carte module
  menu, five-part enablement kit, one-pager, contact scripts, ROI calculator spec.
- **`catalog-variant`** — run per prospect. Qualifies the deal first, mines findings
  from the prospect's own documents, then builds the deck.
- **`catalog-gate`** — two blocking layers. Layer one reviews the text through the
  adversarial engine `gaspol-pitch` already ships, pointed at a buyer rubric instead
  of an investor one. Layer two reviews the rendered images against the deck text,
  because a deck can pass on text and fail on render the same day.
- **`catalog-visual`** — runs only after layer one passes. One 16:9 prompt per slide
  with the render guards baked in, logo and chapter rail left as paste-after-render
  slots, then hands the PNGs back for layer two. Image MCP optional — the prompts are
  the deliverable.

Requires `gaspol-pitch` for the review engine, plus 19 sales and strategy skills.
Run `bash tests/deps-present.sh` to check.

See `CLAUDE.md` for the rules and `references/b2b/` for the brain.

## Install

```bash
claude plugin marketplace add alisadikinma/gaspol-one
claude plugin install gaspol-catalog@gaspol-one
claude plugin install gaspol-pitch@gaspol-one   # required: the review engine
```

The [gaspol-one](https://github.com/alisadikinma/gaspol-one) marketplace also carries
`gaspol-dev` (execution fidelity).

MIT.
