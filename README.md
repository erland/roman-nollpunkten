# Nollpunkten

Detta är projektarkivet för romanprojektet **Nollpunkten**.

## Rekommenderat arbetsflöde

1. Planera romankärnan: huvudperson, mål, hinder, insats och förändring.
2. Skapa synopsis, kapitelplan, romanbibel och stilguide.
3. Skriv ett kapitel i taget i chatten.
4. Justera kapitlet tills användaren är nöjd.
5. Uppdatera projektfilerna och projektstatus.
6. Fortsätt med nästa kapitel eller revision.

## Viktiga filer

- `projektstatus.md` visar nuvarande fas, senaste godkända kapitel och nästa rekommenderade steg.
- `roman-bibel.md` innehåller projektets centrala fakta.
- `synopsis.md` sammanfattar hela handlingen.
- `kapitelplan.md` är färdplanen för romanen.
- `stilguide.md` håller språk, ton och perspektiv konsekvent.
- `tidslinje.md` håller ordning på händelser.
- `kontinuitetsanteckningar.md` fångar fakta som inte får motsägas.
- `revisionsonskemal.md` samlar planerade förbättringar.
- `arbetslogg.md` visar vad som har gjorts.
- `kapitel/` innehåller kapitelutkast och godkända kapitel.

## GitHub Actions och publicering

Projektet innehåller nu ett GitHub Actions-upplägg för validering och reproducerbar publicering.

- `.github/workflows/01-validate.yml` validerar projektstruktur och kapitel vid push/PR mot `main`.
- `.github/workflows/02-build-preview.yml` kan startas manuellt och bygger EPUB + PDF som ett gemensamt preview-artifact.
- `.github/workflows/03-release.yml` körs vid taggar som börjar med `v` och publicerar EPUB + PDF som separata release assets.
- `scripts/validate_project.py` kontrollerar kapitelserie, rubriker, metadata och projektfiler.
- `scripts/build_book.py` bygger EPUB/PDF från `kapitel/kapitel-XX.md` i numerisk ordning.
- `publishing/metadata.yaml` innehåller titel, författare och språk för publicering.

Bygg lokalt med:

```bash
python3 scripts/validate_project.py .
python3 scripts/build_book.py --output-dir dist
```
