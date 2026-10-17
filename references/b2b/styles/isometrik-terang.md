# Style preset: isometrik-terang

A bright, clean corporate look for B2B offer decks. Isometric 3D clay illustration on a
light warm-grey page, navy headlines, teal as the main accent. Read by
`tools/deckkit/prompts.py` through `house.load_preset("isometrik-terang")`.

The seller's name is never written here. The preset uses `{seller}`, `{language}`,
`{audience}` and `{ai}` placeholders; the house standard and the deck spec fill them.

```json
{
  "name": "isometrik-terang",
  "intro": "A finished 16:9 presentation slide in {language} for a B2B offer from {seller} to {audience}.",
  "style": "STYLE: bright, clean corporate slide. Background light warm grey #f3f6f5 unless the layout says otherwise. Headlines deep navy #15212b; accent teal #23857f; second accent amber #a8712a; steel blue #2c5d99; issue slides use burnt orange #b8561a for eyebrow and bars; body grey #44545e. Illustration: clean isometric 3D, soft matte clay, soft shadows, same look as the style reference image. Headline in a bold condensed sans-serif; body in a clean sans-serif; crisp, left-aligned, high contrast, readable on a phone. Use the first reference image ONLY for the exact {seller} wordmark. Use the second reference image ONLY as the style source, do not copy its objects.",
  "guard": "RULES: The words before each colon are layout instructions and are never printed; only the strings between straight double quotes print. Each quoted string prints exactly once, spelled exactly, every digit exact. No other words, numbers or labels anywhere. No English words unless quoted. No people, no faces, no hands. No chart axes with numbers. Documents, receipts, papers, signs and boxes are blank: plain lines or plain shapes only, never letters. The only other lettering allowed is the {seller} wordmark on app screens{ai}. No other logos or brand names. Do not add decorative blocks or shapes that are not described. Keep every line of text in its own clear space; illustrations never overlap text. Every object is sharp, solid and fully drawn: no blurred, ghosted, smeared or half-transparent objects, and nothing copied from the style reference image. Every magenta area is exactly as described: one flat, solid, bright magenta #ff00ff shape with sharp edges, no outline, no shading, no text, no letters and no icon inside; magenta is used nowhere else on the canvas, and no magenta area is added that is not described. Leave the bottom 3% of the canvas empty. Nothing clipped.",
  "ai_clause": " and the two letters AI on the AI chip or on a brooch badge",
  "people_clause_from": "No people, no faces, no hands. ",
  "people_clause_to": "No people other than the figures described. ",
  "text_header": "TEXT (print exactly these, verbatim, each once):",
  "roles": {
    "eye": "eyebrow, small caps teal",
    "eye_problem": "eyebrow, small caps burnt orange",
    "head": "headline, large bold navy",
    "foot": "small grey footer line at the bottom-left"
  },
  "palette": {
    "background": "#f3f6f5",
    "price_background": "#e6eeee",
    "navy": "#15212b",
    "teal": "#23857f",
    "amber": "#a8712a",
    "steel_blue": "#2c5d99",
    "burnt_orange": "#b8561a",
    "body": "#44545e"
  },
  "fonts": {
    "headline": "bold condensed sans (Oswald-like)",
    "body": "clean sans (Roboto/Inter-like)"
  }
}
```

## Palette

- Page: light warm grey `#f3f6f5`. Price and closing slides use `#e6eeee`.
- Headlines: deep navy `#15212b`. Body text: grey `#44545e`.
- Main accent: teal `#23857f`. Second accents: amber `#a8712a` and steel blue `#2c5d99`.
- Problem slides swap the eyebrow and the bars to burnt orange `#b8561a`.
- Magenta `#ff00ff` is a working colour for empty slots (photo wells, logo slots). It is
  pasted over after render and appears nowhere in the finished deck.

## Illustration

- Clean isometric 3D, soft matte clay, soft shadows.
- One style reference image sets the look; the generator copies the look, never the objects.
- Objects are sharp, solid and fully drawn. No blur, no ghosting, no half-transparent shapes.
- No people, faces or hands unless a slide says so (`people: true`).
- Documents, signs and boxes stay blank. Any real lettering is added in post.

## Type

- Headline: bold condensed sans-serif, large, navy.
- Body: clean sans-serif, left-aligned, high contrast, readable on a phone.
- Eyebrow: small caps above the headline, teal on solution slides, burnt orange on problem slides.

## Layout grammar

- Eyebrow above headline. Teal on solution slides, burnt orange on problem slides.
- Body: illustration on the left, 55 to 65 percent of the width (62 percent is typical).
  Text column on the right, 35 to 45 percent, with 3 or 4 points. Each point is a bold
  title plus a grey detail line, and each has a coloured left bar. The bar is burnt orange
  on problem slides and matches the illustration's colour on solution slides.
- Cover: text on the left 40 percent, illustration on the right 60 percent, with a
  tricolour stripe (steel blue, teal, amber) along the top edge.
- Proof slide: dark navy `#15212b` background, white and teal text.
- Price and closing slides: `#e6eeee` background.
- Footer: a small grey line at the bottom-left for the source or `ILUSTRASI · ...`.
- The footer band and page numbers are composited after render, never drawn by the
  generator. The bottom 3 percent of the canvas stays empty for that reason.

## Slide variants

- Three equal columns.
- Two-by-two grid of rule cards.
- Ascending isometric steps.
- Pale full-width banner with a thick left bar.
- Numbered items in burnt-orange circles.

## When not to use

- The seller's own house standard asks for a dark, photographic or hand-drawn look.
- The deck needs real photography on most slides; this preset is built around illustration.
- The audience expects a formal print catalogue with dense tables and no illustration.
- A slide carries a dense data table: build it as a table page, not as an illustration.
