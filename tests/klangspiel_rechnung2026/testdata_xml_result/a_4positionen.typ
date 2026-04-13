#set page(paper: "a4", margin: (top: 1.5cm, bottom: 2cm, left: 2cm, right: 1.5cm))
#set text(size: 10pt, font: "Liberation Sans")

#align(right)[
  #text(size: 9pt)[
    www.klangspiel.ch \
    Switzerland \

    Peter Märki

    Zelglistrasse 49 \
    peter\@klangspiel.ch

    8634 Hombrechtikon \
    CHE-108.547.136
  ]
]

#v(0.5cm)

#pad(left: 10cm)[
#text(size: 12pt, weight: "bold")[
  \
Roger Koch \
11 Kranichweg  \
3074 Muri b. Bern
]
]


#v(1cm)

Hombrechtikon 2026-04-01

#v(0.5cm)

*Rechnung* \
Lieferadresse: Roger Koch, 11 Kranichweg, 3074 Muri b. Bern

#v(0.3cm)

#table(
  columns: (1fr, auto, auto),
  align: (left, right, right),
  // stroke: 0.4pt,
  stroke: none,
  inset: 4pt,
  table.header(
    [*Produkt*],
    [*Anzahl à*],
    [*Total CHF*],
  ),
  [www.klangspiel.ch/unikat/briefmarken\#d4842],
  [1 #h(2em) 57.00],
  [57.00],
  [www.klangspiel.ch/unikat/briefmarkenbogen\#ad1433],
  [1 #h(2em) 19.00],
  [19.00],
  [www.klangspiel.ch/unikat/briefmarkenbogen\#ad3744],
  [1 #h(2em) 19.00],
  [19.00],
  [www.klangspiel.ch/unikat/briefmarkenbogen\#d3940],
  [1 #h(2em) 19.00],
  [19.00],
  [Versandkosten (Lieferung Schweiz)],
  [],
  [2.00],
  table.cell(colspan: 2, align: right)[*Rechnungsbetrag*],
  [*116.00*],

  table.cell(colspan: 2, align: right)[Davon sind MWST 8.1 % (CHE-108.547.136-MWST)],
  [0.15],
)

#v(1cm)

_Ich habe Ihre Zahlung erhalten, vielen Dank._

#v(1fr)


Zahlbar innerhalb 30 Tagen netto mit beigelegtem Einzahlungsschein oder auf Konto Raiffeisenbank Männedorf IBAN CH69 8080 8003 1598 6252 0, IID 80808, SWIFT: RAIFCH22, Begünstigter: Peter Märki, Zelglistrasse 49, 8634 Hombrechtikon. Bei Bankzahlung: Bitte Ref Nr. angeben. Nach Möglichkeit mit Giro, damit keine Spesen anfallen.

Ab der zweiten Mahnung sind Mahnspesen fällig: 50.-.

#page(paper: "a5", flipped: true, margin: (left: 1cm, top: 2cm, right: 1cm, bottom: 2cm))[
	#place(top + left, dx: 2cm, dy: 8cm)[
		#image("a_4positionen.png")
	]

	#place(top + left, dx: 2cm, dy: 3cm)[
		#rotate(-90deg)[
			#text(size: 12pt)[
				Absender: \
				www.klangspiel.ch \
				Peter Märki \
				Zelglistrasse 49 \
				CH-8634 Hombrechtikon
			]
		]
	]

	
	#pad(left: 8cm, top: 6cm)[
		#text(size: 24pt, weight: "bold")[
			  \
			Roger Koch \
			11 Kranichweg	 \
			3074 Muri b. Bern
		]  
	]
]
