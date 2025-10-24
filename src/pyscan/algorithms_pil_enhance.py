
"""
Imaging Algorithms using PIL.
The documentation may be found here
  http://www.pythonware.com/library/pil/handbook/index.htm
"""

from PIL import (
    Image,
    ImageChops,
    ImageDraw,
    ImageEnhance,
    ImageFilter,
    ImageMath,
    ImageOps,
    ImagePalette,
    ImageStat,
)


def tile(listImages):
    imBase = listImages[0][0].copy()
    iWidth, iHeight = imBase.size
    iTileWidth = iWidth / len(listImages)

    x = 0
    for im, strIm in listImages:
        imCrop = im.crop((9, 0, iTileWidth, iHeight))
        imBase.paste(imCrop, (x + 1, 0))
        draw = ImageDraw.Draw(imBase)
        draw.text((x + iTileWidth / 2 - 10, 10), strIm)
        draw.line((x + iTileWidth, 0, x + iTileWidth, iHeight), fill=128)
        del draw
        x += iTileWidth
    return imBase


def saveas(strFilenameBMP, filenameSaveAs, iQuality=100, iDpi=300):
    im = Image.open(strFilenameBMP)
    # im.info['dpi'] = iDpi
    im.save(filenameSaveAs, quality=iQuality, dpi=(float(iDpi), float(iDpi)))


def horizontalMirrorBMP(strFilenameBMP):
    im = Image.open(strFilenameBMP)

    im = ImageOps.mirror(im)

    im.save(strFilenameBMP)


def rotateBMP(strFilenameBMP):
    im = Image.open(strFilenameBMP)

    # Turn 180 degrees
    im = ImageOps.flip(im)
    im = ImageOps.mirror(im)

    im.save(strFilenameBMP)


def enhance2(strFilenameBMP, filenameSaveAs, iLevel, iDpi=300):
    im = Image.open(strFilenameBMP)
    print(im.format, im.size, im.mode)

    if True:
        # Desparcle
        im = im.filter(ImageFilter.MedianFilter(3))

    if True:
        print(im.format, im.size, im.mode)
        im = ImageOps.grayscale(im)

        print("iLevel: %d" % iLevel)

        def f(pixel):
            # print(pixel
            # if pixel > 200:
            if pixel > iLevel:
                return 255
            return 0

        im = Image.eval(im, f)

        # im.putpalette([0, 255], rawmode='L')
        # im.putpalette([0, 255])
        im = im.convert("1")

        print(im.format, im.size, im.mode)

    im.save(filenameSaveAs, dpi=(float(iDpi), float(iDpi)))


