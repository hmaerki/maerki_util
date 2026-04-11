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
    * bestellung.json
    * bestellung.pdf

### Workflow optional

Falls Anzahl angepasst werden muss.

* Von Hand: bestellung.json editieren
* terminal: `./run_json_update.sh`
