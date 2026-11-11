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
| `prompts` | `deckkit prompts slides.json --house H`: `slides.json` + preset + house standard -> `prompts/slide-NN.md` with the full guard block and a trailing `REVISION LOG` (old lines kept, slide `log` appended). Warns on a slide over the preset `text_budget` (isometrik-terang: headline 18 words, other lines 16), and refuses it when `slides.json` sets `"strict_budget": true`, unless the slide sets `dense` to the reason; and `prompts/manifest.json` (`prompt_file` relative to the manifest, a `sha` per slide; house `style_refs` first, relative ones resolved against the house file, then slide refs). |
| `gen` | `deckkit gen prompts/manifest.json --ver rN`: render every manifest slide (to `renders/rN/NN.png`, or `renders/slide-NN.png` without `--ver`; a `.sha` sidecar records the prompt it came from, and a prompt file edited since reports `stale`; the `REVISION LOG` is never sent to the model) from its prompt file through the image client named by the house standard (`image_client`) or `$DECKKIT_IMAGE_CLIENT`. If the client cannot be imported here and it has its own `.venv/bin/python`, `gen` re-runs itself once with that interpreter. Never overwrites an existing render. Never submits a slide twice (2026-10-31, ~94 paid jobs for 13 slides): a job's uuid goes to `<raw>/jobs.json` keyed by version, slide and prompt sha, and any later attempt or rerun collects it with the client's `fetch_image` instead of submitting; an unknown submit outcome is not retried; a job the server marked failed (History status 3) reports `FAIL ... failed on the server`, its record is cleared, and the next run submits a fresh job (2026-11-05: such jobs used to report PENDING forever); `<out>/<ver>/.gen.lock` refuses a second run on the same version. Waiting: snapgen sends webhooks only to the one URL registered in its Service Integration settings (no per-request field). One always-on receiver in the image client (`python -m scripts.webhook_events`, behind a named tunnel at that URL) writes every event to a local file; gen submits without waiting and waits on that file (15 min cap, then one History check), and the client's `poll()` does the same for every MCP tool. No live receiver, or `--no-webhook`, and gen polls the History API. Optional; no client means the prompts are the deliverable. |
| `watermark` | `mark` / `unmark`: tiled diagonal text watermark (or `grid=(cols, rows)` cell-centred text) and corner mark, REVERSIBLE (alpha composite is inverted per pixel). `logo=PATH` tiles a logo at 12% in the page ink instead; logo mode is NOT reversible (`unmark` raises ValueError). Ink white on dark pages, charcoal on light, sampled from the page. |
| `pdf` | `list_pages`, `build_pdf`: one page size, optional watermark, skip list. CLI `--opacity PCT` (1-100) sets the watermark tile opacity, e.g. `--watermark INDUSIA.ai --opacity 12`. Pillow's own writer, no img2pdf. |
| `pptx` | `build_pptx`: one full-bleed picture per 16:9 slide; optional `transition="fade"`, `jpeg_quality`, `fit_image` (slide height from the pages' aspect, for pages with a footer band; mixed aspects raise). |
| `stamp` | `stamp_dir`: numeral from the filename, footer colour sampled, optional white wordmark. CLI needs `--approved`. |
| `band` | `add_band`: footer band with a text line and a logo lockup; optional `url`, `fit_canvas` letterbox, and `number`/`total` (only after approval; CLI `--numbers` needs `--approved`). |
| `compose` | `deckkit compose plan.json`: find the magenta slots the prompt asked for, check their count, run the plan's ops (`logo` flat/quad/pixel, `photo`, `image`, `logo_box`, `flag`, `card`, `text`, `stars`, `whiten`, `logo_slanted`), paint leftover magenta and report it. `whiten` takes `box`, `pinkish` and `dark_fringe` (true: also the dark purple edge magenta leaves on a dark phone bezel; give it a `box`). Slot grounds are sampled before any op, so neighbouring logos never bleed into each other's fill. |
| `logo-quads` | `deckkit logo-quads spec.json`: paste one logo onto hand-measured quads (truck sides, bus body) when the render has no slot; optional flat `plate` behind it; `multiply` + `shade` make it read as a real sticker (body texture, light and shadow carry over); a quad may be `{"quad": [...], ...options}` to override per panel; all quads checked before pasting. `"mode": "pixel"` paints only the magenta pixels (rounded screen corners, notch, an object in front stay) and `"trim": false` keeps an app screenshot's light margins. |
| `retype` | `deckkit retype fixes.json`: apply `replace_block` fixes listed in a JSON file (paths relative to it); validates all fixes first, writes nothing on error; a fix whose `src` is an earlier `dst` chains on that result, so several fixes on one page run in order; `"erase": true` (no `lines`) wipes a box, e.g. a stray wordmark.  `"erase": "flat"` or `"bg_from": X` (sample column) paints the box with that column's background per row, no blend: use it when the box touches letters (the default blend pulls their colour in as a stain). `bg_from` also works in `replace_block`. |
| `reflow` | `deckkit reflow plan.json`: move or delete words of rendered text by reusing the real ink (a model prints a doubled word or stray dot; a stand-in font looks different). Plan `{"fixes":[{"src","dst","ops":[...]}]}`, ops run in order, all fixes checked before any write. Ops: `words` (`line:[y0,y1,x0,x1]`, optional `thr`, `gap`, `dark`; prints the `[xa, xb]` of each word), `move` (`box` or `line`+`word` index, `to:[x,y]` = new top-left, options `clear`, `ink_sum`, `dark`, `bg_x`), `clear` (`box`, `bg_x`). Library: `patch.line_words` (columns darker than `thr`, split by blank runs > `gap`), `patch.move_ink` (copies only pixels with r+g+b < `ink_sum`; `clear` first paints the source box per row from column `bg_x`, so tails of neighbouring lines survive; `dark=False` for light ink), `patch.flat_fill`. Workflow: run `words` first, read the ranges, then `move` / `clear`. |
| `patch` | `missing_glyphs` (`replace_line` and `replace_block` raise `ValueError("font has no glyph for U+....")` instead of printing a hollow box, e.g. `→` in Helvetica Neue: use Arial Bold or SF), `ink_bbox`, `fit` (size by cap height, tracking by width), `render_text`, `paste_text`, `blend_fill` (Laplace inpaint), `glow_text`, `emblem_text` (round glowing-lettering emblem, optional ring), `fill_from_side` (repeat the edge line beside a box across it), `replace_block` (swap a paragraph whose line count changes: corner, colour and erase from the old ink, size shrinks to fit width; `cap_from_ink` sizes from the old ink height, `stretch_to_ink` scales one line to the old ink width so a number swapped in a narrower stand-in font leaves no gap, `align`, `thr` for mid-tone light ink, `dark=False`, `font_index` for .ttc; the bottom check uses the real printed ink), `replace_line` (swap one text line, `dark=False` for light ink on a dark ground: erase, cap height and ink colour taken from the old ink, `squeeze=True` tracks down to -0.04 em), `lerp_fill`, `erase_between`, `size_for_cap`, `baseline_for_top`. |
| `erase` | `erase_footer`: OCR (tesseract) + OpenCV inpaint of a baked-in footer tag. |
| `slots` | `find_white_slots`, `find_slots` (white or magenta, quads), `paste_quad` (perspective paste), `fill_slots` (`key`, `mode` flat, quad or pixel; pixel pastes only where the magenta slot was visible, magenta only): paste real logos into blank white or magenta slots. |
| `lockup` | `trim(im, thr)`, `lockup([a, b], height, sep, gap, second_scale, font)`; CLI `deckkit lockup OUT a.png b.png [--height --sep --gap --second-scale --font --trim-out DIR]`. Trims transparent/white margin (reuses `compose.trim`, now with tolerance `thr`), turns near-white transparent, equal height (second logo `second_scale`x), grey mark between. Empty/unreadable logo -> ValueError, missing file -> FileNotFoundError. |
| `photo` | `cover`, `place`, `circle`: cover-crop a real photo into a rounded box or circle. |
| `recolour` | `bars`: find thin vertical accent bars right of `x_from`, recolour top to bottom; antialiasing kept. Count mismatch raises. |
| `table` (page furniture) | optional `kicker`, `sub`, `widths`, `highlight` (glowing teal "ours" column), `mark_rule` (red/green cells from a value such as "Tidak ada"), `notes`, `ribbon`; `deckkit table extra.json out.png --from-md deck.md --section 25` reads Kicker, Headline, Sub, the table, notes and Pita from the deck. |
| `table` | `render(spec, size, font_path)`: comparison page drawn with PIL (title, header, rows, optional `good`/`bad` cell marks as soft green / red tints). Font size searched per page; a cell that fits at no size raises `ValueError("cell r,c does not fit")`. Bottom band left empty. |
| `deckmd` | `review_html(md_text, title)`: standalone phone-readable HTML, one card per `#`/`##` section, all text escaped. `from_prompts(dir)`: `## Slide NN` sections (numeric order) with the quoted TEXT lines of each `slide-NN.md` as `- role: text` bullets; skips other files and `_rejected/`; no slide file raises `ValueError("no slide-NN.md in <dir>")`. |
| `chrome` | `find_chrome` ($CHROME_BIN, PATH names, macOS app), `shot` (HTML -> PNG at an exact size, crops extra pixels, raises if smaller), `print_pdf`. Temp profile, 120 s timeout. CLI `shot`. |
| `chips` | `pill` (RGBA label with rounded ends), `flag` (equal stripes, `h` or `v`). Library only, no CLI. |

## Not folded in

Per-slide fixes that hard-code coordinates (recolour one bar set, redraw one timeline, remove one
flag, rebuild one slide from panels) and prompt builders tied to one deck. The reusable parts of
them are `patch` and `blend_fill`.

Tests: `tests/py/test_deckkit.py` (run with the venv python; skips without Pillow/numpy).

## sign — tanda tangan dan stempel ke surat PDF

`deckkit sign plan.json` menempel gambar (tanda tangan, stempel) ke PDF yang sudah ada, tanpa
merasterkan halamannya: teks tetap bisa dipilih. Posisi diukur dari teks jangkar (mis. nama
penanda tangan), jadi tetap pas walau draf Word digeser. Tanpa `page`, jangkar dicari dari
halaman terakhir. Latar putih dibuat transparan (`keep_white: true` untuk mematikan).

```json
{"src": "surat.pdf", "dst": "surat-ttd.pdf",
 "items": [{"image": "stempel.jpeg", "anchor": "Budi Santoso", "dx": -40, "dy": -80, "width": 90, "opacity": 0.85},
           {"image": "ttd.png", "anchor": "Budi Santoso", "dx": -5, "dy": -62, "width": 115}]}
```

## letterhead — kop surat ke surat PDF

`deckkit letterhead plan.json` menggambar kop (logo kiri, baris teks rata kanan, garis bawah
berwarna) di atas halaman yang dipilih (bawaan: halaman 1). Isi halaman itu digeser turun
secukupnya; diperkecil hanya kalau baris terakhir akan lewat batas bawah. Teks tetap bisa
dipilih, jadi `deckkit sign` sesudahnya tetap menemukan jangkarnya. Urutan: `letterhead` lalu `sign`.

## repage — surat PDF ke jumlah halaman tertentu, plus nomor halaman

`deckkit repage plan.json` memotong tiap halaman per baris (gambar seperti tanda tangan ikut
baris yang ditimpanya), lalu menyusunnya ulang ke `pages` halaman dengan satu skala bersama,
sebesar mungkin dan tidak lebih dari 1. Baris tidak pernah terbelah; `keep` menjaga satu blok
(mis. dari "Hormat kami" sampai "Founder & CEO") tetap utuh. Tiap baris disalin dari salinan
halaman yang sudah diredaksi, jadi tidak ada teks tersembunyi yang ikut. `footer` menulis nomor
halaman di tengah bawah. Urutan lengkap surat: `repage` → `letterhead` → `sign`.
