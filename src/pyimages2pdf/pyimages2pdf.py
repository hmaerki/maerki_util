# -*- coding: utf-8 -*-
"""
Dieses Modul erstellt die PDF-Dokumente.
Es wird 'reportlab' von http://www.reportlab.org/rl_toolkit.html verwendet.
"""
bDebugDrawGrid = False

import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import types

if False:
    os.environ["RL_canvas_basefontname"] = "Helvetica"
    os.environ["RL_defaultGraphicsFontName"] = "Helvetica"
    os.environ["RL_longTableOptimize"] = "1"

# defaultGraphicsFontName
import reportlab
import reportlab.lib.enums
import reportlab.lib.pagesizes
import reportlab.lib.styles
import reportlab.lib.units
import reportlab.platypus
import reportlab.platypus.flowables

# See: http://two.pairlist.net/pipermail/reportlab-users/2004-April/002917.html
class Bookmark(reportlab.platypus.flowables.Flowable):
    "Utility class to display PDF bookmark."

    def __init__(self, title, key):
        self.title = title
        self.key = key
        reportlab.platypus.flowables.Flowable.__init__(self)

    def wrap(self, availWidth, availHeight):
        """Doesn't take up any space."""
        return (0, 0)

    def draw(self):
        # set the bookmark outline to show when the file's opened
        self.canv.showOutline()
        # step 1: put a bookmark on the
        self.canv.bookmarkPage(self.key)
        # step 2: put an entry in the bookmark outline
        self.canv.addOutlineEntry(self.title, self.key, 0, 0)


#
# Default-Werte
#
# Seite
rectPAGESIZE = reportlab.lib.pagesizes.landscape(reportlab.lib.pagesizes.A4)
rectPAGESIZE = reportlab.lib.pagesizes.A4
fMARGINLEFT = 0.0 * reportlab.lib.units.mm
fMARGINRIGHT = 0.0 * reportlab.lib.units.mm
fMARGINTOP = 12.0 * reportlab.lib.units.mm
fMARGINBOTTOM = 0.0 * reportlab.lib.units.mm

fMARGIN_HEADER_LEFT = 8.0 * reportlab.lib.units.mm
fMARGIN_HEADER_RIGHT = 8.0 * reportlab.lib.units.mm
fMARGIN_HEADER_TOP = 0.0 * reportlab.lib.units.mm
fMARGIN_HEADER_TOP_LINE = 1.0 * reportlab.lib.units.mm

fMARGIN_FOOTER_BOTTOM = 4.0 * reportlab.lib.units.mm


# Fonts
strFONT = "Helvetica"
strFONT_BOLD = "Helvetica-Bold"
iFONT_SIZE_H1 = 16
iFONT_SIZE_H2 = 12
iFONT_SIZE_H3 = 10
iFONT_SIZE_H4 = 6
iFONT_SIZE_NORMAL = 10


def getSampleStyleSheet():
    """Returns a stylesheet object"""
    stylesheet = reportlab.lib.styles.StyleSheet1()

    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="Normal", fontName="Helvetica", fontSize=iFONT_SIZE_NORMAL, leading=10
        )
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="BodyText",
            parent=stylesheet["Normal"],
            # leftIndent=6,
            # firstLineIndent=-6,
            spaceBefore=6,
        )
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="BodyTextRight",
            parent=stylesheet["BodyText"],
            alignment=reportlab.lib.enums.TA_RIGHT,
        )
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="Italic", parent=stylesheet["BodyText"], fontName="Helvetica-Italic"
        )
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="h1",
            parent=stylesheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=iFONT_SIZE_H1,
            leading=22,
            spaceAfter=6,
        ),
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="h2",
            parent=stylesheet["Normal"],
            fontName="Helvetica-Bold",
            fontSize=iFONT_SIZE_H2,
        ),
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="h2Right",
            parent=stylesheet["h2"],
            alignment=reportlab.lib.enums.TA_RIGHT,
        ),
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="h3",
            parent=stylesheet["Normal"],
            fontName="Helvetica-BoldOblique",
            fontSize=iFONT_SIZE_H3,
        ),
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="h3Right",
            parent=stylesheet["h3"],
            alignment=reportlab.lib.enums.TA_RIGHT,
        ),
    )
    stylesheet.add(
        reportlab.lib.styles.ParagraphStyle(
            name="Bullet", parent=stylesheet["Normal"], firstLineIndent=0, spaceBefore=3
        ),
    )

    return stylesheet


styleSheet = getSampleStyleSheet()


