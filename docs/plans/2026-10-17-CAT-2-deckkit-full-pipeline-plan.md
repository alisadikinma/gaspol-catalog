> **For Claude:** REQUIRED SKILL: Use gaspol-execute to implement this plan.
> **CRITICAL:** This plan specifies real integrations. During execution,
> NEVER substitute placeholders for real data sources without explicit
> user approval. If a data source doesn't exist yet, STOP and ask.
> **Progress ledger — HARD PER-PHASE GATE:** `.gaspol/progress/PROGRESS-CAT-2.md`. After EACH phase and **BEFORE** starting the next, STOP and do BOTH: (a) tick that phase's `## Checklist` line, (b) append a `## Log` line ending with the handoff cursor. This is **blocking**, like a test gate: no next phase until both are written. **Never batch all updates at the end.** Update ONLY this file — never the shared `.gaspol/progress.md`.
> **Self-contained:** this plan is the COMPLETE spec. It must be executable by an agent with **no other context**. Every file path, contract, config key, and convention it needs is written here verbatim.

**Ticket:** CAT-2
**Ledger:** .gaspol/progress/PROGRESS-CAT-2.md
**Spec:** docs/plans/2026-10-17-CAT-2-deckkit-full-pipeline-spec.md
**Artifact:** https://claude.ai/artifact/CC9U17vjvyT4UPGnJFDUF8

## Goal

Make `tools/deckkit/` the one library for the whole offer-deck pipeline — slide spec → prompt
files → images → post-render fixes → PDF — so no new deck re-writes `make_prompts.py`,
`render.py` or a post-render fix. Every tool has exactly one row in `docs/tool-routing.md`
(the registry), enforced by a test. The bright isometric style of the latest decks becomes a
reusable preset in the plugin, and the seller's identity becomes a house-standard file
outside the plugin that new decks read instead of being re-explained.

## Architecture Context

Repo: `/Users/alisadikin/Drive-D/claude-plugin/gaspol-catalog`, branch `feat/deckkit-library`
(baseline commit `20b9232`). Read `CLAUDE.md` in the repo root first. Rules that bind this plan:

- **Hard rule 2:** single-company / single-identity knowledge is a runtime input, never
  committed to `references/` or `skills/`. `tests/guard-generic.sh` greps both trees for
  `indusia|irn[ -]?cargo|indrajaya|yafindo|ekaputra|tranzporter|global pratama|hub71|alisadikin|0F59B6|batam|pekanbaru|makassar`
  and for absolute addresses `/Users/|/home/[a-z]|C:\\Users|Drive-D|Obsidian-Vault|obsidian-vault|20-Projects|10-Identity|90-Inbox`.
  This plan extends the same guard to `tools/`.
- **Hard rule 6:** `SKILL.md` frontmatter = `name` + `description` only (`tests/frontmatter.sh`).
- **Hard rule 7:** a render prompt is a file (`prompts/slide-NN.md`), never a chat turn.
  Rejected renders go to `prompts/_rejected/` named by defect.
- **Hard rule 4:** page numbers are never generated in the image and never stamped before the
  human approves renders. Logo, chapter rail, watermark are composited after render.
- **Tool-first rule:** library generic; slide numbers, coordinates, client names, absolute paths
  stay in the project as arguments or a small spec file.

Existing deckkit (v0.8.0), public API — DO NOT break any of it:

| Module | Functions |
|---|---|
| `pdf` | `list_pages(src, pattern=r"\d{2}\.png|slide-\d+\.png", skip=())`, `build_pdf(pages, out, page_size=None, dpi=150, mark_opts=None, marked_dir=None, font_path=None)` |
| `pptx` | `build_pptx(images, out, width_in=13.333, height_in=7.5)` |
| `stamp` | `LAYOUT`, `band_colour(im, layout)`, `white_wordmark(path, target_h)`, `stamp(src, dst, number, wordmark=None, layout=LAYOUT, font_path=None)`, `stamp_dir(src, dst, wordmark_path=None, pattern=r"\d{2}\.png", layout=LAYOUT, font_path=None)` |
| `band` | `GREY`, `RULE`, `trim(img)`, `add_band(page, text, logos=(), band_frac=0.055, bg=(255,255,255), ink=GREY, rule=RULE, sep="×", ...)` |
| `watermark` | `DEFAULTS`, `is_dark(im, probe, threshold)`, `mark(im, font_path=None, ink=None, **opts)`, `unmark(im, font_path=None, ink=None, dark=None, **opts)` (reversible alpha composite) |
| `patch` | `ink_bbox(img, box, dark=True, thr=150)`, `render_text(text, font_path, size, fill, tracking=0.0)`, `fit(text, font_path, target_w, cap_h, fill, tol=1)`, `blend_fill(img, box, iterations=600)`, `paste_text(img, patch, xy, anchor="lb")`, `glow_text(...)` |
| `slots` | `find_white_slots(img, min_area=0.01, white=235)`, `trim_logo(path, white=240)`, `fill_slots(img, logo_paths, min_area=0.01, fit=(0.78, 0.7))` |
| `erase` | `find_word(bgr, needle, region_top=0.86)`, `erase_footer(path, needle, region_top=0.86, ink_delta=35, out=None)` |
| `fonts` | `CANDIDATES`, `load_font(px, path=None)` |
| `__main__` | argparse subcommands `pdf pptx stamp band unmark erase-footer logo-slots`; each branch lazily imports its module; `FileNotFoundError/ValueError/RuntimeError` → `FAIL: <msg>` on stderr, exit 1 |

Docs: `docs/tool-routing.md` (table `| I want to... | Use |`), `docs/deckkit.md` (module table).
Tests: `tests/py/test_deckkit.py` (unittest, 9 tests, skips without Pillow/numpy), shell gates in
`tests/run-all.sh` (`deps-present research-contract guard-generic frontmatter refs-present fixture-shape`).
Skills touched: `skills/catalog-visual/SKILL.md`, `skills/catalog-brainstorm/SKILL.md`,
`references/b2b/b2b-brand-intake.md`. Version: `.claude-plugin/plugin.json` (currently 0.8.0), `README.md`.

