**Ticket:** CAT-2

# deckkit full pipeline + house style reference

## Design

### Problem

Every new deck re-writes the same Python: a prompt builder (three copies), an image
render runner (two copies), and a dozen post-render fixes. The style the seller wants is
re-explained per deck in `brand.md`. An inventory of 46 deck scripts across three client
folders found: 13 already covered by `tools/deckkit/` (v0.8.0), 10 that need a parameter on
an existing module, 11 that warrant a new module, 12 client-specific one-offs.

Two goals, one ticket (same subsystem):

1. `deckkit` covers the whole deck pipeline — prompt files, image generation, post-render,
   PDF — with one tool per job and a registry that maps job to tool.
2. The Ekaputra deck style becomes the default reference for future decks, so the user
   does not re-explain it.

### Approved decisions

- Style reference: the Ekaputra deck (bright isometric). The MONI style is not kept as a preset.
- Split: the generic style lives in the plugin; the seller's identity (INDUSIA) lives outside
  the plugin in a house-standard file. Hard rule 2 and `guard-generic.sh` stay intact.
- Scope: stages 1 (prompt files), 2 (image generation) and 3 (post-render) all go into deckkit.
- One-off scripts stay in client folders. Video scripts stay with `vidkit` (gaspol-video).

### Part 1 — deckkit modules

New modules (each a CLI subcommand in `__main__.py` where it has one):

| Module | Job | Replaces |
|---|---|---|
| `prompts.py` | Slide spec (layout, visual, `(role, text)` list, refs) + style preset + guard → `prompts/slide-NN.md` + `manifest.json`. Refuses duplicate band/footer sentences across slides. | EKA `make_prompts.py`, SPS `make_prompts.py`, C3 `gen_prompts.py` |
| `gen.py` | `manifest.json` → images via the image client. Slide filter, N parallel workers, retries, raw output kept, versioned output name (`NN-<ver>.png`). Model, mode, client path come from house standard / env, never hardcoded. | EKA `render.py`, SPS `render.py` |
| `photo.py` | Cover-crop a photo into a box with radius, or into a circle. | `swap_photos`, `tempel_16`, photo parts of `finalize`/`tambal`/`tempel_25` |
| `recolour.py` | Find vertical accent bars in a column, recolour top-to-bottom to a palette. | `warna_bar.py` |
| `table.py` | Comparison-table page drawn in PIL with exact numbers, wrap and font-size search. | `tabel_25.py` |
| `deckmd.py` | `deck.md` → HTML review page; prompt files → `deck.md`. | `buat_review.py`, `build_deck_md.py` |
| `chrome.py` | HTML → PNG at an exact size, HTML → PDF, headless Chrome. Chrome path resolved, not hardcoded. | `shot.sh`, Chrome call in BRD build |
| `chips.py` | Small pill label and flag drawn in PIL. | pill/flag code in 4 scripts |

Extensions to existing modules (a parameter, not a new tool):

| Module | Add | From |
|---|---|---|
| `slots.py` | `find_slots(key="white"|"magenta")` returning quads; `mode=flat|quad|pixel`; `paste_quad()` perspective paste | SPS `tempel_sps`, `tempel_25` |
| `patch.py` | `replace_line()`, `lerp_fill()`, `emblem_text()`, `size_for_cap`, `baseline_for_top`, `erase_between`, `fill_from_side` | EKA `tambal_teks`, C3 `finalize`, CAT `revisi`, MONI `patch` |
| `watermark.py` | `logo=` (image tile), `grid=(cols, rows)` | EKA `pdf.py`, MONI `build_pdf` |
| `band.py` | `url=`, `number_fmt` (`{n} / {total}`), background colour, `fit_canvas=(W,H)` | SPS `band`, `buat_pdf`, EKA `finish` |
| `pptx.py` | `transition="fade"`, `jpeg_quality` | C3 `build_pptx` |

Registry and uniqueness:

- `docs/tool-routing.md` is the registry: "I want to… → use". `docs/deckkit.md` holds details.
- New test: one job = one routing row. Every deckkit module with a public job has at least one
  row (a module may serve several distinct jobs, e.g. `pdf` for the full and the public
  version), every row points to an existing module/subcommand, and no two rows name the same
  job. A tool without a row, a row without a tool, or a job listed twice fails the test. This
  is the anti-duplicate guard.
