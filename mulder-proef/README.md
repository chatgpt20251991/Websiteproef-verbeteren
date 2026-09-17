# Mulder-proef: installatie en uitvoering

Gecontroleerd op 17 september 2026. Dit document vervangt de installatie-instructie
uit de ZIP: werk via de branch `codex/mulder-mockup-proef` en een pull request.
Geen bestaande Avenzo-workflow wordt gewijzigd. Geen websitepublicatie of e-mail.

## Bestanden

- `.github/workflows/avenzo-mulder-mockups.yml`: afzonderlijke workflow.
- `mulder-referentie.png`: ongewijzigde aangeleverde referentie, 1536 × 1024.
- `mulder-proef/test_workflow.py`: reproduceerbare offline tests van de Python-code
  die rechtstreeks uit de workflow wordt gelezen.

Referentie SHA-256:
`327b76ead6cd4e00ad1ed77718efda6bfbf063c4eeb5d0fe5344b0767cffb3e6`.

## Kosteloze controle

Een push van de workflow of referentie op deze specifieke proefbranch voert alleen
`Controle` uit. De standaardinvoer is ook bij handmatig starten `Controle` met
kostenakkoord uit. Er is geen OpenAI-aanroep. De runner controleert het referentiebeeld,
de gekozen instellingen en uitsluitend of `AVIN2` niet leeg is. Beide opdrachten
worden ter beoordeling opgeslagen. Dit bewijst geen sleutelgeldigheid, modeltoegang
of beschikbaar saldo. De geheime waarde wordt nergens gelogd of opgeslagen.

De workflow koppelt uitsluitend `${{ secrets.AVIN2 }}` aan `OPENAI_API_KEY`.
Maak geen nieuwe sleutel en kopieer de bestaande waarde niet naar lokale bestanden.

## Eén betaalde proef, alleen na uitdrukkelijk akkoord

De proef staat voorbereid op:

| Instelling | Waarde |
| --- | --- |
| Taak | Desktop en mobiel |
| Model | gpt-image-2.5-sunburst |
| Endpoint | https://api.openai.com/v1/images/edits |
| Kwaliteit | max |
| Resolutie | 4K |
| Desktop | 3840 × 2160, één PNG |
| Mobiel | 1728 × 3840, één PNG |
| Maximum | Twee verzoeken achter elkaar, `n=1` per verzoek |
| Automatische herhalingen | Geen |

De API krijgt in elk verzoek hetzelfde referentiebeeld en een afzonderlijke opdracht.
De prompts behouden de donkere architectuurfotografie, warme verlichting,
champagneaccenten en typografie. Ze vragen twee losse vlakke webpagina's zonder
collage, toestelranden of decoratieve omgeving. De ontvangen PNG's worden niet
opgeschaald of nabewerkt. Vormgeving, leesbaarheid en feitelijke claims moeten na
ontvangst visueel worden beoordeeld; offline tests kunnen dat niet bewijzen.

Uitvoer boven QHD is volgens OpenAI experimenteel. `max` is ondersteund, maar
dit is geen hard budget in euro's of dollars. Werkelijke kosten hangen af van
input- en uitvoertokens. Geen kostenakkoord betekent geen beeldverzoek.

Na review en samenvoeging van de PR staat de workflow op `main`. GitHub vereist
dat voor `workflow_dispatch`. Kies in Actions de Mulder-workflow en de instellingen
hierboven; zet alleen na het afgesproken kostenakkoord `api_kosten_akkoord` aan.
Start precies één keer. Een eerdere betaalde run opnieuw uitvoeren wordt geweigerd
via `GITHUB_RUN_ATTEMPT`. Een volledig nieuwe handmatige start kan opnieuw kosten
maken en valt niet onder toestemming voor de eerdere proef.

Bij een fout, time-out of afwijkende afmetingen stopt de workflow direct. Een
time-out kan betekenen dat het verzoek al is verwerkt; niet opnieuw indienen
zonder het verbruik en de eerdere run te beoordelen en nieuw akkoord te krijgen.

## Resultaat

Het artifact `mulder-mockups` bevat de losse PNG's indien ontvangen, twee opdrachten,
`run-report.json` en een lokaal te openen `bekijken.html`. Bewaar het binnen 14 dagen.
Rapportage bevat het runnummer en de commit, nooit de secretwaarde. Een
`requests_submitted`-telling betekent een ingezette verzendpoging, geen bewijs
dat OpenAI het verzoek heeft verwerkt of gefactureerd.

## Zelf de offline tests uitvoeren

Installeer PyYAML 6.0.3 in een afzonderlijke testomgeving en voer vanuit de hoofdmap uit:

```text
python -m unittest discover -s mulder-proef -v
```

Tests gebruiken een duidelijk fictieve sleutel, gesimuleerde API-antwoorden en
een netwerkblokkade. De PNG-testbeelden zijn alleen testfixtures, geen mockupresultaten.
De productiecode gebruikt uitsluitend de Python-standaardbibliotheek.

## Actuele officiële bronnen

- [OpenAI image generation](https://developers.openai.com/api/docs/guides/image-generation):
  kwaliteitskeuzes, uitvoerafmetingen, PNG/base64 en experimentele resoluties.
- [OpenAI Sunburst model](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst).
- [OpenAI image edit API](https://developers.openai.com/api/reference/resources/images/methods/edit):
  multipart referentiebeeld, model, `n=1`, `quality`, `size`, `output_format`, `background`.
- [GitHub handmatige workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow):
  standaardbranch en schrijfrechten voor handmatig starten.

De meegeleverde claim van 29 geslaagde tests is niet als bewijs overgenomen.
De installatie heeft een eigen controle uitgevoerd. Zie het afzonderlijke
opleverrapport voor werkelijk uitgevoerde tests, GitHub-run en openstaande stappen.