def enhance(strFilenameBMP, filenameSaveAs, fPercentageBlack=0.01, iDpi=300):
    im = Image.open(strFilenameBMP)
    print(im.format, im.size, im.mode)

    if False:
        im = im.convert("L")
    if False:
        im = im.convert("L")

        def f(pixel):
            print(pixel)
            if pixel > 180:
                return 255
            return 0

        im = Image.eval(im, f)
    if False:
        rgb2xyz = (
            0.412453,
            0.357580,
            0.180423,
            0,
            0.212671,
            0.715160,
            0.072169,
            0,
            0.019334,
            0.119193,
            0.950227,
            0,
        )
        rgb2xyz = (
            0.112453,
            0.357580,
            0.180423,
            0,
            0.112671,
            0.715160,
            0.072169,
            0,
            0.019334,
            0.119193,
            0.950227,
            0,
        )
        im = im.convert("RGB", rgb2xyz)
    if False:
        im = im.convert("1")

    if False:
        im = im.filter(ImageFilter.MinFilter(7))
        im = im.filter(ImageFilter.MaxFilter(3))

    if False:
        # dunkler
        enh = ImageEnhance.Brightness(im)
        im = enh.enhance(0.8)
    if False:
        # mehr Kontrast
        enh = ImageEnhance.Contrast(im)
        im = enh.enhance(1.5)
    if False:
        im = ImageOps.grayscale(im)
    if False:
        enh = ImageEnhance.Contrast(im)
        im = enh.enhance(1.3)
    if False:
        print(im.format, im.size, im.mode)
        im = ImageOps.grayscale(im)
        print("im.histogram(): ", im.histogram())

        # enh = ImageEnhance.Contrast(im)
        # im = enh.enhance(1.5)
        def f(pixel):
            # print(pixel
            if pixel > 200:
                return 255
            return 0

        im = Image.eval(im, f)
        print(im.format, im.size, im.mode)

    if True:
        histogram = im.histogram()
        f = open(filenameSaveAs.replace(".png", "_histogram.txt"), "w")
        f.write(str(histogram))
        for i in histogram:
            f.write("%d\n" % i)
        f.write("Summenkurve\n")
        if len(histogram) == 256:
            iTotal = 0
            for gray in histogram:
                iTotal += gray
                f.write("%d\n" % iTotal)
        else:
            r, g, b = 0, 0, 0
            for i in range(256):
                r += histogram[i]
                g += histogram[i + 256]
                b += histogram[i + 512]
                f.write("%d\t%d\t%d\n" % (r, g, b))
        f.close()

    if True:
        # Desparcle
        im = im.filter(ImageFilter.MedianFilter(3))

    if True:
        print(im.format, im.size, im.mode)
        im = ImageOps.grayscale(im)
        print("im.histogram(): ", im.histogram())

        # enh = ImageEnhance.Contrast(im)
        # im = enh.enhance(1.5)
        def f(pixel):
            # print(pixel
            if pixel > 200:
                return 1
            return 0

        # im = im.point(f, 'P')

        iTotal = 0
        histogram = im.histogram()
        for gray in histogram:
            iTotal += gray
        assert iTotal == im.size[0] * im.size[1]
        if True:
            iGrayBlack = None
            iGrayWhite = None
            iSum = 0
            for i, iGray in zip(range(len(histogram)), histogram):
                iSum += iGray
                if (not iGrayBlack) and (iSum > iTotal * fPercentageBlack):
                    iGrayBlack = i
                if (not iGrayWhite) and (iSum > iTotal * (1 - fPercentageBlack)):
                    iGrayWhite = i
            iLevel = (iGrayWhite + iGrayBlack) / 2
        if False:
            iSum = 0
            for i, iGray in zip(range(len(histogram)), histogram):
                iSum += iGray
                if iSum > iTotal * 0.02:
                    break
        print("iLevel: %d" % iLevel)

        def f(pixel):
            # print(pixel
            # if pixel > 200:
            if pixel > iLevel:
                return 255
            return 0

        im = Image.eval(im, f)
        if False:
            # im.putpalette(ImagePalette.ImagePalette(mode='P',
            # palette=range(256)), rawmode='L')
            # im.putpalette(data=range(256), rawmode='P')
            palette = [
                0,
            ] * 256
            palette[1] = 255
            print(palette)
            # im.putpalette(data=range(256))
            im.putpalette(data=palette, rawmode="RGB")

        # im.putpalette([0, 255], rawmode='L')
        # im.putpalette([0, 255])
        im = im.convert("1")

        print(im.format, im.size, im.mode)

    if False:
        stat = ImageStat.Stat(im)
        print("stat.count: ", stat.count)
        print("stat.mean: ", stat.mean)
        print("stat.median: ", stat.median)
        print("stat.var: ", stat.var)
        print("stat.stddev: ", stat.stddev)

        print("im.histogram(): ", im.histogram())

    # im.show()
    # im.save('tmp.jpg')
    im.save(filenameSaveAs, dpi=(float(iDpi), float(iDpi)))


