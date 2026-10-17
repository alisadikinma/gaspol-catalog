# Tool routing: reach for the tool, do not rewrite it

Before writing a script that touches a rendered deck (PDF, numbering, watermark, footer, text fix,
logos), find the task below. Run from the plugin root with the venv python that has Pillow, numpy
and OpenCV (`~/.gaspol-video/venv/bin/python -m tools.deckkit ...`). `pptx` needs `python-pptx`,
`erase-footer` needs `tesseract` on PATH.

| I want to... | Use | Module |
|---|---|---|
| Slide spec -> prompt files + manifest | `deckkit prompts slides.json --house H` | `prompts` |
| Prompt files -> slide images (image MCP) | `deckkit gen prompts/manifest.json --ver r1` | `gen` |
| Pages folder -> PDF (one page size, optional watermark) | `deckkit pdf SRC OUT [--watermark TEXT --watermark-logo LOGO.png --grid 3x4 --corner CONFIDENTIAL --page-size WxH --skip ...]` | `pdf` |
| Public version without price pages | `deckkit pdf ... --skip 18.png 19.png` | `pdf` |
| Pages -> PPTX (16:9, clean pages) | `deckkit pptx OUT images... [--transition fade] [--jpeg-quality 92]` | `pptx` |
| Page numbers from filenames (+ wordmark) | `deckkit stamp SRC DST [--wordmark logo.png]` (never bake numbers into prompts) | `stamp` |
| Footer band: confidentiality line + logo lockup | `deckkit band SRC DST --text "..." --logos a.png b.png [--url U] [--fit-canvas WxH] [--numbers --number-fmt "{n} / {total}"]` (`--numbers` only after the human approved the renders, hard rule 4) | `band` |
| Undo a watermark baked into finals | `deckkit unmark SRC DST --watermark TEXT --corner TEXT` (same options as `pdf`, incl. `--grid`; a logo watermark is not reversible) | `watermark` |
| Remove a baked-in footer tag or page number | `deckkit erase-footer IMG NEEDLE` | `erase` |
| Real logos into blank white boxes the model left | `deckkit logo-slots IMG logos...` (left to right; `--key` white or magenta, `--mode` flat or quad) | `slots` |
| Logo onto a tilted screen or panel (magenta or white slot) | `deckkit logo-slots IMG logo.png --key magenta --mode quad` | `slots` |
| Real photo into a photo well or empty circle | `deckkit photo IMG PHOTO --box x,y,w,h [--radius R] [--circle]` | `photo` |
| Recolour the accent bars beside text points | `deckkit recolour IMG --colours "#2c5d99" "#a8712a" ...` | `recolour` |
| Comparison table page with exact numbers (drawn, not rendered) | `deckkit table spec.json out.png` | `table` |
| deck.md -> HTML review page for the human | `deckkit review DECK.md OUT.html [--title T]` | `deckmd` |
| Prompt files -> deck.md text (what the slides will say) | `deckkit deckmd PROMPTS_DIR OUT.md` | `deckmd` |
| Fix a few words in a rendered page without re-rendering | `tools/deckkit/patch.py`: `ink_bbox`, `fit`, `render_text`, `paste_text`, `blend_fill`, `glow_text`, `replace_line` (swap one line at the old cap height and ink colour; `squeeze` for tight boxes), `lerp_fill`, `erase_between`, `size_for_cap`, `baseline_for_top` | `patch` |

Rule of thumb: patch, do not re-roll. Re-rendering a page re-rolls every approved string on it.

## When no tool fits (inject back)

1. Search first: `ls tools/deckkit`, this table, `docs/deckkit.md`.
2. Close but not quite: extend the existing module (parameter), add a test.
3. Truly new and reusable: add a module under `tools/deckkit/`, register a subcommand in
   `__main__.py` if it has a CLI, test it in `tests/py/test_deckkit.py`, add a row HERE and in
   `docs/deckkit.md`.
4. Do it the same session. A script left in a client folder is a script the next deck rewrites.
5. Slide numbers, coordinates, client names and absolute paths stay in the project as arguments or
   a small plan file, never in the library. `tests/guard-generic.sh` keeps client names out of
   references and skills; keep them out of `tools/` too.