Source scripts to port FROM (read them, keep them, never delete them — they are the reference
implementations). Short names used below:

- `EKA` = `/Users/alisadikin/Drive-D/pitch-deck/Ekaputra-Dinata-Utama/renders/v3-slide`
- `MONI` = `/Users/alisadikin/Drive-D/pitch-deck/MoniBatamInovasi/prospects/pt-moni-batam-inovasi`
- `CAT0` = `/Users/alisadikin/Drive-D/pitch-deck/indusia-ai-fms/catalog/tools`
- `C3` = `/Users/alisadikin/Drive-D/pitch-deck/indusia-ai-fms/catalog-3/tools`
- `SPS` = `/Users/alisadikin/Drive-D/pitch-deck/indusia-ai-fms/prospects/sps-samudera-perdana-selaras/tools`

## Tech Stack

- Python 3, run with `~/.gaspol-video/venv/bin/python` (has Pillow 12.3, numpy 2.5, OpenCV 5.0;
  NO PyYAML, NO python-pptx). Below, `PY` means that path.
- stdlib `json`, `argparse`, `concurrent.futures`, `importlib`, `subprocess`, `unittest`.
- tesseract at `/opt/homebrew/bin/tesseract` (existing `erase`).
- Image generator: external module `mcp_image_server` in the repo
  `/Users/alisadikin/Drive-D/claude-plugin/geminigen-api-client`. Signature:
  `generate_image(prompt, model="nano-banana-2", aspect="16:9", style="Photorealistic", mode=None, resolution="4K", output_format="png", output_dir=..., refs=None, poll_timeout=420, poll_interval=6) -> str`;
  the function may be wrapped by FastMCP — unwrap with `getattr(m.generate_image, "fn", m.generate_image)`.
  Success string starts with `OK` and contains `local: <path>`. Its location is NEVER written in
  plugin code: it comes from the house standard key `image_client` or `$DECKKIT_IMAGE_CLIENT`.

**detect-stack:** no stack markers for this project — verification is plan-declared only. The
commands used in every Verification block are:
- `unit:` `PY -m unittest discover -s tests/py -t . -v` (from repo root)
- `gates:` `bash tests/run-all.sh` (prints `ALL GREEN`)

## Shared contracts (verbatim — every phase relies on these)

### House-standard / preset file format

Both the style preset (in the plugin) and the house standard (outside) are markdown files whose
machine part is the FIRST fenced block opened with three backticks + `json`. Prose around it is
for humans. Loader: `tools/deckkit/house.py`.

House standard resolution (`house.resolve(explicit=None, start=cwd)`), first hit wins:
1. `explicit` (CLI `--house PATH`).
2. env `GASPOL_CATALOG_HOUSE`.
3. nearest ancestor of `start` containing `.gaspol/context-sources.md` with a line
   `house-standard: <path>` (path may use `~`).
4. none → return `None` (not an error; callers degrade and say so).

House standard JSON keys (all optional except `seller` and `preset`):
`seller` (str), `preset` (str, name of a file in `references/b2b/styles/` without `.md`),
`logo` (path), `wordmark` (path), `watermark` (str), `corner` (str), `band_text` (str with
`{client}`), `site` (str), `phone` (str), `image_client` (dir path), `image_model` (str),
`image_mode` (str|null), `style_refs` (list of paths), `language` (str, default `"Indonesian"`).

Preset JSON keys: `name`, `intro` (with `{language}`, `{seller}`, `{audience}`), `style`,
`guard` (with `{seller}`, `{ai}`), `ai_clause` (text substituted for `{ai}` when a slide has
`"ai": true`), `people_clause_from`, `people_clause_to` (substring swap when a slide has
`"people": true`), `text_header`, `roles` (dict of reusable role labels, e.g. `eye`, `eye_problem`,
`head`, `foot`), `palette` (dict name → hex), `fonts` (dict).

### Deck spec (per project, written by `catalog-visual`)

`slides.json` in the project:

```json
{
  "audience": "a food distributor",
  "client": "PT Contoh",
  "ref_dir": "ref/illustrations",
  "slides": [
    {"n": 2, "sid": "masalah-gudang",
     "layout": "Top: eyebrow and headline ...",
     "visual": "The cluttered manual warehouse ...",
     "text": [["eyebrow, small caps burnt orange", "PERMASALAHAN 1 · GUDANG"],
              ["headline, large bold navy", "..."]],
     "refs": ["gudang-kacau.jpg"],
     "ai": false, "people": false, "extra": ""}
  ]
}
```

Prompt file layout (`prompts/slide-NN.md`), exactly this order, blank line between blocks:

```
<intro>

LAYOUT: <layout>

VISUAL: <visual>

<style>[ <extra>]

<text_header>
- <role>: "<text>"
...

<guard>
```

