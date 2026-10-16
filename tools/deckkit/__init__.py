"""deckkit: post-render tooling for catalog / offer decks (PDF, watermark, numbering, footer band,
text patching, logo slots, footer erase). Pillow required; numpy for patch/watermark; cv2 +
tesseract for erase and slots; python-pptx for pptx.

CLI: ``python3 -m tools.deckkit --help`` from the plugin root.
"""