- `tests/guard-generic.sh` extends to scan `tools/` for client names and absolute home paths.

### Part 2 — style reference

**A. Generic preset, in the plugin:** `references/b2b/styles/isometrik-terang.md`

- Palette: background `#f3f6f5`, headline navy `#15212b`, accent teal `#23857f`, problem
  slides burnt orange `#b8561a`, steel blue `#2c5d99`, amber `#a8712a`, body grey `#44545e`;
  price/closing background `#e6eeee`; proof slide dark navy.
- Illustration: clean isometric 3D, soft matte clay, soft shadows.
- Type: bold condensed sans headline (Oswald-like), clean sans body.
- Layout grammar: eyebrow above headline (teal for solution, burnt orange for problem);
  illustration left ~62%, right text column with 3–4 points each with a coloured left bar;
  variants three columns, 2×2 rule cards, ascending steps, pale banner with thick left bar;
  cover text left 40% / illustration right 60% with tricolour top stripe; grey footer line
  bottom-left for source/ILUSTRASI.
- STYLE block from the Ekaputra builder; GUARD block from the SPS builder (the newest deck in
  the same style, a superset of Ekaputra's: adds magenta paste slots, blank documents, no
  ghosted objects, empty bottom 3%). Seller name replaced by `{seller}`.
- Machine-readable fenced ```json block that `prompts.py` loads (stdlib `json`; the venv has
  no PyYAML).
- `refs-present.sh` adds the file to its list.

**B. Seller identity, outside the plugin:**
`/Users/alisadikin/Drive-D/pitch-deck/ref/house-standard.md` (never committed to the plugin)

- Seller name, logo paths, watermark text, footer band format
  ("RAHASIA · hanya untuk <klien>" + client logo × seller logo), site, WhatsApp number,
  preset = `isometrik-terang`, default image model and mode, image client location, style
  reference images.
- Resolution order (deckkit and skills alike): `--house PATH` / a path named in session →
  `$GASPOL_CATALOG_HOUSE` → a `house-standard: <path>` line in the nearest ancestor
  `.gaspol/context-sources.md` → none. `/Users/alisadikin/Drive-D/pitch-deck/.gaspol/context-sources.md`
  carries that line for this machine.
- `catalog-brainstorm` brand intake pre-fills `brand.md` from it and asks only client-specific
  items (client logo, client name, client colours if any). `catalog-visual` reads the preset
  through `brand.md`.

### Data integration map

| Component | Data source | Existing? | Notes |
|---|---|---|---|
| `prompts.py` | per-deck slide spec (project file) + preset + house standard | preset new | spec stays in the project |
| `gen.py` | `manifest.json` + image client from house standard/env | client exists outside plugin | no MCP → prompts still produced, report `NOT RUN` |
| post-render modules | PNGs in project | yes | unchanged CLI for existing commands |
| `catalog-brainstorm` | house-standard.md | new file | soft: missing file → ask everything as today |

### Error handling

- Missing house standard: not a failure; fall back to today's behaviour and say so.
- `gen.py` without an image client: exit non-zero with a clear message; prompts are still the deliverable.
- `recolour` / `slots` find a different count than expected: refuse and print found vs expected
  (never paint the wrong element).
- `prompts.py` duplicate band sentence: refuse with the two slide numbers.

### Testing

- Unit tests in `tests/py/test_deckkit.py` per new module and per new parameter, on small
  synthetic images (no client assets).
- Routing-registry test (above). `guard-generic.sh` over `tools/`.
- `bash tests/run-all.sh` green.
- One real check: rebuild one Ekaputra slide prompt with `deckkit prompts` from a spec and
  diff against the existing `prompts/slide-02.md` — block order and the TEXT block format
  must match. The STYLE block is the generic form of Ekaputra's: the deck-specific cold-chain
  mapping (frozen/chilled/dry) is dropped, and two sentences fix the reference-image order
  (first = seller wordmark, second = style source).

### Out of scope

- The 12 one-off scripts (e.g. `susun_19`, `badge`, `unflag_arc1`, `stamp_office`).
- Video scripts (vidkit).
- MONI style preset.
- Deleting or rewriting scripts in client folders.