class PdfRenderer:
    def __init__(self, bDebug, listFiles, strPdfFilename):
        self.bDebug = bDebug
        self.listFiles = listFiles
        self.strPdfFilename = strPdfFilename

    def __myFirstPage(self, canvas, doc):
        """
        Header.
        """
        (
            strFilenameFull,
            strHeaderLinks,
            strHeaderMitte,
            strHeaderRechts,
            strBookmark,
        ) = self.listFiles[doc.page - 1]
        strFilename = os.path.basename(strFilenameFull)

        canvas.saveState()

        # canvas.setFillColor(Color(0, 0, 0, 1))
        canvas.setFillColor(reportlab.lib.colors.white)
        if self.bDebug:
            canvas.setFillColor(reportlab.lib.colors.lightgrey)
            # canvas.setFillColor(reportlab.lib.colors.red)
            # canvas.setFillColor(reportlab.lib.colors.darkgray)
            # canvas.setFillColor(reportlab.lib.colors.burlywood)

        canvas.rect(
            0.0,
            0.0,
            doc.width + fMARGINLEFT + fMARGINRIGHT,
            doc.height + fMARGINTOP + fMARGINBOTTOM,
            stroke=0,
            fill=1,
        )

        canvas.restoreState()
        canvas.saveState()

        yHeader = doc.height - fMARGIN_HEADER_TOP
        canvas.line(
            fMARGIN_HEADER_LEFT,
            yHeader - fMARGIN_HEADER_TOP_LINE,
            doc.width - fMARGIN_HEADER_RIGHT,
            yHeader - fMARGIN_HEADER_TOP_LINE,
        )

        # canvas.setFont(strFONT_BOLD, iFONT_SIZE_H2)
        # canvas.setFillColor(reportlab.lib.colors.lightgrey)
        # canvas.setFillColor(reportlab.lib.colors.darkgray)
        canvas.setFont(strFONT_BOLD, iFONT_SIZE_H2)
        canvas.drawRightString(
            doc.width - fMARGIN_HEADER_RIGHT, yHeader, strHeaderRechts
        )

        canvas.setFont(strFONT, iFONT_SIZE_H2)
        canvas.drawString(fMARGIN_HEADER_LEFT, yHeader, strHeaderLinks)
        canvas.drawCentredString(
            fMARGIN_HEADER_LEFT + doc.width / 2.0, yHeader, strHeaderMitte
        )

        canvas.setFont(strFONT, iFONT_SIZE_H4)
        canvas.drawString(fMARGIN_HEADER_LEFT, fMARGIN_FOOTER_BOTTOM, strFilename)
        canvas.drawCentredString(
            fMARGIN_HEADER_LEFT + doc.width / 2.0,
            fMARGIN_FOOTER_BOTTOM,
            "%d (%d)" % (doc.page, len(self.listFiles)),
        )

        canvas.restoreState()

    def __startPdfDocument(self, strFilename, strTitle):
        doc = reportlab.platypus.SimpleDocTemplate(
            strFilename,
            showBoundary=bDebugDrawGrid,
            pageCompression=1,
            pagesize=rectPAGESIZE,
            leading=22,
            spaceAfter=6,
            borderWidth=0.5,
            borderColor=reportlab.lib.colors.red,
            borderRadius=5,
            borderPadding=0,
            leftMargin=fMARGINLEFT,
            rightMargin=fMARGINRIGHT,
            topMargin=fMARGINTOP,
            bottomMargin=fMARGINBOTTOM,
            allowSplitting=1,
            title=strTitle,
            author="Author...",
            subject="Subject...",
            keywords=[],
            _debug=0,
        )
        return doc

    def __escape(self, strText):
        if strText == None:
            return ""
        if type(strText) == types.StringType:
            strText = strText.replace("&", "&amp;").replace("<", "&lt;")
            strText = strText.decode("utf-8")
        return strText

    def __parafy(self, strStyle, strText):
        strText = self.__escape(strText)
        return reportlab.platypus.Paragraph(strText, styleSheet[strStyle])

    def getImage(self, strFilenameFull, maxImageWidth, maxImageHeight):
        maxImageHeight = float(maxImageHeight)
        maxImageWidth = float(maxImageWidth)

        strFilenameFull2 = convertPdf2Jpg(strFilenameFull)
        img = reportlab.lib.utils.ImageReader(strFilenameFull2)
        iw, ih = img.getSize()
        aspect = float(ih) / float(iw)
        height = maxImageWidth * aspect
        width = maxImageWidth
        if height > maxImageHeight:
            height = maxImageHeight
            width = maxImageHeight / aspect

        return (
            reportlab.platypus.Image(strFilenameFull2, width=width, height=height),
            width,
            height,
        )

    def __dumpPages(self, doc, story):

        for (
            strFilenameFull,
            strHeaderLinks,
            strHeaderMitte,
            strHeaderRechts,
            strBookmark,
        ) in self.listFiles:
            strFilename = os.path.basename(strFilenameFull)
            print('"' + strFilename + '" processing...')
            strKey = strFilename

            story.append(Bookmark(strBookmark, strKey))
            maxImageWidth = doc.width - fMARGINLEFT - fMARGINRIGHT
            maxImageHeight = doc.height - fMARGINTOP - fMARGINBOTTOM
            # maxImageWidth = 1.5*reportlab.lib.units.cm
            # maxImageHeight = 1.5*reportlab.lib.units.cm
            image, width, height = self.getImage(
                strFilenameFull, maxImageWidth, maxImageHeight
            )
            # story.append(reportlab.platypus.Spacer(10, (maxImageHeight-height)/2.0))
            story.append(image)
            story.append(reportlab.platypus.flowables.PageBreak())
            print('"' + strFilename + '" done!')

    def createPages(self):
        doc = self.__startPdfDocument(self.strPdfFilename, "Dies ist ein Test")
        story = []
        self.__dumpPages(doc, story)
        print('Writing "%s"...' % self.strPdfFilename)
        doc.build(
            story, onFirstPage=self.__myFirstPage, onLaterPages=self.__myFirstPage
        )


