# Export a Typst sample book and check its EPUB

You will make an EPUB 3 from a short book and check whether its two headings and one equation survived conversion.

## Run a complete handoff

Download the named ZIP under **Assets** on the [release page](https://github.com/Uone100/typst-epub-handoff/releases/latest). Extract the ZIP and open a terminal in the directory containing `SKILL.md`. Install Typst with HTML export, Pandoc and Python 3.9 or newer. Check that `typst --version` and `pandoc --version` run. Use a fresh working directory for the generated book files.

```sh
typst compile --features html examples/book.typ book.html
pandoc book.html --from=html --to=epub3 --mathml --metadata "title=Field Notes" -o book.epub
python scripts/compare_book.py book.html book.epub
```

Read the JSON report. For the bundled book, `result` should be `pass`, `reference_headings` should be 2 and `reference_equations` should be 1. Open `book.epub` in your target reader to check the appearance of the equation.

## Check a real book

Replace the sample Typst path and title with your own. Keep any images referenced by the HTML next to it at their original relative paths. If you already have matching HTML and EPUB files, run only the final command.

Exit code 1 means the comparison found a difference. Review the identified content in both files, correct the source or conversion setting, and run the audit again. Exit code 2 indicates an input problem such as a missing or invalid file. Intentional image re-encoding can also require inspection. The check compares book content; use EPUBCheck separately for EPUB conformance.

## Ask an agent

Follow the [README](README.md) to install the Skill. Try “Compare this reference HTML with this EPUB in spine order and show me any heading, math, illustration or local-link differences.” Provide both file paths.
