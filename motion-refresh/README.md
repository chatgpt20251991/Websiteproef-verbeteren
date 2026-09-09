# Avenzo: motion op de bestaande website

**Gebouwd als eerste bewegingsversie. Niet live gepubliceerd. Geen volledige native-4K- of 3D-robotversie.**

De bestaande negen pagina's, teksten, navigatie, afbeeldingen en mailto-formulierwerking blijven de basis. De eerder goedgekeurde branding wordt tegelijk meegenomen via `brand-refresh`.

## Gebouwd

Scrollgestuurde hero/parallax, beperkte bewegende typografie, perspectiefkanteling van bestaande dienstbeelden, een SVG-lichtspoor over de drie verbindingen in de AI-afbeelding, desktop pinned storytelling met de bestaande softwareafbeelding en drie processtappen, scroll reveal en knop-/pijlinteracties. Native scrollbediening, lichtere mobiele beweging, OS reduced-motion ondersteuning en een pauzeknop. De renderlus stopt bij stilstand. Geen externe runtimebibliotheken, tracking, mailacties of scroll hijacking.

De oorspronkelijke foto's zijn nog steeds foto's. Deze CSS 2.5D-effecten zijn geen onafhankelijk draaiende onderdelen, geen WebGL-model en geen scrollgestuurde video-/framereeks. Die zwaardere productanimatie is niet gebouwd.

## Gemeten beeldkwaliteit

De publieke site is op 9 september 2026 rond 15:42 UTC opnieuw gelezen via Actions-run 34371985953. Van 32 gekoppelde assets zijn de rasterafmetingen gemeten. Hero maximaal 1672 x 941; mobiele hero 1106 x 1422; dienstbeelden 1586 x 992; softwareclose-up 1672 x 941. In de gecontroleerde pagina's zijn geen gekoppelde GLB/GLTF-modellen of framereeksen gevonden. Ongepubliceerde originelen in de Work-omgeving kunnen wel bestaan.

Een 3840 x 2160-testvenster maakt een 1672px-foto niet native 4K. Vectorlogo's en tekst schalen mee, maar bestaand fotodetail wordt niet door CSS teruggewonnen. `build_media.py` kan echte grotere originelen naar responsive WebP-varianten omzetten, van 640 tot 3840px. Het vergroot nooit een te kleine bron. Deze pipeline is nog niet op echte 4K-originelen uitgevoerd. Originele srcsets blijven behouden.

## Toepassen

Laad `assets/avenzo-motion-20260909.css` NA bestaande site-CSS en brand-refresh CSS; laad de JS met `defer`.

```sh
python3 motion-refresh/apply.py --source /pad/naar/bestaande-html --output /pad/naar/lege-patchmap
```

De output is een PATCH, geen complete website. Behoud overige assets, fonts, routes en formuliercode. Gebruik bij voorkeur de oorspronkelijke gedeelde templates. De builder verifieert dat de volledige main-inhoud ongewijzigd blijft en weigert onbekende templates. Brand-refresh verwijdert de bekende per-request Cloudflare-injectie; publiceer geen ruwe netwerksnapshot blind.

Alleen publiceren in de bestaande bevoegde Sites-omgeving, na previewcontrole. Deze branch en de Actions-workflows publiceren niets. Geen nieuwe site, DNS-, domein- of mailwijzigingen. Behoud de vorige Sites-versie voor rollback.

## Werkelijk getest

Lokale Chromium-preview: 14 geslaagde browsergevallen. 390px/DPR3, 1440px en 3840 x 2160; geen horizontale overflow of JavaScript-excepties in die controles. Scrollreactie, pauzeknop, mobiel menu, alle negen routes, accordeons, bestaand formulier, reduced motion inclusief runtimewijziging, geen-JS-fallback en teardown gecontroleerd. Typografie in de offline preview gebruikt de systeemfallback; geen fonts meegestuurd. Geen Safari-/Firefox-certificering, gemeten 60fps, Core Web Vitals-score of bugvrijheidsclaim.

10 nieuwe unittests en 13 bestaande brand-refresh-tests geslaagd in de lokale uitvoering. Reproduceer de unittests met:

```sh
python3 -m unittest discover -s motion-refresh/tests -p 'test_*.py' -v
python3 -m unittest discover -s brand-refresh/tests -v
node --check motion-refresh/assets/avenzo-motion-20260909.js
```

Pillow is nodig voor de optionele beeldpipeline en tests, niet voor de website. Browsercheck-broncode, volledige meetrapporten, offline preview en opname zijn meegeleverd in het overdrachtpakket.

## Terugzetten

Verwijder de twee motion-includes en hun bestanden. Of pauzeer tijdelijk met `AvenzoMotion.pause()`. `AvenzoMotion.destroy()` verwijdert de toegevoegde laag tijdens een paginabezoek. De goedgekeurde branding kan afzonderlijk behouden blijven.
