# Global Constants
strFilenamePdf = "belege.pdf"
strDirectory = "."
bDebug = True

# Load PyImagesToPdf-Framework
import os, re

from pyimages2pdf import pyimages2pdf


# Define Header-Text
def expandFiles(strFilenameFull):
    strFilename = os.path.basename(strFilenameFull)
    strHeaderLinks = "Steuererklärung Hans Märki 2013"
    strHeaderMitte = "Haus Aehrenweg 6"
    strHeaderRechts = re.sub(
        r"^beleg_2013-(?P<belegNr>.*)(.jpg|.png|.pdf)",
        r"Beleg \g<belegNr>",
        strFilename,
    )
    strBookmark = "%s: %s" % (strHeaderMitte, strHeaderRechts)
    return strFilenameFull, strHeaderLinks, strHeaderMitte, strHeaderRechts, strBookmark


# Directory Listing
listFiles = pyimages2pdf.listdir(strDirectory)

# Wir schliessen unseren Report selbst aus
listFiles = filter(lambda f: os.path.basename(f) != strFilenamePdf, listFiles)
# Wir akzeptieren nur Files ohne SKIP
listFiles = filter(lambda f: os.path.basename(f).find("SKIP") == -1, listFiles)

# Add Header-Text
listFiles = map(expandFiles, listFiles)

# Build PDF
pyimages2pdf.render(bDebug, listFiles, strFilenamePdf)