Manifest `prompts/manifest.json`: list of `{"n": int, "sid": str, "prompt_file": "prompts/slide-NN.md", "refs": [abs paths]}`.
Refs resolve: house `style_refs` first (in order), then slide `refs` joined to `ref_dir` (relative
to the spec file's directory).

### Registry table format (`docs/tool-routing.md`)

The routing table gains a third column naming the module:

```
| I want to... | Use | Module |
|---|---|---|
| Pages folder -> PDF ... | `deckkit pdf ...` | `pdf` |
```

Registry test rules: (a) every `tools/deckkit/*.py` except `__init__`, `__main__`, `fonts`, `house`
appears in at least one row's Module column; (b) every Module cell names an existing module file;
(c) no two rows have the same "I want to..." text; (d) every `deckkit <cmd>` in the Use column is
a subcommand registered in `__main__.py` (parse `sub.add_parser("<cmd>"`).

## Data Integration Map

| Feature | Data source | Hook/API | Exists? | Action |
|---|---|---|---|---|
| Registry test | `docs/tool-routing.md` + `tools/deckkit/*.py` + `__main__.py` | file read | Yes (files) | New test reads them |
| House standard | markdown + ```json block outside plugin | `house.resolve/load` | No | Create `house.py`; create the real file in Phase P |
| Style preset | `references/b2b/styles/isometrik-terang.md` | `house.load_preset(name)` | No | Create from EKA STYLE + SPS GUARD (verbatim below) |
| Prompt files | project `slides.json` + preset + house | `prompts.build` | No | Create `prompts.py` |
| Images | `mcp_image_server.generate_image` at house `image_client` | `gen.run` | Yes (external) | Load by path at runtime; tests inject a fake |
| Photo paste | project photos | `photo.place/circle` | No | Create `photo.py` |
| Bar recolour | rendered PNG | `recolour.bars` | No | Port from `EKA/warna_bar.py` |
| Magenta / quad slots | rendered PNG | `slots.find_slots/paste_quad` | Partly (`find_white_slots`) | Extend |
| Text line replace | rendered PNG | `patch.replace_line` etc. | Partly | Extend |
| Logo / grid watermark | rendered PNG | `watermark.mark(logo=, grid=)` | Partly | Extend (keep reversibility for text mode) |
| Band url / n of N / fit canvas | rendered PNG | `band.add_band(url=, number=, total=, fit_canvas=)` | Partly | Extend |
| PPTX fade | PNGs | `pptx.build_pptx(transition=, jpeg_quality=)` | Partly | Extend; install python-pptx |
| Table page | project rows | `table.render` | No | Port from `SPS/tabel_25.py` |
| Review HTML / deck.md | project `deck.md` / prompt files | `deckmd.review_html/from_prompts` | No | Port from `SPS/buat_review.py`, `C3/build_deck_md.py` |
| HTML → PNG/PDF | headless Google Chrome | `chrome.shot/print_pdf` | Yes (app) | Port from `MONI/render/shot.sh` |
| Pill / flag | PIL drawing | `chips.pill/flag` | No | Create |

## Phases

### Phase A: Registry test + guard over tools/

**Estimated time:** 15 minutes

**Files:**
- Create: `tests/py/test_registry.py`
- Modify: `docs/tool-routing.md` (add Module column to every existing row)
- Modify: `tests/guard-generic.sh` (scan `tools/` too, both patterns)
- Modify: `tests/run-all.sh` (add a Python step: run `PY -m unittest discover -s tests/py -t .` when `~/.gaspol-video/venv/bin/python` exists, else print `SKIP python (venv absent)`; failure sets rc=1)

**Steps:**
1. Write failing test for the registry rules (a)–(d) in `tests/py/test_registry.py`. Expected error: `AssertionError` — current table has no Module column (rule a fails for every module).
2. Run `PY -m unittest tests.py.test_registry -v`, confirm it fails for that reason.
3. Add the Module column to every row of `docs/tool-routing.md`: pdf→`pdf`, public version→`pdf`, pptx→`pptx`, stamp→`stamp`, band→`band`, unmark→`watermark`, erase-footer→`erase`, logo-slots→`slots`, patch→`patch`. The row "Rendering the page images themselves" is deleted here (Phase F re-adds the gen row).
4. Run the test, confirm pass.
5. Add `tools/` to both grep calls in `tests/guard-generic.sh` (`grep -rniE "$PAT" references/ skills/ tools/` and same for `$ADDR`), with `--include='*.py' --include='*.md'` so `__pycache__` is skipped. Run it; if it fails on existing code, fix the code (move the value to an argument), never weaken the pattern.
6. Add the Python step to `tests/run-all.sh`. Run `bash tests/run-all.sh`.
7. Commit: `test(deckkit): routing registry test, guard scans tools/ (CAT-2)`

**Edge cases:** module with no row; row pointing to a deleted module; duplicate "I want to" text; `deckkit foo` with no parser — each needs its own assertion message naming the offender.
**Error paths:** routing file missing → test fails with the path in the message.
**Observability:** each assertion message lists the offending module/row text.

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN` and includes the Python step
- [ ] Temporarily touching `tools/deckkit/zz.py` makes the registry test fail naming `zz` (then remove it)
- [ ] No placeholder/TODO comments in new code

### Phase B: house.py — resolve and load house standard and presets

**Estimated time:** 15 minutes

**Files:**
- Create: `tools/deckkit/house.py`
- Test: `tests/py/test_house.py`

**Steps:**
1. Write failing test for `house.load_json_block(path)`, `house.resolve(explicit, start, env)`, `house.load(path)`, `house.load_preset(name)`. Expected error: `ImportError: cannot import name 'house'`.
2. Run, confirm it fails for that reason.
3. Implement: `load_json_block` returns the dict from the first fenced json block; raises `ValueError("no json block in <path>")` when absent and `ValueError("bad json in <path>: <msg>")` on parse error. `resolve` follows the 4-step order in Shared contracts (`env` parameter defaults to `os.environ`, for testability; expands `~`; a named path that does not exist raises `FileNotFoundError`). `load` validates `seller` and `preset` present (`ValueError("house standard <path> missing key: seller")`). `load_preset(name)` reads `references/b2b/styles/<name>.md` relative to the plugin root (`Path(__file__).resolve().parents[2]`); unknown name → `FileNotFoundError` listing available presets.
4. Run tests, confirm pass.
5. Commit: `feat(deckkit): house standard + preset loader (CAT-2)`

**Edge cases (each a test):** explicit path wins over env and file; env wins over file; context-sources in a grandparent dir; line with `~`; context-sources without the key → next step; nothing → `None`; markdown with two json blocks → first used; empty json `{}` → `load` raises missing key.

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

### Phase C: Style preset `isometrik-terang`

**Estimated time:** 15 minutes

**Files:**
- Create: `references/b2b/styles/isometrik-terang.md`
- Modify: `tests/refs-present.sh` (add `styles/isometrik-terang.md` to the list; message `refs OK — 9 berkas`)
- Test: `tests/py/test_house.py` (add preset test)

**Steps:**
1. Write failing test: `house.load_preset("isometrik-terang")` returns dict with keys `name intro style guard ai_clause people_clause_from people_clause_to text_header roles palette fonts`, `{seller}` present in `guard`, and no `INDUSIA`/`indusia` anywhere. Expected error: `FileNotFoundError` (preset absent).
2. Run, confirm failure.
3. Write the preset. Prose sections (≥20 lines total, plain English): Palette, Illustration, Type, Layout grammar, Slide variants, When not to use. JSON block values — copy verbatim:
   - `intro`: `"A finished 16:9 presentation slide in {language} for a B2B offer from {seller} to {audience}."`
   - `style`: `"STYLE: bright, clean corporate slide. Background light warm grey #f3f6f5 unless the layout says otherwise. Headlines deep navy #15212b; accent teal #23857f; second accent amber #a8712a; steel blue #2c5d99; issue slides use burnt orange #b8561a for eyebrow and bars; body grey #44545e. Illustration: clean isometric 3D, soft matte clay, soft shadows, same look as the style reference image. Headline in a bold condensed sans-serif; body in a clean sans-serif; crisp, left-aligned, high contrast, readable on a phone. Use the first reference image ONLY for the exact {seller} wordmark. Use the second reference image ONLY as the style source, do not copy its objects."`
   - `guard`: `"RULES: The words before each colon are layout instructions and are never printed; only the strings between straight double quotes print. Each quoted string prints exactly once, spelled exactly, every digit exact. No other words, numbers or labels anywhere. No English words unless quoted. No people, no faces, no hands. No chart axes with numbers. Documents, receipts, papers, signs and boxes are blank: plain lines or plain shapes only, never letters. The only other lettering allowed is the {seller} wordmark on app screens{ai}. No other logos or brand names. Do not add decorative blocks or shapes that are not described. Keep every line of text in its own clear space; illustrations never overlap text. Every object is sharp, solid and fully drawn: no blurred, ghosted, smeared or half-transparent objects, and nothing copied from the style reference image. Every magenta area is exactly as described: one flat, solid, bright magenta #ff00ff shape with sharp edges, no outline, no shading, no text, no letters and no icon inside; magenta is used nowhere else on the canvas, and no magenta area is added that is not described. Leave the bottom 3% of the canvas empty. Nothing clipped."`
   - `ai_clause`: `" and the two letters AI on the AI chip or on a brooch badge"`
   - `people_clause_from`: `"No people, no faces, no hands. "`, `people_clause_to`: `"No people other than the figures described. "`
   - `text_header`: `"TEXT (print exactly these, verbatim, each once):"`
   - `roles`: `{"eye": "eyebrow, small caps teal", "eye_problem": "eyebrow, small caps burnt orange", "head": "headline, large bold navy", "foot": "small grey footer line at the bottom-left"}`
   - `palette`: `{"background": "#f3f6f5", "price_background": "#e6eeee", "navy": "#15212b", "teal": "#23857f", "amber": "#a8712a", "steel_blue": "#2c5d99", "burnt_orange": "#b8561a", "body": "#44545e"}`
   - `fonts`: `{"headline": "bold condensed sans (Oswald-like)", "body": "clean sans (Roboto/Inter-like)"}`
   Layout grammar prose (copy): eyebrow above headline (teal on solution slides, burnt orange on problem slides); body = illustration left 55–65% (62% typical) + right text column 35–45% with 3–4 points (bold title + grey detail) each with a coloured left bar — burnt orange on problem slides, matching the illustration's colour on solution slides; variants: three equal columns, 2×2 rule cards, ascending isometric steps, pale full-width banner with a thick left bar, numbered items in burnt-orange circles; cover: text left 40% / illustration right 60% with a tricolour stripe (steel blue, teal, amber) along the top edge; proof slide: dark navy `#15212b` background, white and teal text; price and closing slides: `#e6eeee` background; footer: small grey line bottom-left for the source or `ILUSTRASI · …`; footer band and page numbers are composited after render, never drawn.
4. Run test + `bash tests/refs-present.sh` + `bash tests/guard-generic.sh`, confirm pass.
5. Commit: `feat(catalog): isometrik-terang style preset (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN` (`refs OK — 9 berkas`, guard OK)
- [ ] No placeholder/TODO comments in new code

### Phase D: prompts.py — slide spec → prompt files + manifest

**Estimated time:** 15 minutes

**Files:**
- Create: `tools/deckkit/prompts.py`
- Modify: `tools/deckkit/__main__.py` (subcommand `prompts SPEC [--house PATH] [--preset NAME] [--out DIR] [--only N ...]`)
- Test: `tests/py/test_prompts.py`

**Steps:**
1. Write failing test: `prompts.render_prompt(slide, preset, ctx)` returns the exact layout in Shared contracts; `prompts.build(spec_path, house=..., preset=..., out_dir=...)` writes `slide-NN.md` + `manifest.json`. Expected error: `ImportError: cannot import name 'prompts'`.
2. Run, confirm failure.
3. Implement. Rules: `{seller}` from house `seller` (or `--seller`-less: preset placeholder left → refuse with `ValueError("no seller: pass --house or set GASPOL_CATALOG_HOUSE")`); `{language}` from house `language` default `Indonesian`; `{audience}` from spec; `{ai}` → `ai_clause` if slide `ai` else `""`; `people` → swap clause; `extra` appended to style after one space. Text lines `- <role>: "<text>"`; a text containing `"` → `ValueError` naming slide and role (straight quotes break the guard). Refuse (ValueError, message names both slide numbers): duplicate `n`; the same text string under a role containing `footer` or `band` on two slides (the C3 duplicate-band rule); empty `text`; missing ref file (message names the path). `--only` writes only those slides but rewrites manifest for all. Prints `N prompt -> DIR`.
4. Run tests, confirm pass.
5. Commit: `feat(deckkit): prompts — slide spec to prompt files + manifest (CAT-2)`

**Edge cases (tests):** `ai` true/false; `people` true; extra empty vs non-empty; duplicate footer string; quote in text; missing ref; `--only 2`; house absent → refusal message.
**Observability:** CLI prints count and output dir; every refusal names slide `n` and field.

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] `PY -m tools.deckkit prompts --help` lists the options
- [ ] No placeholder/TODO comments in new code