def enhance3(strFilenameBMP, filenameSaveAs, iDpi=300):
    """
    Dieser Algorithmus SMOOTH die grossen Flaechen,
    aber veraendert die Uebergaenge nicht. So koennen
    Schatten und Verlaeufe einfach entfernt werden
    """
    im = Image.open(strFilenameBMP)
    # print(im.format, im.size, im.mode
    width, height = im.size

    bShow = True

    im = ImageOps.autocontrast(im, cutoff=0)
    if bShow:
        im.show()

    #
    # imAlphaBW ist dort weiss, wo groesse
    # Grauspruenge vorhanden sind:
    # Im Umkreis von 3 Pixel wird der Unterschied
    # vom hellsten zum dunkelsten Pixel genommen (imDiff).
    # Dort wo der Unterschied groesser als 120 ist: weiss,
    # sonst schwarz (imAlphaBW).
    #
    imMax = im.filter(ImageFilter.MaxFilter(3))
    imMin = im.filter(ImageFilter.MinFilter(3))
    imDiff = ImageChops.difference(imMax, imMin)
    if bShow:
        imDiff.show()

    def blackWhite(im, iLimit):
        palette = [0] * iLimit + [255] * (256 - iLimit)
        return im.point(palette)

    imAlphaBW = blackWhite(imDiff, 120)

    #
    # Das urspruengliche Bild wird geglaettet (imMedian)
    # und anschliessend schwarz/weiss gewandelt (imBW).
    #
    # imMedian = im.filter(ImageFilter.MedianFilter(3))
    imMedian = im.filter(ImageFilter.SMOOTH)
    imBW = blackWhite(imMedian, 160)
    if bShow:
        imBW.show()
    # imBW.show()

    #
    # Jetzt werden die drei Bilder kombiniert.
    # Dort wo es grosse Grauwertspruenge gab, wird
    # das Original-Bild verwendet, sonst das geglaettete.
    #
    imGrayBW = Image.composite(im, imBW, imAlphaBW)
    if bShow:
        imGrayBW.show()

    if height > 2400:
        #
        # Grosse Bilder werden verkleinert.  2400 entspricht
        # der Hoehe von A4 bei 200 dpi.
        #
        heightNew = 2400
        widthNew = heightNew * width / height
        imGrayBW = imGrayBW.resize((widthNew, heightNew), Image.ANTIALIAS)
    else:
        imGrayBW = imGrayBW.filter(ImageFilter.SMOOTH)
    if bShow:
        imGrayBW.show()

    #
    # Schwarz ist aufgrund des obigen SMOOTH nur noch grau.  Nachfolgende
    # Korrektur verdunkelt dunkle Bereiche.  Zudem wird das Bild auf
    # vier Grauwerte reduziert
    #
    table = [0] * 96 + [85] * 96 + [170] * 32 + [255] * 32
    imGrayBW = imGrayBW.point(table)

    # Das Image wird mit einer Palette versehen und abgespeichert.
    imgPalette = imGrayBW.convert(
        "P", dither=Image.NONE, palette=Image.ADAPTIVE, colors=4
    )
    imgPalette.save(filenameSaveAs.replace(".png", "_gray.png"))

    # Das Image wird schwarz/weiss gewandelt und gespeichert
    imGrayBW = blackWhite(imGrayBW, 127)
    # imGrayBW.show()
    imGrayBW = imGrayBW.convert("1")
    if bShow:
        imGrayBW.show()

    imGrayBW.save(filenameSaveAs, dpi=(float(iDpi), float(iDpi)))


