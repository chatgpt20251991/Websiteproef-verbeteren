# Avenzo Digital — publicatiecontrole en herstelkopieën

## Status op 9 september 2026

Deze repository was bij aanvang van de controle leeg. Zij bevat nu openbare controles en kopieën van een deel van de gepubliceerde website. **Dit is niet de volledige oorspronkelijke projectmap en er is geen automatische deployment ingesteld.**

## Vastgestelde bereikbaarheid

De eenmalige GitHub Actions-controle van 9 september 2026 om 04:27 UTC leverde op:

| Adres | Waarneming |
| --- | --- |
| https://avenzodigital.nl/ | HTTP 200 via HTTPS; titel `Van visie. Naar voorsprong. \| Avenzo Digital` |
| https://www.avenzodigital.nl/ | HTTP 200 via HTTPS; dezelfde titel |
| http://avenzodigital.nl/ | Doorgestuurd naar HTTPS op hetzelfde domein |
| http://www.avenzodigital.nl/ | Doorgestuurd naar HTTPS op hetzelfde domein |
| https://avenzo-digital.ll33555555.chatgpt.site/ | HTTP 200 via HTTPS; dezelfde titel |

De latere herstelkopie bevestigde ook HTTP 200 voor `/contact/` en de hieronder genoemde CSS en JavaScript. De footer bevat beide zakelijke e-mailadressen en KvK 94554692. Tijdens deze werkzaamheden zijn DNS, hosting en live website-inhoud niet gewijzigd.

Ruwe broncontrole: [diagnostic run 34311016187](https://github.com/chatgpt20251991/Websiteproef-verbeteren/actions/runs/34311016187).

## Inhoud

- `.github/workflows/avenzo-diagnostics.yml`: alleen-lezen controle van openbare DNS en HTTP.
- `.github/workflows/avenzo-homepage-backup.yml`: kopieert geselecteerde publiek geserveerde HTML, CSS en JavaScript naar deze repository; schrijft niet naar hosting.
- `recovery/published-homepage.html`: momentopname van de homepage.
- `recovery/published-contact.html`: momentopname van de contactpagina.
- `recovery/published-app.js`: gepubliceerde JavaScript.
- `recovery/published-site.css`: gepubliceerde CSS.
- `recovery/public-text-backup-observations.json`: tijdstippen, bronadressen, HTTP-statussen, hashes en opslagcommits.

De workflows hebben **geen terugkerend tijdschema**. Zij starten bij een wijziging aan hun eigen workflowbestand of via een handmatige start. De herstelkopie-workflow gebruikt uitsluitend het automatische repositorytoken voor het opslaan van openbare bestanden in deze repository.

## Contactformulier: werkelijk gedrag

De op 9 september gelezen HTML en JavaScript tonen dat het contactformulier een `mailto:info@avenzodigital.nl`-bericht samenstelt. De bezoeker moet dit zelf versturen vanuit zijn of haar mailprogramma. Er is ook een knop om de aanvraagtekst te kopiëren. De pagina vermeldt expliciet dat zij de gegevens niet verstuurt of opslaat.

Dit is **geen zelfstandig verzendend contactformulier**. Een mailto-koppeling bewijst geen e-mailbezorging. De mailbox achter het adres en geautomatiseerde mailverwerking zijn afzonderlijke onderdelen en zijn niet door deze workflows geconfigureerd of getest.

## Belangrijke grenzen

1. HTTP 200 en een juiste titel bewijzen bereikbaarheid op het controlemoment, geen volledige functionele, mobiele, toegankelijkheids- of beveiligingsaudit.
2. Aanwezigheid van mail-DNS-records bewijst geen ingelogde IMAP/SMTP-toegang of actieve mailboxopvolging.
3. De herstelkopieën zijn door de server geleverde bestanden, niet de oorspronkelijke templates, buildconfiguratie, backend of volledige broncode.
4. Afbeeldingen en lettertypebestanden zijn niet gekopieerd. Verwijzingen naar assets blijven afhankelijk van de bestaande hosting. Het back-uppakket is daardoor niet zelfstandig inzetbaar als volledige website.
5. De HTML kan scripts bevatten die door de publicatie/CDN-laag zijn toegevoegd. Publiceer deze momentopnamen niet blind als oorspronkelijke broncode.
6. Bewaar hier geen mailboxwachtwoorden, API-sleutels, klantmails, privé-uitvoeringslogs of persoonsgegevens. Deze repository is openbaar.

## Vervolg bij toegang tot de oorspronkelijke bouw- en hostingomgeving

Exporteer de echte projectmap naar een passende, bij voorkeur private broncoderepository. Behoud het bestaande ontwerp. Koppel alleen een deployment nadat bouw, assets, routes en een herstelmogelijkheid zijn gecontroleerd. Een zelfstandige contactverzending vraagt een apart beveiligd serverendpoint en een daadwerkelijke bezorgtest; pas het huidige formulier niet aan alsof die functie al bestaat.
