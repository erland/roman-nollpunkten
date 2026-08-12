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


## Fix 2026-08-12

Preview-bygget stoppade eftersom titelsidan fortfarande fanns i EPUB:ens TOC efter Pandoc-bygget. `publishing/fix-epub-after-pandoc.py` är nu uppdaterad så den inte längre letar efter en hårdkodad titel från mallprojektet, utan identifierar XHTML-filen som innehåller `<section class="title-page">` och tar bort motsvarande TOC-post oavsett filnamn eller titel.

## Fix 2 – robust TOC för titel som matchar kapitelrubrik

Preview kunde fortfarande falla eftersom kapitel 17 heter **Nollpunkten**, samma som boktiteln. Efterbearbetningen bygger nu om EPUB-navens TOC från faktiska XHTML-kapitel i spine-ordning i stället för att försöka ta bort titelsidan kirurgiskt. Det gör att kapitel 1–18 alltid finns kvar och att titelsidan inte visas i innehållsförteckningen.

## Fix 2b – PDF-template

Den anpassade LaTeX-mallen definierar nu Pandocs `\tightlist`, vilket krävs när Pandoc genererar kompakta listor i PDF-flödet.