def enhance4(strFilenameBMP, filenameSaveAs, iDpi=300):
    """
    Diese Optimierung nimmt den Papierhintergrund mit eventuellen
    Verlaeufen wie z. B. bei aufgeklappten Buechern und subtrahiert
    dies vom Original. Dadurch ist der Hintergrund quasi weiss.
    Jetzt wird wie ueblich verkleinert und mit einem Schwellwert
    auf SW umgesetzt.
    """
    im = Image.open(strFilenameBMP)
    print(im.format, im.size, im.mode)

    bShow = True

    im = ImageOps.autocontrast(im, cutoff=0)
    if bShow:
        pass

    imMax = im.filter(ImageFilter.MedianFilter(5))
    imMax = imMax.filter(ImageFilter.MaxFilter(19))
    if bShow:
        imMax.show()

    imDiff = ImageChops.difference(im, imMax)
    imDiff = ImageChops.invert(imDiff)
    if bShow:
        imDiff.show()

    width, height = im.size
    if height > 2400:
        #
        # Grosse Bilder werden verkleinert.  2400 entspricht
        # der Hoehe von A4 bei 200 dpi.
        #
        heightNew = 2400
        widthNew = heightNew * width / height
        imDiff = imDiff.resize((widthNew, heightNew), Image.ANTIALIAS)
    else:
        imDiff = imDiff.filter(ImageFilter.SMOOTH_MORE)
    if bShow:
        imDiff.show()

    if False:
        imDiff.save("buchknick_300dpi.bmp")

    table = [0] * 200 + [255] * 56
    imBW = imDiff.point(table)

    imBW = imBW.convert("1")
    if bShow:
        imBW.show()
    imBW.save(filenameSaveAs, dpi=(float(iDpi), float(iDpi)))


def enhance5(
    strFilenameBMP,
    filenameSaveAs,
    bVerkleinern=True,
    iRasterEntfernen=4,
    bHelligkeitskorrektur=False,
    iAlphaBW=120,
    iBlackWhite=180,
    iDpi=300,
):
    """
    Diese Optimierung kombiniert enhance3 und enhance4.
    """
    im = Image.open(strFilenameBMP)
    print(im.format, im.size, im.mode)

    bShow = False

    im = ImageOps.autocontrast(im, cutoff=0)

    def blackWhite(im, iLimit):
        table = [0] * iLimit + [255] * (256 - iLimit)
        return im.point(table)

    if bHelligkeitskorrektur:
        imMax = im.filter(ImageFilter.MedianFilter(5))
        imMax = imMax.filter(ImageFilter.MaxFilter(19))

        imDiff = ImageMath.eval("a-b+256", a=im, b=imMax)

        imEqualized = imDiff.convert("L")

        #
        # imAlphaBW ist dort weiss, wo groesse
        # Grauspruenge vorhanden sind:
        # Im Umkreis von 3 Pixel wird der Unterschied
        # vom hellsten zum dunkelsten Pixel genommen (imDiff).
        # Dort wo der Unterschied groesser als 120 ist: weiss,
        # sonst schwarz (imAlphaBW).
        #
        imMax = imEqualized.filter(ImageFilter.MaxFilter(3))
        imMin = imEqualized.filter(ImageFilter.MinFilter(3))
        imDiff = ImageChops.difference(imMax, imMin)
        if bShow:
            # imDiff.show()
            pass
        imAlphaBW = imDiff
        imAlphaBW = blackWhite(imDiff, iAlphaBW)

        imSmooth = imEqualized.filter(ImageFilter.SMOOTH_MORE)
        imSharpen = im.filter(ImageFilter.SHARPEN)
        imGray = Image.composite(imSharpen, imSmooth, imAlphaBW)
    else:
        imGray = im.copy()

    def blackWhite(im, iLimit):
        table = [0] * iLimit + [255] * (256 - iLimit)
        return im.point(table)

    imBW = blackWhite(imGray, iBlackWhite)

    if bShow:
        tile(
            (
                (im, "im"),
                (imEqualized, "imEqualized"),
                (imAlphaBW, "imAlphaBW"),
                (imGray, "imGray"),
                (imBW, "imBW"),
            )
        ).show()

    width, height = imGray.size
    if bVerkleinern and (height > 2400):
        #
        # Grosse Bilder werden verkleinert.  2400 entspricht
        # der Hoehe von A4 bei 200 dpi.
        #
        heightNew = 2400
        widthNew = heightNew * width / height
        imBW = imGray.resize((widthNew, heightNew), Image.ANTIALIAS)
    else:
        imBW = imGray.filter(ImageFilter.SMOOTH_MORE)

    if bShow:
        # imBW.show()
        pass

    imBW = blackWhite(imBW, iBlackWhite)

    imBW = imBW.convert("1")

    # Raster entfernen

    if iRasterEntfernen:
        # 300 DPI: Sinnvoll: 5
        # 200 DPI: Sinnvoll: 4
        # Vorlage: Kantonalbank, gescannt mit 200 dpi
        # ä,i: Mindestens 8 zusammenhängende Pixel in 3x3
        # Raster: Maximum 4 zusammenhängende Pixel in 3x3
        imBW = imBW.filter(ImageFilter.RankFilter(3, iRasterEntfernen))
        if False:
            if iRasterEntfernen > 4:
                imBW = imBW.filter(ImageFilter.RankFilter(5, iRasterEntfernen))
            else:
                imBW = imBW.filter(ImageFilter.RankFilter(3, iRasterEntfernen))

    if bShow:
        imBW.show()
    imBW.save(filenameSaveAs, dpi=(float(iDpi), float(iDpi)))


