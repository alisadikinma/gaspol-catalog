# deckkit: the offer-deck library

One library for the whole deck pipeline: slide spec -> prompt files -> images ->
post-render fixes -> PDF. Distilled from the deck folders of finished catalogs and pitch
decks. Run
`~/.gaspol-video/venv/bin/python -m tools.deckkit --help` from the plugin root, or import
`from tools.deckkit import pdf, watermark, stamp, band, patch, slots, erase`. Routing table:
`docs/tool-routing.md`.

| Module | What |
|---|---|
| `house` | `resolve`, `load`, `load_preset`: the seller house standard (outside the plugin, found by `--house`, `$GASPOL_CATALOG_HOUSE`, or a `house-standard:` line in `.gaspol/context-sources.md`) and the style presets in `references/b2b/styles/`. Library only. |
| `prompts` | `deckkit prompts slides.json --house H`: `slides.json` + preset + house standard -> `prompts/slide-NN.md` with the full guard block, and `prompts/manifest.json` (house `style_refs` first, then slide refs). |
| `gen` | `deckkit gen prompts/manifest.json --ver rN`: render every manifest slide from its prompt file through the image client named by the house standard (`image_client`) or `$DECKKIT_IMAGE_CLIENT`. If the client cannot be imported here and it has its own `.venv/bin/python`, `gen` re-runs itself once with that interpreter. Never overwrites an existing render. Optional; no client means the prompts are the deliverable. |
| `watermark` | `mark` / `unmark`: tiled diagonal text watermark (or `grid=(cols, rows)` cell-centred text) and corner mark, REVERSIBLE (alpha composite is inverted per pixel). `logo=PATH` tiles a logo at 12% in the page ink instead; logo mode is NOT reversible (`unmark` raises ValueError). Ink white on dark pages, charcoal on light, sampled from the page. |
| `pdf` | `list_pages`, `build_pdf`: one page size, optional watermark, skip list. Pillow's own writer, no img2pdf. |
| `pptx` | `build_pptx`: one full-bleed picture per 16:9 slide; optional `transition="fade"`, `jpeg_quality`. |
| `stamp` | `stamp_dir`: numeral from the filename, footer colour sampled, optional white wordmark. |
| `band` | `add_band`: footer band with a text line and a logo lockup; optional `url`, `fit_canvas` letterbox, and `number`/`total` (only after approval). |
| `patch` | `ink_bbox`, `fit` (size by cap height, tracking by width), `render_text`, `paste_text`, `blend_fill` (Laplace inpaint), `glow_text`, `emblem_text` (round glowing-lettering emblem, optional ring), `fill_from_side` (repeat the edge line beside a box across it), `replace_line` (swap one text line: erase, cap height and ink colour taken from the old ink, `squeeze=True` tracks down to -0.04 em), `lerp_fill`, `erase_between`, `size_for_cap`, `baseline_for_top`. |
| `erase` | `erase_footer`: OCR (tesseract) + OpenCV inpaint of a baked-in footer tag. |
| `slots` | `find_white_slots`, `find_slots` (white or magenta, quads), `paste_quad` (perspective paste), `fill_slots` (`key`, `mode` flat, quad or pixel; pixel pastes only where the magenta slot was visible, magenta only): paste real logos into blank white or magenta slots. |
| `photo` | `cover`, `place`, `circle`: cover-crop a real photo into a rounded box or circle. |
| `recolour` | `bars`: find thin vertical accent bars right of `x_from`, recolour top to bottom; antialiasing kept. Count mismatch raises. |
| `table` | `render(spec, size, font_path)`: comparison page drawn with PIL (title, header, rows, optional `good`/`bad` cell marks as soft green / red tints). Font size searched per page; a cell that fits at no size raises `ValueError("cell r,c does not fit")`. Bottom band left empty. |
| `deckmd` | `review_html(md_text, title)`: standalone phone-readable HTML, one card per `#`/`##` section, all text escaped. `from_prompts(dir)`: `## Slide NN` sections (numeric order) with the quoted TEXT lines of each `slide-NN.md` as `- role: text` bullets; skips other files and `_rejected/`; no slide file raises `ValueError("no slide-NN.md in <dir>")`. |
| `chrome` | `find_chrome` ($CHROME_BIN, PATH names, macOS app), `shot` (HTML -> PNG at an exact size, crops extra pixels, raises if smaller), `print_pdf`. Temp profile, 120 s timeout. CLI `shot`. |
| `chips` | `pill` (RGBA label with rounded ends), `flag` (equal stripes, `h` or `v`). Library only, no CLI. |

## Not folded in

Per-slide fixes that hard-code coordinates (recolour one bar set, redraw one timeline, remove one
flag, rebuild one slide from panels) and prompt builders tied to one deck. The reusable parts of
them are `patch` and `blend_fill`.

Tests: `tests/py/test_deckkit.py` (run with the venv python; skips without Pillow/numpy).