### Phase E: prompts parity check against a real deck

**Estimated time:** 10 minutes

**Files:**
- Create: `tests/py/fixtures/slides-parity.json` (one slide, generic text — copy layout/visual/text roles of `EKA/prompts/slide-02.md` but replace client words: `GFSoft`→`SistemLama`, drop the source line)
- Test: `tests/py/test_prompts.py` (parity test)

**Steps:**
1. Write failing test: building the fixture with preset `isometrik-terang` and seller `ContohAI` yields a file whose block ORDER and TEXT-block line format equal those of `EKA/prompts/slide-02.md` (compare by splitting on blank lines and checking each block's prefix: intro starts `A finished 16:9`, then `LAYOUT:`, `VISUAL:`, `STYLE:`, `TEXT (print exactly`, `RULES:`). Expected error: `FileNotFoundError` (fixture absent).
2. Run, confirm failure.
3. Create the fixture. Do NOT read EKA files from the test (they are outside the repo); hardcode the expected prefixes in the test. Manually diff once: `diff <(sed -n '/^TEXT/,/^$/p' <generated>) <(sed -n '/^TEXT/,/^$/p' $EKA/prompts/slide-02.md)` and record in the ledger that only client words differ.
4. Run tests, confirm pass.
5. Commit: `test(deckkit): prompt layout parity fixture (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] Ledger records the manual diff result
- [ ] No placeholder/TODO comments in new code

### Phase F: gen.py — manifest → images

**Estimated time:** 15 minutes

**Files:**
- Create: `tools/deckkit/gen.py`
- Modify: `tools/deckkit/__main__.py` (subcommand `gen MANIFEST [--house PATH] [--ver V] [--only N ...] [--model M] [--mode M] [--workers 4] [--tries 3] [--out DIR] [--raw DIR] [--resolution 2K]`)
- Modify: `docs/tool-routing.md` (rows for `prompts` and `gen`, Module `prompts` / `gen`)
- Test: `tests/py/test_gen.py`

**Steps:**
1. Write failing test: `gen.run(manifest, generator=fake, out_dir, raw_dir, ver, only, workers, tries, model, mode)` with a fake generator that returns `OK local: <tmp png>` / raises / returns `ERR x`. Expected error: `ImportError: cannot import name 'gen'`.
2. Run, confirm failure.
3. Implement: `load_generator(client_dir)` inserts dir on `sys.path`, imports `mcp_image_server`, unwraps `.fn`; dir from `--house` key `image_client` else `$DECKKIT_IMAGE_CLIENT`; neither → `RuntimeError("no image client: set image_client in the house standard or DECKKIT_IMAGE_CLIENT")`; import failure → `RuntimeError` with the dir. Each slide: read prompt file (path relative to the manifest's parent's parent when relative, i.e. project root), call `generator(prompt=..., model=..., mode=..., aspect="16:9", resolution=..., output_format="png", output_dir=raw_dir, refs=refs or None)` (pass `style="None"` only when the generator accepts `style` — inspect signature), retry up to `tries` on exception or non-`OK`, copy `local:` file to `out_dir/NN-<ver>.png` (or `slide-NN.png` when no `--ver`). Never overwrite an existing output file: if present, refuse that slide with `exists` (renders are approved artifacts). Returns list of `(n, status)`; CLI prints one line per slide, exit 1 if any slide failed.
4. Run tests, confirm pass.
5. Add routing rows: "Slide spec -> prompt files + manifest" → `deckkit prompts slides.json --house H` | `prompts`; "Prompt files -> slide images (image MCP)" → `deckkit gen prompts/manifest.json --ver r1` | `gen`.
6. Commit: `feat(deckkit): gen — render manifest via image client (CAT-2)`

**Edge cases (tests):** all ok; one slide fails all tries → status carries last error, others still produced; exception path; `--only`; existing output → `exists`; missing prompt file → that slide `FAIL missing prompt`.
**Observability:** per-slide line `NN OK|exists|FAIL <first 200 chars>`; raw files kept in `--raw`.

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes (registry test now covers prompts/gen)
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No real image API call in tests
- [ ] No placeholder/TODO comments in new code

### Phase G: photo.py — photo into box or circle

**Estimated time:** 10 minutes

**Files:**
- Create: `tools/deckkit/photo.py`
- Modify: `__main__.py` (subcommand `photo IMAGE PHOTO --box x,y,w,h [--radius R] [--circle] [--out PATH]`)
- Modify: `docs/tool-routing.md` (row, Module `photo`)
- Test: `tests/py/test_photo.py`

**Steps:**
1. Write failing test: `photo.cover(photo, (w,h))` crops to exact size keeping centre; `photo.place(page, photo, box, radius=0)` only changes pixels inside the rounded box; `photo.circle(page, photo, centre, r)` only changes pixels inside the circle. Expected error: `ImportError`.
2. Run, confirm failure.
3. Implement (port technique from `MONI/render/tools/swap_photos.py` and `SPS/tempel_16.py`: object-fit cover, antialiased mask drawn at 4× then downsampled). Box outside page → `ValueError`.
4. Run tests, confirm pass; add routing row "Real photo into a photo well or empty circle".
5. Commit: `feat(deckkit): photo — cover-crop into box or circle (CAT-2)`

**Edge cases:** portrait photo into landscape box and reverse; radius 0; radius > half side (clamp); RGBA photo.

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

### Phase H: recolour.py — accent bars

**Estimated time:** 10 minutes

**Files:**
- Create: `tools/deckkit/recolour.py`
- Modify: `__main__.py` (subcommand `recolour IMAGE --colours "#2c5d99" "#23857f" ... [--x-from 0.55] [--out PATH]`)
- Modify: `docs/tool-routing.md` (row, Module `recolour`)
- Test: `tests/py/test_recolour.py`

**Steps:**
1. Write failing test: synthetic page with 3 thin teal vertical bars in the right half; `recolour.bars(img, ["#2c5d99","#a8712a","#15212b"], x_from=0.55)` recolours them top-to-bottom; count mismatch raises `ValueError("found 3 bars, expected 4")` and leaves the image unchanged. Expected error: `ImportError`.
2. Run, confirm failure.
3. Port `EKA/warna_bar.py` (cv2 connected components, aspect filter `h > 5% page`, `w < 1.2% page`, `h/w > 4`, projected colour shift preserving antialiasing). Hex input; bar detection colour configurable (`source="#23857f"`, tolerance) instead of the hardcoded teal mask.
4. Run tests, confirm pass; routing row "Recolour the accent bars beside text points".
5. Commit: `feat(deckkit): recolour — accent bars top to bottom (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

### Phase I: slots — magenta slots and perspective paste

**Estimated time:** 15 minutes

**Files:**
- Modify: `tools/deckkit/slots.py` (add `find_slots(img, key="white"|"magenta", min_area=0.002)` → list of quads `[(x,y)*4]` sorted left-to-right then top-to-bottom; `paste_quad(img, logo, quad, plate=None, fit=0.8)`; `fill_slots(..., key="white", mode="flat"|"quad")` keeps old default behaviour)
- Modify: `__main__.py` (`logo-slots` gains `--key {white,magenta}` and `--mode {flat,quad}`)
- Modify: `docs/tool-routing.md` (update logo-slots row; add "Logo onto a tilted screen" row, both Module `slots`)
- Test: `tests/py/test_deckkit.py` (existing slot tests must stay green) + new cases

**Steps:**
1. Write failing test: magenta parallelogram on a page → `find_slots(key="magenta")` returns one quad within 3 px of the true corners; `paste_quad` leaves no `#ff00ff` pixel (tolerance 40) in the region. Expected error: `AttributeError: module 'tools.deckkit.slots' has no attribute 'find_slots'`.
2. Run, confirm failure.
3. Port from `SPS/tempel_25.py` (magenta mask, connected components, 4 corners via `cv2.approxPolyDP`/min-area quad) and `SPS/tempel_sps.py` (8-coefficient perspective solve, PIL `Image.PERSPECTIVE`). Fill leftover magenta edge pixels with neighbouring colour (`patch.blend_fill`). Slot count ≠ logo count → `ValueError("found N slots, got M logos")`.
4. Run all tests, confirm pass (old `fill_slots` tests unchanged).
5. Commit: `feat(deckkit): slots — magenta key, perspective paste (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] Existing `logo-slots` CLI with no new flags behaves as before
- [ ] No placeholder/TODO comments in new code

### Phase J: patch — line replacement helpers

**Estimated time:** 15 minutes

**Files:**
- Modify: `tools/deckkit/patch.py` (add `replace_line(img, box, text, font_path, fill=None, align="left")`, `lerp_fill(img, box)`, `erase_between(img, box, bg=None)`, `size_for_cap(font_path, cap_h)`, `baseline_for_top(font_path, size, top)`)
- Modify: `docs/tool-routing.md` (extend the patch row text with `replace_line`)
- Test: `tests/py/test_deckkit.py` (new cases)

**Steps:**
1. Write failing test: page with a dark text line in a box → `replace_line` erases it (no ink left from the old glyphs outside new glyph bbox), writes the new text with cap height within ±1 px of the old ink height, ink colour sampled from the old ink when `fill=None`. Expected error: `AttributeError: ... has no attribute 'replace_line'`.
2. Run, confirm failure.
3. Port: `lerp_fill` = per-row left-to-right edge interpolation from `EKA/tambal_teks.py`; `replace_line` = `ink_bbox` → `lerp_fill` (flat background) → `fit` → `paste_text`; `size_for_cap`, `baseline_for_top`, `erase_between` from `CAT0/revisi_2026_09_15.py` and `C3/finalize.py`. New text wider than box → `ValueError` unless a `squeeze=True` flag allows tracking down to −0.04 em.
4. Run tests, confirm pass.
5. Commit: `feat(deckkit): patch — replace_line and fill helpers (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

### Phase K: watermark — logo tile and grid

**Estimated time:** 10 minutes

**Files:**
- Modify: `tools/deckkit/watermark.py` (`mark(..., logo=None, grid=None)`; `logo` = path of a logo tiled diagonally at the DEFAULTS opacity; `grid=(cols, rows)` places text in a fixed grid instead of free tiling)
- Modify: `tools/deckkit/pdf.py` + `__main__.py` `pdf` (`--watermark-logo PATH`, `--grid CxR`)
- Modify: `docs/tool-routing.md`
- Test: `tests/py/test_deckkit.py`

**Steps:**
1. Write failing test: `mark(page, logo=<png>)` changes pixels in ≥3 separated places; `unmark(mark(page, text=..., grid=(3,4)), text=..., grid=(3,4))` round-trips within 2 levels per channel. Expected error: `TypeError: ... unexpected keyword argument 'logo'`.
2. Run, confirm failure.
3. Implement (port `EKA/pdf.py` logo tile at 12% alpha, `MONI/render/build_pdf.py` 3×4 grid at 30°). Reversibility kept for text and grid modes; logo mode documented as not reversible (unmark with `logo` → `ValueError("logo watermark is not reversible")`).
4. Run tests, confirm pass.
5. Commit: `feat(deckkit): watermark — logo tile and grid layout (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

### Phase L: band and pptx options

**Estimated time:** 15 minutes

**Files:**
- Modify: `tools/deckkit/band.py` (`add_band(..., url=None, number=None, total=None, number_fmt="{n} / {total}", fit_canvas=None)`)
- Modify: `tools/deckkit/pptx.py` (`build_pptx(..., transition=None, jpeg_quality=None)`)
- Modify: `__main__.py` (`band --url --numbers --number-fmt --fit-canvas WxH`; `pptx --transition fade --jpeg-quality 92`)
- Modify: `docs/tool-routing.md`
- Test: `tests/py/test_deckkit.py`

**Steps:**
1. Write failing test: `add_band(page, "RAHASIA", url="contoh.ai")` output height = input + band; ink present under the logo area; `fit_canvas=(1920,1080)` letterboxes an odd-size page to exactly that size before banding; `number=3, total=10` draws ink at the right end. Expected error: `TypeError: ... unexpected keyword argument 'url'`.
2. Run, confirm failure.
3. Implement (port `SPS/band.py`, `SPS/buat_pdf.py`, `EKA/finish.py`). Numbers only when the caller passes them — CLI `--numbers` takes them from filenames (`NN`), honoring hard rule 4 (the skill calls it only after approval).
4. Install python-pptx into the venv: `~/.gaspol-video/venv/bin/pip install python-pptx`. Record in ledger `## Keputusan saat jalan`.
5. Write failing pptx test: `build_pptx(imgs, out, transition="fade")` → the slide XML contains `<p:transition` and `<p:fade`; `jpeg_quality=92` stores JPEG media. Implement (port `C3/build_pptx.py` raw transition XML). Run, confirm pass.
6. Commit: `feat(deckkit): band url/numbers/fit, pptx fade (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes (pptx tests no longer skipped)
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

### Phase M: table.py — exact-number comparison page

**Estimated time:** 15 minutes

**Files:**
- Create: `tools/deckkit/table.py`
- Modify: `__main__.py` (`table SPEC.json OUT.png [--size 2752x1536] [--font PATH]`)
- Modify: `docs/tool-routing.md` (row, Module `table`)
- Test: `tests/py/test_table.py`

**Steps:**
1. Write failing test: `table.render(spec, size)` where spec = `{"title": str, "columns": [str...], "rows": [[cell...]], "marks": {"r,c": "good"|"bad"}, "palette": {...}}` returns an image of exactly `size`; every cell text fits its cell (font-size search); a cell too long for the minimum size raises `ValueError` naming row/col. Expected error: `ImportError`.
2. Run, confirm failure.
3. Port from `SPS/tabel_25.py` (wrap + font-size search, red/green cell marks), colours from spec `palette` with preset defaults; no client names in module.
4. Run tests, confirm pass; routing row "Comparison table page with exact numbers (drawn, not rendered)".
5. Commit: `feat(deckkit): table — drawn comparison page (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

### Phase N: deckmd.py — review page and deck.md from prompts

**Estimated time:** 15 minutes

**Files:**
- Create: `tools/deckkit/deckmd.py`
- Modify: `__main__.py` (`review DECK.md OUT.html [--title T]`; `deckmd PROMPTS_DIR OUT.md`)
- Modify: `docs/tool-routing.md` (two rows, Module `deckmd`)
- Test: `tests/py/test_deckmd.py`

**Steps:**
1. Write failing test: `deckmd.review_html(md_text, title)` returns standalone HTML containing every slide heading and escaped text (`<` in input → `&lt;`); `deckmd.from_prompts(dir)` collects quoted TEXT strings per `slide-NN.md` into `## Slide NN` sections in numeric order. Expected error: `ImportError`.
2. Run, confirm failure.
3. Port from `SPS/buat_review.py` (strip SPS-specific labels and names) and `C3/build_deck_md.py`. stdlib only (`html.escape`).
4. Run tests, confirm pass.
5. Commit: `feat(deckkit): deckmd — review page, deck.md from prompts (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

### Phase O: chrome.py and chips.py

**Estimated time:** 15 minutes

**Files:**
- Create: `tools/deckkit/chrome.py` (`find_chrome()`, `shot(html, out_png, size=(2752,1536))`, `print_pdf(html, out_pdf)`)
- Create: `tools/deckkit/chips.py` (`pill(text, font_path, size, fg, bg, pad)`, `flag(colours, size, stripes="h")`)
- Modify: `__main__.py` (`shot HTML OUT.png [--size WxH]`; `chips` has no CLI — library only, row cites `tools/deckkit/chips.py`)
- Modify: `docs/tool-routing.md` (rows, Modules `chrome`, `chips`)
- Test: `tests/py/test_chrome_chips.py`

**Steps:**
1. Write failing test: `chips.pill(...)` returns RGBA with transparent corners and opaque centre; `chips.flag([(255,0,0),(255,255,255)], (60,40))` top half red, bottom white; `chrome.find_chrome()` honours `$CHROME_BIN`, else known macOS/Linux names via `shutil.which`, else `RuntimeError("Chrome not found: set CHROME_BIN")`; `chrome.shot` on a tiny HTML produces a PNG of exactly `size` (test skipped when Chrome absent). Expected error: `ImportError`.
2. Run, confirm failure.
3. Port `MONI/render/shot.sh` flags (`--headless=new --hide-scrollbars --force-device-scale-factor=1 --window-size=W,H --screenshot=`), subprocess with timeout 120 s, non-zero exit → `RuntimeError` with stderr tail; verify output size, crop/raise if Chrome added pixels. macOS app path is a candidate inside `find_chrome`, not a constant elsewhere.
4. Run tests, confirm pass.
5. Commit: `feat(deckkit): chrome shot/pdf, chips pill/flag (CAT-2)`

**Verification:**
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN` (guard over tools/ still OK)
- [ ] No placeholder/TODO comments in new code

### Phase P: Skills, docs, and the house standard file

**Estimated time:** 15 minutes

**Files:**
- Modify: `skills/catalog-visual/SKILL.md` — prompt authoring writes `slides.json` and runs `deckkit prompts`; rendering runs `deckkit gen`; post-render steps point to `docs/tool-routing.md`; default preset comes from the house standard (`house-standard` resolution order), fallback = today's behaviour. No path, no seller name.
- Modify: `references/b2b/b2b-brand-intake.md` — new section "Seller house standard": resolution order (named in session → `$GASPOL_CATALOG_HOUSE` → `house-standard:` line in nearest `.gaspol/context-sources.md` → none), pre-fill `brand.md` from it, ask only client-specific items (client name, client logo, client colours), house values carry `[from: house-standard]` provenance.
- Modify: `skills/catalog-brainstorm/SKILL.md` — Step 0 resolves the house standard in the same order before the brand intake questions.
- Modify: `docs/deckkit.md` (module table: add house, prompts, gen, photo, recolour, table, deckmd, chrome, chips; delete "Image generation stays in catalog-visual"; list new options of slots/patch/watermark/band/pptx), `docs/tool-routing.md` intro line ("covers the whole deck pipeline").
- Modify: `CLAUDE.md` (Tool-first rule mentions prompts/gen and the house standard; references index adds `styles/isometrik-terang.md`), `.claude-plugin/plugin.json` → `0.9.0`, `README.md` (version line + changelog line `0.9.0 — deckkit covers prompts and render, isometrik-terang preset, house standard`).
- Create (OUTSIDE the plugin, not committed): `/Users/alisadikin/Drive-D/pitch-deck/ref/house-standard.md` and `/Users/alisadikin/Drive-D/pitch-deck/.gaspol/context-sources.md` (one line `house-standard: /Users/alisadikin/Drive-D/pitch-deck/ref/house-standard.md`).

**Steps:**
1. Write failing test for the real house standard: `house.load(house.resolve(start="/Users/alisadikin/Drive-D/pitch-deck/Ekaputra-Dinata-Utama"))` returns `preset == "isometrik-terang"` and every path value exists — as a script `tests/py/check_local_house.py` run manually (NOT discovered by unittest — file name must not start with `test_`, since it reads machine-specific paths). Expected error: `resolve` returns `None` → `AssertionError: no house standard resolved`.
2. Run `PY tests/py/check_local_house.py`, confirm failure. (The check script itself must not contain the absolute path: it takes the start dir as argv[1].)
3. Write `house-standard.md` JSON: `seller` `"INDUSIA.ai"`, `preset` `"isometrik-terang"`, `wordmark`/`logo` = the INDUSIA logo file in `/Users/alisadikin/Drive-D/pitch-deck/ref/` (ls the folder, pick the file named like `indusia*logo*`; if none or ambiguous STOP and ask Ali), `watermark` `"INDUSIA.ai"`, `band_text` `"RAHASIA · hanya untuk {client}"`, `site` `"www.indusia.ai"`, `phone` `"+62 813-6-811-811"`, `image_client` `"/Users/alisadikin/Drive-D/claude-plugin/geminigen-api-client"`, `image_model` `"nano-banana-pro"`, `image_mode` `null`, `style_refs` = one generic isometric illustration from `/Users/alisadikin/Drive-D/pitch-deck/Ekaputra-Dinata-Utama/renders/v2-ilustrasi/` (pick a warehouse scene without client marks; ask Ali if unsure), `language` `"Indonesian"`. Prose above the block in plain Indonesian: what this file is, which preset it picks, what still gets asked per client.
4. Write `context-sources.md`. Run the check script, confirm pass.
5. Edit the skills/reference/docs/CLAUDE.md/plugin.json/README as listed. Run `bash tests/run-all.sh` (guard must stay green — no path or seller name in skills/references).
6. Commit (plugin repo only): `docs(catalog): skills use deckkit prompts/gen + house standard; 0.9.0 (CAT-2)`

**Verification:**
- [ ] `PY tests/py/check_local_house.py /Users/alisadikin/Drive-D/pitch-deck/Ekaputra-Dinata-Utama` passes
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] `grep -c 0.9.0 .claude-plugin/plugin.json README.md` ≥ 1 each
- [ ] No placeholder/TODO comments in new code

### Phase Q: Penutup — end-to-end check and review

**Estimated time:** 15 minutes

**Files:**
- Create (scratch, outside repo): an end-to-end run dir in the session scratchpad

**Steps:**
1. Write failing end-to-end test as a shell sequence in the scratch dir: a 2-slide `slides.json` (generic text) → `PY -m tools.deckkit prompts slides.json` (house resolved via `--house /Users/alisadikin/Drive-D/pitch-deck/ref/house-standard.md`) → expect `prompts/slide-01.md`, `slide-02.md`, `manifest.json`. Before Phase D–F exist this fails with `invalid choice: 'prompts'`; now it must pass. Then `deckkit band`, `deckkit pdf --watermark ...` on two synthetic PNGs → one PDF with 2 pages.
2. Run it, confirm pass.
3. Ask Ali via AskUserQuestion whether to spend one real image render: `deckkit gen manifest.json --only 1 --ver e2e`. Yes → run, open the PNG (Read tool), report. No → record `real render: NOT RUN — Ali declined` in ledger.
4. Run review agent ONCE for the whole branch: `silent-failure-hunter` (model opus, effort high) over `git diff 20b9232..HEAD -- tools/`. Fix CONFIRMED findings with a test each.
5. `bash tests/run-all.sh`, `PY -m unittest discover -s tests/py -t . -v`, `graphify update .` (if `graphify-out/` exists).
6. Commit any fixes: `fix(deckkit): review findings (CAT-2)`. Do not merge — hand to `gaspol-finish`.

**Verification:**
- [ ] End-to-end sequence passes; PDF has 2 pages
- [ ] Real render result or `NOT RUN — Ali declined` recorded
- [ ] silent-failure-hunter findings fixed or recorded in `## Utang terbuka`
- [ ] `PY -m unittest discover -s tests/py -t . -v` passes
- [ ] `bash tests/run-all.sh` prints `ALL GREEN`
- [ ] No placeholder/TODO comments in new code

## Out of scope

- The 12 one-off scripts (`EKA/susun_19.py`, `EKA/tambal_15.py`, `MONI/render/tools/badge.py`, `build_v5.py`, `unflag_arc1.py`, `MONI/brd/render/build.py`, `CAT0/stamp_office.py`, `CAT0/revisi_2026_09_15.py`, `C3/finalize.py`, `C3/tambal.py`, `SPS/tempel_14.py`, `SPS/tempel_15.py`) stay in their folders; only their generic helpers are ported (Phases G–O).
- Video scripts (`video/`, `video-v3/`, `catalog-2/`, `catalog-4/`) — belong to `vidkit`.
- A MONI-style preset.
- Deleting or editing anything in client folders.