def enhance6(
    strFilenameBMP,
    filenameSaveAs,
    bVerkleinern=True,
    iRasterEntfernen=4,
    iAlphaBW=120,
    iBlackWhite=180,
    iDpi=300,
):
    """
    Diese Optimierung kombiniert enhance3 und enhance4.
    """
    if False:
        import bmputils

        # strFilenameBmpTmp = strFilenameBMP.lower().replace('.bmp', '_tmp.bmp')
        # bmputils.convert(strFilenameBMP, strFilenameBmpTmp)
        # im = Image.open(strFilenameBmpTmp)
        bmputils.convert(strFilenameBMP, strFilenameBMP)
    im = Image.open(strFilenameBMP)
    print(im.format, im.size, im.mode)

    bShow = False

    if bShow:
        tile(
            (
                (im, "im"),
                (imEqualized, "imEqualized"),
                (imAlphaBW, "imAlphaBW"),
                (imGray, "imGray"),
                (imBW, "imBW"),
            )
        ).show()

    width, height = im.size
    if bVerkleinern and (height > 2400):
        #
        # Grosse Bilder werden verkleinert.  2400 entspricht
        # der Hoehe von A4 bei 200 dpi.
        #
        heightNew = 2400
        widthNew = heightNew * width / height
        im = im.resize((widthNew, heightNew), Image.ANTIALIAS)
    else:
        im = im.filter(ImageFilter.SMOOTH_MORE)

    if bShow:
        # im.show()
        pass

    def blackWhite(im, iLimit):
        table = [0] * iLimit + [255] * (256 - iLimit)
        return im.point(table)

    im = blackWhite(im, iBlackWhite)

    im = im.convert("1")

    # Raster entfernen

    if iRasterEntfernen:
        # 300 DPI: Sinnvoll: 5
        # 200 DPI: Sinnvoll: 4
        # Vorlage: Kantonalbank, gescannt mit 200 dpi
        # ä,i: Mindestens 8 zusammenhängende Pixel in 3x3
        # Raster: Maximum 4 zusammenhängende Pixel in 3x3
        im = im.filter(ImageFilter.RankFilter(3, iRasterEntfernen))
        if False:
            if iRasterEntfernen > 4:
                im = im.filter(ImageFilter.RankFilter(5, iRasterEntfernen))
            else:
                im = im.filter(ImageFilter.RankFilter(3, iRasterEntfernen))

    if bShow:
        im.show()
    im.save(filenameSaveAs, dpi=(float(iDpi), float(iDpi)))


def enhanceColor(strFilenameBMP, filenameSaveAs, iBlack=10, iWhite=100, iDpi=300):
    im = Image.open(strFilenameBMP)
    print(im.format, im.size, im.mode)
    a = iBlack
    b = float(256) / float(iWhite - iBlack)

    def f(pixel):
        print(pixel)
        if pixel > iWhite:
            return 255
        if pixel < iBlack:
            return 0
        return int(b * (pixel - a))

    im = Image.eval(im, f)
    # Das Image wird mit einer Palette versehen und abgespeichert.
    im = im.convert("P", dither=Image.NONE, palette=Image.ADAPTIVE, colors=256)
    im.save(filenameSaveAs, dpi=(float(iDpi), float(iDpi)))
