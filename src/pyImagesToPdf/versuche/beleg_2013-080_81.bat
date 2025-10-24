set BIN="C:\Program Files (x86)\ImageMagick-6.6.9-Q16\convert.exe"
set CONVERT=%BIN%\convert.exe
set MOGRIFY=%BIN%\mogrify.exe

rem convert -verbose -density 150 -trim beleg_2013-080_81.pdf -quality 100 -sharpen 0x1.0 beleg_2013-080_81.jpg
rem convert -density 300 -trim beleg_2013-080_81.pdf -quality 100

set GS="C:\Program Files\gs\gs9.15\bin\gswin64c.exe"
rem %GS% -sDEVICE=pngalpha -sOutputFile=beleg_2013-080_81.png -r144 beleg_2013-080_81.pdf
rem %GS% -sBACKGROUND=red -q -dNOPROMPT -sDEVICE=pngalpha -r300 -sOutputFile=beleg_2013-080_81.png beleg_2013-080_81.pdf
rem %GS% -dBackgroundColor=16#CCCC00 -sDEVICE=pngalpha -r300 -sOutputFile=beleg_2013-080_81.png beleg_2013-080_81.pdf

rem %GS% -sDEVICE=pngalpha -r300 -sOutputFile=beleg_2013-080_81.png beleg_2013-080_81.pdf
rem convert -background transparent beleg_2013-080_81.png beleg_2013-080_81_transp.png

rem %GS% -sDEVICE=jpeg -dJPEGQ=100 -r300 -sOutputFile=beleg_2013-080_81.jpg beleg_2013-080_81.pdf

rem %GS% -sDEVICE=png -r300 -sOutputFile=beleg_2013-080_81.png beleg_2013-080_81.pdf

rem %GS% -q -dNOPROMPT -dNOPAUSE -dBatch -sDEVICE=png16m -r360 -sOutputFile=beleg_2013-080_81.png beleg_2013-080_81.pdf
%GS% -dNOPROMPT -dNOPAUSE -dBATCH -sDEVICE=png16m -r360 -sOutputFile=beleg_2013-080_81.png beleg_2013-080_81.pdf

rem %GS% -sDEVICE=png256 -r300 -sOutputFile=beleg_2013-080_81.png beleg_2013-080_81.pdf

pause

