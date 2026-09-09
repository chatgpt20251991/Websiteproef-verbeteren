# V2: correctie van nauwelijks zichtbare animatie

**Nieuwe bewegingspreview en broncode. Niet live. Geen volledige 3D- of native-4K-rebuild.**

## Geconstateerd probleem
De oude homepagepreview is daadwerkelijk opnieuw gerenderd. Bij 350 pixels scrollen verschoof het grote beeld slechts 5,20 pixels (transform y 1,87 naar 7,07 in het testvenster 1440 x 1000). De oude MP4 was 10 seconden bij 16 fps en liet hoofdzakelijk paginascroll zien. Een gewijzigde transformstring was dus onvoldoende bewijs van de visuele impact die de gebruiker vroeg. De gebruikersinstelling voor minder beweging is onbekend en wordt niet als oorzaak aangewezen; die zou de MP4-klacht niet verklaren.

## V2
De bestaande AI-illustratie wordt in SVG opgesplitst in de AI-module en het bedienpaneel. De delen bewegen afzonderlijk naar buiten en omhoog, met tegengestelde lichte rotaties. Drie verbindingen volgen de beide uiteinden. Het zijn geknipte afbeeldingslagen, geen geanimeerd 3D-model. Geen nieuwe afbeelding gegenereerd of bronfoto opgeschaald.

De zelfstandige preview opent direct met de grote bewegingsdemo, een zichtbare Speel animatie/Pauzeren-knop, status en toetsenbordbedienbare schuifbalk. De pagina hoeft niet te scrollen om de beweging te kunnen zien. Bij normale bewegingsvoorkeur speelt de preview automatisch. Bij reduced motion alleen na expliciete activering door de bezoeker; dat opt-in geldt uitsluitend voor de demo. Een knop schakelt terug naar de bestaande homepage. Daar volgt dezelfde AI-illustratie de scrollpositie en blijft reduced motion gerespecteerd.

## Toepassen
Laad assets/avenzo-motion-v2.css na de bestaande V1/brand CSS en assets/avenzo-motion-v2.js na V1 JS, met defer. Behoud bestaande routes, teksten, beelden, lettertypen, mail en formulier. De focus-demo verschijnt uitsluitend wanneer meta name=avenzo-preview bestaat. Zet die meta-tag NIET op de publieke site: daar alleen de bestaande AI-dienstillustratie uitbreiden.

De huidige V1-buildworkflow voegt de V2-includes nog niet automatisch toe. De oude V1-artifact is dus niet deze correctie. Gebruik de nieuwe bestanden en controleer in de oorspronkelijke Sites-preview. Deze wijzigingen publiceren niets.

## Werkelijk gecontroleerd
Lokale Chromium-rendering op 390 x 844, 1440 x 900 en 3840 x 2160. Op een STILSTAANDE pagina veranderde de horizontale positie van de linker module met circa -26/-80/-98 pixels en het paneel met +18/+55/+67 pixels. Een vergelijking van de gerenderde afbeelding bevestigde gewijzigde pixels, niet alleen andere CSS. Play/pause, toetsenbordschuifbalk, volledige homepage, mobiel menu, scrollbesturing, reduced motion inclusief expliciet preview-opt-in, geen-JS-fallback en teardown gecontroleerd. Geen JavaScript-fouten in die controles.

De nieuwe MP4 is 1440 x 900, circa 12 seconden, gerenderd vanuit de echte preview. De pagina bleef stilstaan (scrollY=0). De uiteindelijke MP4-frames zijn visueel bekeken; tussen 0,6 en 2,4 seconden veranderde 27,4% van de gecontroleerde beeldregio significant. Geen 60fps-, Safari-/Firefox-, native-4K- of echte-apparaatprestatieclaim. Geen fonts meegestuurd.

De overdracht in de chat bevat Avenzo_bewegende_preview_V2.html, Avenzo_beweging_V2.mp4 en Avenzo_beweging_V2_code_en_preview.zip met tests en meetrapporten. De eerdere V1-bewegingslaag voor overige onderdelen blijft bestaan. Niet alle beelden zijn als los bewegende 3D-objecten nagebouwd; de 4K-bronbeelden en publicatie blijven open.
