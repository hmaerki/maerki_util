# Neuimplementierung für Linux

## Bestehende Lösung

https://github.com/hmaerki/privat_svn_hans/tree/main/klangspiel/trunk/Verkauf/rechnung_verschickt

[Beispielrechnung](../rechnung_verschickt/z_rechnung_vorlage_webshop_excel.beispielbestellung.txt)

[Windows Doc Barcode](../rechnung_verschickt/z_vorlage_etikette_barcode.doc)


[VB schweiz](../rechnung_verschickt/z_vorlage_schweiz.doc)
[VB ausland](../rechnung_verschickt/z_vorlage_ausland.doc)

[Windows Docm](../rechnung_verschickt/z_vorlage_schweiz.docm)

### Workflow bisher

* z_vorlage_schweiz.docm: öffen

  * XML hineinkopieren
  * Button `[GO]`

    * Im Dokument wird der XML-Teil gefunden
    * Aufgrund des XML dokuments wird ein ASCII body zusammengestellt.
    * Das email wird versandt indem Thunderbird gestarted wird

  * Schweiz

    * Rechnung erstellen
    * Vorauskasse erstellen
    * Zahlung erhalten - Mahnstufen

  * Ausland
    * Rechnung erstellen

### Workflow neu

* bestellung.xml

  * run_klangpsiel_versandpapiere.sh

    * xml einlesen
      * pdf vorauskasse erstellen
      * pdf versandpapier erstellen
