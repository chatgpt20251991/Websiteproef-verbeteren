# Goedgekeurde Avenzo-header en footer

**Status: gebouwd als uitvoerbare HTML/CSS-wijziging. Niet gepubliceerd.**

Dit is de implementatie van het in het Avenzo-project goedgekeurde logo en mobiele contact-/footerontwerp, geen nieuwe ontwerpronde. Het logo is een compacte vectorconversie van het goedgekeurde beeldbestand; er is geen ander lettertypewoordmerk bedacht. Bordeaux in de header, wit in de footer.

## Werkelijke wijzigingen

- Nieuw woordmerk bovenaan en onderaan, met vaste beeldverhouding om verspringen te voorkomen.
- De goedgekeurde projectuitnodiging en knop naar `/contact/`.
- Gelabelde contactregels, lijniconen en subtiele scheidingen: Projectaanvragen / info@avenzodigital.nl; Algemene vragen / avenzodigitalgroup@gmail.com; KvK / 94554692.
- Tagline, studiolink en afsluitende regel. Geen verzonnen LinkedIn-/Instagram-links; alleen het echte e-mailicoon is actief.
- Op mobiel gestapeld; op breed scherm contactgegevens in drie kolommen. Lange adressen kunnen bij zeer smalle schermen of vergroting netjes afbreken.

De bestaande teksten in `<main>`, navigatie en contactformulier-JavaScript worden niet gewijzigd. De mailto-werking van het formulier wordt door deze ontwerppatch niet veranderd.

## Toepassen in de bestaande bouwomgeving

Werk in de oorspronkelijke Avenzo-site, niet in een nieuw aangemaakte site. De bestaande domeinkoppeling wijst naar ChatGPT Sites. GitHub is hier nog geen publicatiekoppeling.

Neem `footer.html` en de headerwijziging uit `apply.py` over in de oorspronkelijke gedeelde layout/template. Voeg de twee bestanden uit `assets/` toe en laad de CSS na de bestaande site-CSS. Wanneer de bron uit statische HTML bestaat, kan de patch eerst veilig in een aparte map worden opgebouwd:

```sh
python3 brand-refresh/apply.py --source /pad/naar/bestaande-html --output /pad/naar/nieuwe-lege-stagingmap
```

De stagingmap is een **patch**, niet een volledige website-export: bestaande afbeeldingen, fonts, CSS en JavaScript blijven nodig. Vervang niet de volledige website door deze patchmap. De oorspronkelijke `recovery/`-bestanden in deze repository blijven ongewijzigd.

## Controleren en publiceren

```sh
python3 -m unittest discover -s brand-refresh/tests -v
```

De workflow `Validate approved Avenzo brand refresh` leest de huidige negen publieke pagina's, maakt aangepaste HTML-kandidaten en controleert logo's, mailadressen, KvK en behoud van `<main>`. Hij kan een patchartefact opleveren; hij publiceert niets en heeft geen hostingrechten.

Publiceer na de previewcontrole **de bestaande Site** vanuit ChatGPT Sites. Controleer vervolgens op zowel het hoofddomein als www dat de nieuwe versie wordt geserveerd. Een succesvolle Actions-run is geen livegang. Voor rollback: herpubliceer de eerdere Sites-versie. Wijzig geen DNS, domein, mail of afzenderinstellingen voor deze ontwerptaak.
