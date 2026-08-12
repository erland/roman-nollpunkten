# Publiceringsanteckningar

Det här projektet är anpassat till GitHub Actions-konceptet från Romanskaparens publiceringskit.

## Workflows

- `.github/workflows/01-validate.yml` kör snabb projektvalidering vid push/PR mot `main`.
- `.github/workflows/02-build-preview.yml` kan startas manuellt och bygger EPUB + PDF som ett gemensamt artifact: `nollpunkten-preview`.
- `.github/workflows/03-release.yml` körs på taggar `v*` och publicerar EPUB + PDF som separata GitHub Release assets.

## Bygge

Bygg lokalt med:

```bash
python3 scripts/validate_project.py .
python3 scripts/build_book.py --output-dir dist
```

Pandoc är låst till `3.1.11.1` i byggskriptet och i GitHub Actions.

## Projektanpassningar

- Titel: `Nollpunkten`
- Författare: `Erland Lindmark`
- Språk: `sv-SE`
- Omslagsbild används inte.
- Kapitel hämtas från `kapitel/kapitel-XX.md` i numerisk ordning.
- Kapitelnoteringar efter `---` exporteras inte.
