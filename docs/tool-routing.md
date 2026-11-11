# Tool routing: reach for the tool, do not rewrite it

This table covers the whole deck pipeline (prompts -> gen -> post-render -> PDF). Before writing a
script for any of it (prompt files, renders, PDF, numbering, watermark, footer, text fix, logos),
find the task below. Run from the plugin root with the venv python that has Pillow, numpy
and OpenCV (`~/.gaspol-video/venv/bin/python -m tools.deckkit ...`). `pptx` needs `python-pptx`,
`erase-footer` needs `tesseract` on PATH.

| I want to... | Use | Module |
|---|---|---|
| Slide spec -> prompt files + manifest | `deckkit prompts slides.json --house H` (top-level `"language"` in slides.json overrides the house language for one deck) | `prompts` |
| Prompt files -> slide images (image MCP) | `deckkit gen prompts/manifest.json --ver r1` (writes `renders/r1/NN.png`; a render whose prompt changed is `stale`, never overwritten); waits on the image client's shared webhook receiver (local event files) when it runs, else polls the History API; never submits a slide twice: jobs are recorded in `.tmp/mentah/jobs.json` and a rerun collects a pending job; a second run on the same `--ver` is refused while one runs) | `gen` |
| Block a render that names a real place/object without its photo | `deckkit refgate prompts/manifest.json` (exit 1 lists slide, name, missing ref; `gen` runs it first, `--no-refgate REASON` skips; entities in `ref/real-refs.json` of the deck or any parent folder) | `refgate` |
| Pages folder -> PDF (one page size, optional watermark) | `deckkit pdf SRC OUT [--watermark TEXT --watermark-logo LOGO.png --grid 3x4 --corner CONFIDENTIAL --page-size WxH --skip ...]` | `pdf` |
| Public version without price pages | `deckkit pdf ... --skip 18.png 19.png` | `pdf` |
| PDF letter onto fewer pages (cut per line, never mid-line; one common scale <= 1) + page numbers in the footer | `deckkit repage plan.json` (`{"src","dst","pages":3,"first_top","top","bottom","keep":[["Hormat kami","Founder & CEO"]],"footer":"Halaman {n} dari {total}"}`; run before `letterhead` and `sign`) | `repage` |
| Letterhead (kop surat) onto a PDF letter exported without one (text stays selectable; content moved down, scaled only if it would not fit) | `deckkit letterhead plan.json` (`{"src","dst","pages":[1],"logo","logo_height","lines":[{"text","size","bold","colour"}],"rules":[[R,G,B],...]}`; run before `deckkit sign`; needs `pymupdf`) | `letterhead` |
| Signature and company stamp onto a PDF letter (text stays selectable; placed relative to a text anchor such as the signer's name) | `deckkit sign plan.json` (`{"src","dst","items":[{"image","anchor","dx","dy","width","opacity","page","keep_white"}]}`; white backgrounds become transparent; needs `pymupdf` in the venv) | `sign` |
| Pages -> PPTX (16:9, clean pages) | `deckkit pptx OUT images... [--transition fade] [--jpeg-quality 92]` | `pptx` |
| Pages with a footer band (not 16:9) -> PPTX without squashing | `deckkit pptx OUT images... --fit-image` | `pptx` |
| Page numbers from filenames (+ wordmark) | `deckkit stamp SRC DST --approved [--wordmark logo.png]` (never bake numbers into prompts; refuses without `--approved`, which means the human approved the renders) | `stamp` |
| Square profile logo (wide wordmark centred inside the circle the profile crops to, e.g. Google Business Profile) | `deckkit logo-square LOGO OUT [--size 720 --safe 0.8 --bg R,G,B]` | `lockup` |
| Two logos -> one "A × B" lockup (trimmed, white made transparent, equal height; for the cover slot or `band --logos`) | `deckkit lockup OUT.png logo1 logo2 [--height 300 --sep × --gap N --second-scale 0.78 --font F.ttf --trim-out DIR]` (`--trim-out` saves the trimmed single logos for `band --logos`) | `lockup` |
| Footer band: confidentiality line + logo lockup (or a product caption: `--sub` description line, `--band-frac 0.095`, `--secondary-frac 0.6` for an equal lockup) | `deckkit band SRC DST --text "..." --logos a.png b.png [--prefix slide- --url U --url-colour R,G,B] (SRC = a folder, or a map.json of page -> render) [--fit-canvas WxH] [--numbers --approved --number-fmt "{n} / {total}"]` (`--numbers` refuses without `--approved`: only after the human approved the renders, hard rule 4) | `band` |
| Undo a watermark baked into finals | `deckkit unmark SRC DST --watermark TEXT --corner TEXT` (same options as `pdf`, incl. `--grid`; a logo watermark is not reversible) | `watermark` |
| Remove a baked-in footer tag or page number | `deckkit erase-footer IMG NEEDLE` | `erase` |
| Real logos into blank white boxes the model left | `deckkit logo-slots IMG logos...` (left to right; `--key` white or magenta, `--mode` flat, quad or pixel; `--min-area 0.002` for small card-header slots, default 0.01 of the page; `--pad 12` covers a soft pink glow around the slot; `--fit 0.95 0.95` for bigger logos, default 0.78 0.7 of the slot) | `slots` |
| Everything pasted into magenta slots after render, per page plan: logos flat / perspective / per-pixel, round photos, sticker badges, flags, cards, text, stars, slanted truck-side logos | `deckkit compose plan.json [--only key]` (`{"pages": [{"src","dst","expect_slots","ops":[...]}]}`; slot selectors by x/y/area + where/from/to; leftover magenta counted) | `compose` |
| Logo onto vehicle sides or panels the render drew with no slot (hand-measured quads) | `deckkit logo-quads spec.json` (`{"src","dst","logo","plate","fit","quads":[[TL,TR,BR,BL],...]}`) | `slots` |
| Logo onto a tilted screen or panel (magenta or white slot) | `deckkit logo-slots IMG logo.png --key magenta --mode quad` | `slots` |
| Logo onto a magenta slot with an object drawn in front of it (hand, device edge) | `deckkit logo-slots IMG logo.png --key magenta --mode pixel` (pastes only where the slot was magenta) | `slots` |
| App screenshot onto a magenta phone screen with rounded corners, a notch, or an object in front of it | `deckkit logo-quads spec.json` with `"mode": "pixel", "trim": false, "fit": 1.0, "plate": null` and a hand-measured quad; render the screenshot at the quad's aspect | `slots` |
| Paste a product, device or sign plate onto a rendered page in perspective, with a contact shadow (or clone a figure already on the page) | `deckkit vidkit paste PAGE OBJECT.png OUT --box x,y,width` or `--quad x,y;x,y;x,y;x,y` `[--shadow 0.45 --blur 1.5 --whole --from-box x0,y0,x1,y1]` (runs gaspol-video's `vidkit paste`, not a copy) | `vidbridge` |
| Erase an object or a stray part from a rendered page (fill from the clean rows above) | `deckkit vidkit erase ...` (see `deckkit vidkit erase --help`) | `vidbridge` |
| Move a background colour family of a render or photo to the brand colour (royal blue -> navy) | `deckkit vidkit retint IN OUT --to "#071A33" [--hue 200-260 --min-sat 0.30 --strength 1.0 --preview p.jpg]` | `vidbridge` |
| Remove a thin line (crack, wire, scratch) from a photo along a traced path | `deckkit vidkit inpaint IMG OUT --path "x,y;x,y;..." [--width 24]` | `vidbridge` |
| Real photo into a photo well or empty circle | `deckkit photo IMG PHOTO --box x,y,w,h [--radius R] [--circle]` | `photo` |
| Recolour the accent bars beside text points | `deckkit recolour IMG --colours "#2c5d99" "#a8712a" ...` | `recolour` |
| Comparison table page with exact numbers (drawn, not rendered) | `deckkit table spec.json out.png` | `table` |
| deck.md -> HTML review page for the human | `deckkit review DECK.md OUT.html [--title T]` | `deckmd` |
| Prompt files -> deck.md text (what the slides will say) | `deckkit deckmd PROMPTS_DIR OUT.md` | `deckmd` |
| Retype text paragraphs in rendered pages from a spec file (project keeps only the JSON) | `deckkit retype fixes.json` (`{"font", "fixes": [{"src", "dst", "box", "lines", "note", ...replace_block options}]}`; `"erase": "flat"` or `"bg_from": X` wipes a box that touches letters without pulling their colour in; `"add": {"size", "fill"}` writes new lines into an empty box; checks every fix before writing any) | `patch` |
| Move or delete a word in a rendered title (doubled word, stray dot) by reusing the real ink, no stand-in font | `deckkit reflow plan.json` (`{"fixes":[{"src","dst","ops":[{"op":"words","line":[y0,y1,x0,x1]},{"op":"move","line":[...],"word":2,"to":[x,y]},{"op":"clear","box":[...]}]}]}`; `words` prints the x range of each word first). Library: `patch.line_words`, `patch.move_ink` (`dark=False` for light ink) | `patch` |
| Fix a few words in a rendered page without re-rendering | `tools/deckkit/patch.py`: `ink_bbox`, `fit`, `render_text`, `paste_text`, `blend_fill`, `glow_text`, `emblem_text` (round glowing-lettering emblem, optional ring), `fill_from_side` (repeat the edge line beside a box across it), `replace_block` (swap a paragraph with a different number of lines; light-on-dark with `dark=False`), `replace_line` (swap one line at the old cap height and ink colour; `squeeze` for tight boxes), `lerp_fill`, `erase_between`, `size_for_cap`, `baseline_for_top` | `patch` |
| HTML page -> PNG at an exact size (headless Chrome) | `deckkit shot page.html out.png --size 2752x1536` | `chrome` |
| JD data -> one-page "How I'd build your system" PDF | `deckkit jdpage data.json out.pdf` | `jdpage` |
| Area deck -> job deck PDF (cover + CTA text swapped, other slides untouched) | `deckkit jobdeck DECK.html SLOTS.json OUT.pdf` | `jobdeck` |
| Small pill label or flag drawn in code (no image model) | `tools/deckkit/chips.py`: `pill`, `flag` | `chips` |

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
