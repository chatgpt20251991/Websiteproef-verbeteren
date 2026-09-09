# Avenzo: directe mailtoegang controleren

## Status en afbakening

Deze map bevat een **verbindingstest**, niet een actieve mailkoppeling voor ChatGPT of een automatische antwoorddienst. De website en de bestaande ChatGPT-opvolgtaak worden niet gewijzigd. Groene offline tests betekenen niet dat de mailbox live is aangesloten.

De check gebruikt uitsluitend `info@avenzodigital.nl`, de Vimexx-server `mail.zxcs.nl`, IMAP 993 en SMTP 465 met verplichte TLS-certificaat- en hostnaamcontrole. Zij meldt alleen of inloggen en readonly INBOX-toegang lukken. Geen berichten of headers worden opgehaald; niets wordt als gelezen gemarkeerd, verwijderd, doorgestuurd of verstuurd. Providerfoutteksten, aantallen berichten en wachtwoorden komen niet in het rapport.

## Eenmalig veilig activeren voor een verbindingstest

1. Open in deze repository **Settings > Secrets and variables > Actions > New repository secret**.
2. Naam: `AVENZO_MAIL_PASSWORD`. Waarde: het bestaande wachtwoord van **de mailbox** `info@avenzodigital.nl`, niet van het Vimexx-klantenaccount. Zet het nooit in chat, een issue, broncode of een gewone repository variable.
3. Open **Actions > Avenzo mailbox connection preflight > Run workflow**. Selecteer `main` en schakel `live_login` in. De standaardinstelling is uit.
4. Bekijk de job `mail-login`. `authenticated` betekent alleen geslaagde IMAP/SMTP-authenticatie. `blocked` betekent dat de credential ontbreekt; `failed` betekent dat een check faalde. Er is nog geen bezorgtest of automatische antwoorddienst geactiveerd.

Deze repository is publiek. De broncode is openbaar; een GitHub Actions-secret is dat niet. Vertrouw alleen repositorymedewerkers die de mailbox ook zouden mogen benaderen: iemand met schrijfrechten kan workflows veranderen en zo secrets gebruiken. Voeg geen klantmails of mailboxexports toe aan deze repository of aan openbare logs. Verwijder het secret na een eenmalige controle wanneer er geen vervolgtoegang nodig is.

## Wat nog apart moet worden afgerond

- Een daadwerkelijke, beveiligde IMAP/SMTP-adapter of ondersteunde mailbox-app beschikbaar maken aan het uitvoerende mailsysteem. Deze preflight is geen MCP-server en voegt geen ChatGPT-app toe.
- De al bestaande opvolgtaak controleren en zo nodig aanpassen; niet zomaar een tweede taak maken. Haar actuele status en volgende uitvoering moeten in taakbeheer worden geverifieerd.
- Alleen echte reacties op aantoonbaar door de assistent verstuurde zakelijke mails beantwoorden. Een SENT-label alleen bewijst die herkomst niet. Bestaande gesprekken blijven via de zakelijke Gmail lopen; nieuwe klantmails uitsluitend vanuit het zakelijke domeinadres na geslaagde aansluiting. Geen antwoord bij stilte, afwijzing, afmelding, automatische melding of al afgehandelde vraag.
- Het publieke contactformulier is in de snapshot van 9 september een eerlijk gelabelde mailto-hulp: het opent het mailprogramma en verstuurt niet zelf. Een server-side formulier vereist een apart beveiligd verzendpunt, validatie, antimisbruik, foutafhandeling en publicatie in de oorspronkelijke bouwomgeving.

## Lokaal testen

Python 3.10 of hoger; geen aanvullende packages nodig:

```sh
python3 -m unittest discover -s tests -v
```

De tests gebruiken uitsluitend mocks. Een lokale echte login kan met `AVENZO_MAIL_PASSWORD` in een beschermd procesenvironment en `python3 operations/check_mail_connection.py`. Gebruik nooit een wachtwoord als commandoregelargument of in een gedeelde terminalgeschiedenis.

## Bronnen

- Vimexx, serverinstellingen en versleutelde poorten: https://www.vimexx.nl/help/email-instellingen-imap-pop3-smtp
- GitHub, gebruik van Actions-secrets: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets
- OpenAI, beheren van bestaande geplande taken: https://help.openai.com/en/articles/10291617-scheduled-tasks-in-chatgpt

De check verandert geen DNS, hosting, mailboxinstellingen, publicatie of taakplanning.
