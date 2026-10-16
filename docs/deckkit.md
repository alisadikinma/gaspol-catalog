# deckkit: post-render deck library

Distilled from the deck folders of finished catalogs and pitch decks. Run
`~/.gaspol-video/venv/bin/python -m tools.deckkit --help` from the plugin root, or import
`from tools.deckkit import pdf, watermark, stamp, band, patch, slots, erase`. Routing table:
`docs/tool-routing.md`.

| Module | What |
|---|---|
| `watermark` | `mark` / `unmark`: tiled diagonal watermark and corner mark, REVERSIBLE (alpha composite is inverted per pixel). Ink white on dark pages, charcoal on light, sampled from the page. |
| `pdf` | `list_pages`, `build_pdf`: one page size, optional watermark, skip list. Pillow's own writer, no img2pdf. |
| `pptx` | `build_pptx`: one full-bleed picture per 16:9 slide. |
| `stamp` | `stamp_dir`: numeral from the filename, footer colour sampled, optional white wordmark. |
| `band` | `add_band`: footer band with a text line and a logo lockup. |
| `patch` | `ink_bbox`, `fit` (size by cap height, tracking by width), `render_text`, `paste_text`, `blend_fill` (Laplace inpaint), `glow_text`. |
| `erase` | `erase_footer`: OCR (tesseract) + OpenCV inpaint of a baked-in footer tag. |
| `slots` | `find_white_slots`, `fill_slots`: paste real logos into blank white boxes. |

## Not folded in

Per-slide fixes that hard-code coordinates (recolour one bar set, redraw one timeline, remove one
flag, rebuild one slide from panels) and prompt builders tied to one deck. The reusable parts of
them are `patch` and `blend_fill`. Image generation stays in `catalog-visual`.

Tests: `tests/py/test_deckkit.py` (run with the venv python; skips without Pillow/numpy).
