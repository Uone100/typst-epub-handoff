# Typst EPUB Handoff

Take a book from Typst to an EPUB 3 download, then compare its actual reading-order content with its HTML reference. The audit lists missing or reordered headings, changed math text, unmatched local illustrations and unresolved local links.

## Install as an Agent Skill

Download the **versioned ZIP** from [Releases](https://github.com/Uone100/typst-epub-handoff/releases/latest). Extract its contents into `.agents/skills/typst-epub-handoff/` in a Codex project or `.claude/skills/typst-epub-handoff/` in a Claude Code project. The installed folder should contain SKILL.md directly. Start a new session and ask for the task described above. You can also run the helper directly.

## Worked example

Typst with HTML export and Pandoc for conversion; Python 3.9+ standard library for the audit. An existing HTML/EPUB pair can be checked without either converter.

```sh
typst compile --features html examples/book.typ book.html
pandoc book.html --from=html --to=epub3 --mathml --metadata "title=Field Notes" -o book.epub
python scripts/compare_book.py book.html book.epub
```

Expected: pass, 2 source headings, 1 source equation. Exit 1 means review; 2 means an invalid input. Math comparison checks normalized text, not layout or mathematical equivalence. Image encoding changes and intentional substitutions require review. Source-local image matching covers img references within the HTML directory. For EPUB specification validation, use EPUBCheck as well.

## Why it exists

[116 👍 on the upstream EPUB export request](https://github.com/typst/typst/issues/188). Authors also discuss [asset and cross-page link handling](https://forum.typst.app/t/can-typst-produce-epub-format-document/7344) and [math on reading devices](https://forum.typst.app/t/how-to-pre-render-maths-to-images/6441). [typ2epub](https://github.com/IceySwan/typ2epub) already converts books; this Skill can independently check its output against equivalent source HTML. Reaction counts were observed on 2026-11-20. They measure interest in the upstream request. This specific Skill's adoption is measured separately through its Release attachment.
