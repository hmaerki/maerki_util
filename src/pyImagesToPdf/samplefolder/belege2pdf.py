# -*- coding: utf-8 -*-

# Global Constants
strFilenamePdf = 'belege.pdf'
strDirectory = '.'
bDebug = True

# Load PyImagesToPdf-Framework
import sys, os, re
strPyImagesToPdf = r'C:\Projekte\hans_svn\pyImagesToPdf'
sys.path.insert(0, strPyImagesToPdf)
import pyImageToPdf

# Define Header-Text
def expandFiles(strFilenameFull):
  strFilename = os.path.basename(strFilenameFull)
  strHeaderLinks = 'Steuererklärung Hans Märki 2013'
  strHeaderMitte = 'Haus Aehrenweg 6'
  strHeaderRechts = re.sub(r'^beleg_2013-(?P<belegNr>.*)(.jpg|.png|.pdf)', r'Beleg \g<belegNr>', strFilename)
  strBookmark = '%s: %s' % (strHeaderMitte, strHeaderRechts)
  return strFilenameFull, strHeaderLinks, strHeaderMitte, strHeaderRechts, strBookmark

# Directory Listing
listFiles = pyImageToPdf.listdir(strDirectory)

# Wir schliessen unseren Report selbst aus
listFiles = filter(lambda f: os.path.basename(f) != strFilenamePdf, listFiles)
# Wir akzeptieren nur Files ohne SKIP
listFiles = filter(lambda f: os.path.basename(f).find('SKIP') == -1, listFiles)

# Add Header-Text
listFiles = map(expandFiles, listFiles)

# Build PDF
pyImageToPdf.render(bDebug, listFiles, strFilenamePdf)
