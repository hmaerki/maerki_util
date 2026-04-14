# Klangspiel Rechnung 2026

run_klangspiel_rechnung2026.sh

```bash
#!/bin/bash
uv run --with=git+https://github.com/hmaerki/maerki_util.git@main klangspiel_rechnung2026 clipboard
```


## Workflow

* Email öffnen, xml in clipboard kopieren

* terminal, Ordner buchhaltung: `run_klangspiel_rechnung2026.sh`

* `./run_klangspiel_rechnung2026.sh`:
  
  * 'copied xml successfully'
  * 'Rechnung: ' `Nr. 20260303_01`
  * 'Zahlung erhalten [y/n]: ' `y`

  Nun wird ein Ordner erstellt:

    * run_json_update.sh
    * original.json
    * xy_bestellung.pdf

### Workflow optional

Falls Anzahl angepasst werden muss.

* Von Hand: original.json editieren
* terminal: `./run_json_update.sh`

Beispiel original.json

```json
{
  ...
  "ftotal": "116.00",  # NICHT anpassen. Rechnung liest berechneten Wert
  "ftotalmwst": "0.15",   # Anpassen.

  "positionen": [
    {
      "anzahl": "1",  # Anpassen
      "wo": "U62",  # Anpassen
      "unit": "Stück",  # Anpassen
      "text": "www.klangspiel.ch/unikat/briefmarken#d4842 ",
      "preis": "57.00"  # Anpassen
    },

```
