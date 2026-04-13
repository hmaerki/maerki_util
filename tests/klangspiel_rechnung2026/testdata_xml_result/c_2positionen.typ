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
  \
  \
 
]
]


#v(1cm)

Hombrechtikon 2025-05-13

#v(0.5cm)

*Rechnung* \


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
  [www.klangspiel.ch/trinkente_klein_blau 34.20 abzüglich 2.6% Rabatt],
  [2 #h(2em) 66.62],
  [33.31],
  [www.klangspiel.ch/trinkente_klein_gruen 34.20 abzüglich 2.6% Rabatt],
  [2 #h(2em) 66.62],
  [33.31],
  [Versandkosten (Lieferung Schweiz)],
  [],
  [9.00],
  table.cell(colspan: 2, align: right)[*Rechnungsbetrag*],
  [*142.24*],

  table.cell(colspan: 2, align: right)[Davon sind MWST 8.1 % (CHE-108.547.136-MWST)],
  [10.67],
)

#v(1cm)

_Ich habe Ihre Zahlung erhalten, vielen Dank._

#v(1fr)


Zahlbar innerhalb 30 Tagen netto mit beigelegtem Einzahlungsschein oder auf Konto Raiffeisenbank Männedorf IBAN CH69 8080 8003 1598 6252 0, IID 80808, SWIFT: RAIFCH22, Begünstigter: Peter Märki, Zelglistrasse 49, 8634 Hombrechtikon. Bei Bankzahlung: Bitte Ref Nr. angeben. Nach Möglichkeit mit Giro, damit keine Spesen anfallen.

Ab der zweiten Mahnung sind Mahnspesen fällig: 50.-.

#page(paper: "a5", flipped: true, margin: (left: 1cm, top: 2cm, right: 1cm, bottom: 2cm))[
	#place(top + left, dx: 2cm, dy: 8cm)[
		#image("c_2positionen.png")
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
			Karsten Müller \
			Rödgener Str. 30a	Deutschland \
			04509 Delitzsch
		]  
	]
]