def convertPdf2Jpg(strFilenameFullWithUnicode):
    if not strFilenameFullWithUnicode.endswith(".pdf"):
        return strFilenameFullWithUnicode

    strTempDir = tempfile.gettempdir()

    # Replace Unicode-Characters in Filename
    # http://stackoverflow.com/questions/20078816/replace-non-ascii-characters-with-a-single-space
    # Replace non-ASCII characters with a 'x'
    strFilenameFull = re.sub(r"[^\x00-\x7F]+", "x", strFilenameFullWithUnicode)
    if strFilenameFull != strFilenameFullWithUnicode:
        # Copy the file into the tmp-directory
        strFilenameFull = os.path.join(strTempDir, os.path.basename(strFilenameFull))
        shutil.copyfile(strFilenameFullWithUnicode, strFilenameFull)

    strGsExe = r"C:\Program Files\gs\gs9.54.0\bin\gswin64c.exe"
    strFilenamePng = os.path.basename(strFilenameFull)
    strFilenamePng = strFilenamePng.replace(".pdf", ".png")
    # http://stackoverflow.com/questions/20078816/replace-non-ascii-characters-with-a-single-space
    # Replace non-ASCII characters with a 'x'
    strFilenamePng = re.sub(r"[^\x00-\x7F]+", "x", strFilenamePng)
    strFilenameFullPng = os.path.join(strTempDir, strFilenamePng)
    if os.path.exists(strFilenameFullPng):
        os.remove(strFilenameFullPng)
    # command = r'"%s" -dNOPROMPT -dNOPAUSE -dBATCH -sDEVICE=png16m -r360 -sOutputFile="%s" "%s"' % (strGsExe, strFileNameFullPng, strFilenameFullPdf)
    # print(command
    # rc = os.system(command)
    listArgs = [
        strGsExe,
        "-dNOPROMPT",
        "-dNOPAUSE",
        "-dBATCH",
        "-sDEVICE=png16m",
        "-r360",
        "-sOutputFile=" + strFilenameFullPng,
        strFilenameFull,
    ]
    print(" ".join(listArgs))
    rc = subprocess.call(listArgs)
    if rc != 0:
        raise Exception("Ghostscript returned " + str(rc) + ". " + " ".join(listArgs))
    return strFilenameFullPng


def render(bDebug, listFiles, strPdfFilename):
    listFiles = list(listFiles)
    pdfRenderer = PdfRenderer(bDebug, listFiles, strPdfFilename)
    pdfRenderer.createPages()
    print("Done!")


def listdir(strDirectory):
    listFiles = os.listdir(strDirectory)
    listFiles.sort()

    def onlyImages(strFilename):
        strDummy, strExtension = os.path.splitext(strFilename)
        return strExtension in (".jpg", ".png", ".pdf")

    listFiles = filter(onlyImages, listFiles)
    listFiles = map(lambda f: os.path.abspath(os.path.join(strDirectory, f)), listFiles)
    listFiles = list(listFiles)
    return listFiles
