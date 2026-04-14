#!/bin/bash

# lpstat -p -d
# lpoptions -p HL-5350DN-series -l | grep -i 'tray\|source\|input'

COMMON="-P HL-5350DN-series -o BRMediaType=ThickPaper2 rechnung.pdf"

# A4
lpr -o page-ranges=1 -o InputSlot=Tray2 -o PageSize=A4 $COMMON

# A6
lpr -o page-ranges=2 -o InputSlot=Tray1 -o PageSize=A6 $COMMON

