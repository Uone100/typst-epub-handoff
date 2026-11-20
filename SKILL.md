---
name: typst-epub-handoff
description: Deliver a reflowable EPUB from a Typst book and check the result against its HTML export for chapter order, inline MathML, image coverage and local link targets. Use when an author needs a repeatable handoff to an e-reader.
---
1. Compile the user's existing Typst entry file to HTML with their installed Typst CLI (`typst compile --features html book.typ book.html`, enable HTML only if required by that version). Keep the project's assets alongside that HTML. If compilation or a feature is unsupported, capture the diagnostic. Confirm the HTML itself shows the intended headings, equations and illustrations.
2. From the HTML directory run Pandoc, e.g. `pandoc book.html --from=html --to=epub3 --mathml --metadata title="Book title" -o book.epub`. Use a fresh output pathname. If the author uses another EPUB converter, keep it and use the audit step against the equivalent HTML.
3. Run `python scripts/compare_book.py book.html book.epub`. Inspect reported missing headings, changes in math token sequence, image totals and unresolved internal targets in reading order. Fix the export and rerun. For intentional changes record the exception, especially equations explicitly converted to illustrations.
4. Use EPUBCheck when formal EPUB conformance is part of acceptance. Preview at two font sizes on the intended reader before claiming device compatibility. This comparison starts at the HTML export, so losses that already occurred while compiling Typst need source review.
