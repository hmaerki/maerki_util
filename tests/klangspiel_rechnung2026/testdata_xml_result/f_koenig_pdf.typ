#set page(paper: "a4", margin: (top: 1.5cm, bottom: 2cm, left: 2cm, right: 1.5cm))
#set text(size: 10pt, font: "Liberation Sans")

#align(right)[
  #text(size: 9pt)[
    www.klangspiel.ch \
    Switzerland \
    Tel: +41 55 508 22 72

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
Matthias König \
Reinhold-Frei-Strasse 23  \
8049 Zurich
]
]


#v(1cm)

Hombrechtikon 2026-02-22

#v(0.5cm)

*Rechnung* \
Lieferadresse: Nick König, Reinhold-Frei-Strasse 23, 8049 Zurich

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
  [www.klangspiel.ch/cointrap_transparent],
  [1 #h(2em) 4.30],
  [4.30],
  [Kleinmengenzuschlag],
  [1 #h(2em) 5.00],
  [5.00],
  [Versandkosten (Lieferung Schweiz)],
  [],
  [1.60],
  table.cell(colspan: 2, align: right)[*Rechnungsbetrag*],
  [*10.90*],

  table.cell(colspan: 2, align: right)[Davon sind MWST 8.1 % (CHE-108.547.136-MWST)],
  [0.81],
)

#v(1fr)

_Ich habe Ihre Zahlung erhalten, vielen Dank._

Zahlbar innerhalb 30 Tagen netto mit beigelegtem Einzahlungsschein oder auf Konto Raiffeisenbank Männedorf IBAN CH69 8080 8003 1598 6252 0, IID 80808, SWIFT: RAIFCH22, Begünstigter: Peter Märki, Zelglistrasse 49, 8634 Hombrechtikon. Bei Bankzahlung: Bitte Ref Nr. angeben. Nach Möglichkeit mit Giro, damit keine Spesen anfallen.

Ab der zweiten Mahnung sind Mahnspesen fällig: 50.-.

#page(paper: "a5", flipped: true, margin: (left: 1cm, top: 2cm, right: 1cm, bottom: 2cm))[
	#place(top + left, dx: 2cm, dy: 8cm)[
		#image("f_koenig_pdf.png")
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
			Nick König \
			Reinhold-Frei-Strasse 23	 \
			8049 Zurich
		]  
	]
]
