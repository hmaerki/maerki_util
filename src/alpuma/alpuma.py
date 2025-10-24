#! /usr/bin/env python

"""
  2005-2019, Hans Maerki, License LGPL

  Doubleclicking this file will loop over all
  image files in the current folder and create
  image-files and index.zulu_content.html.

  Installation:
    Now move this script into the folder with the images and
    double click it.
    If there is an error - you have about half a millisecond to
    see it. If this is to quick, open a dos-window, cd to the
    directory with your image-files and type "alpuma.py". Now
    you will see the error message.

   Pseudocode:
     for each *.jpg|*.gif|*.png
       convert image
       Get size of image
       if 'index.zulu_content.html' does not exist: create it from template.
       replace in 'index.zulu_content.html'
         href="bilder/06.jpg"
            <img src="bilder/06k.jpg" alt="Grossformat" border="0" width="200" height="150">
         if not found
            Add template at begin of page

  Kurzanleitung:
    Ordnerstruktur bereitstellen:
      base/alpuma_v2.0.0.py       (von Hans)
      base/alpuma_config.txt      (von Hans)
      base/orig/IMAGE123.JPG      (Hier die Bilder hineinkopieren
    'base/alpuma_v2.0.0.py' doppelklicken. Es entstehen folgende Files:
      'base/images/IMAGE123.JPG'
      'base/thumbs/IMAGE123.JPG'
      'base/index.zulu_content.html'

  Features:
    Imageverarbeitung:
      Ordner werden kreiert, falls noetig.
      Die Datei 'index.zulu_content.html' wird kreiert, falls noetig.
      Images werden nur dann neu geschrieben, falls sie inhaltlich geaendert haben.
      Die Breite des Images wird angepasst. Falls zu hoch, wird anhand der
      maximalen Hoehe skaliert.

    HTML aktualisieren:
      Falls 'html_filename' fehlt in 'alpuma_config.txt', wird kein
      HTML-File bearbeitet.
      width/height wird eingesetzt, falls nicht vorhanden.
      Entry für image wird eingesetzt, falls nicht vorhanden.
      Falls ein File 'thumbs/IMAGE123_alpuma_override.JPG' existiert, wird
      auf dieses File referenziert statt auf 'thumbs/IMAGE123.JPG'.
      Falls ein File 'images/IMAGE123_alpuma_override.JPG' existiert und statt
      'images/IMAGE123.JPG' verwendet werden soll, so muss der neue Filename
      manuell im html-File nachgetragen werden.

    Annotations:
      In 'alpuma_config.txt' kann eine Annotation definiert werden. Dies
      ist zum Beispiel ein Copyright-Vermerk "© Aldo Mustardo".
      Diese Annotation wird auf alle Bilder plaziert, auf welcher der
      Text Platz hat.

    Recursion:
      Es werden alle Ordner unterhalb des Verzeichnisses
        recurse = {'top_directory': 'top',}
      durchsucht. Falls 'recurse=' nicht definiert ist, so wird
      der aktuelle Ordner verwendet.

    Recursion2
      Es werden alle Ordner unterhalb diesem File rekursiv durchlaufen.
      Wird ein 'alpuma_config.txt' gefunden, so wir dieses verarbeitet.

  History:
    2003-04-03, Hans Maerki. Python rules!
    2003-04-28, v2.0.0, Hans Maerki. Many new features.
    2003-04-28, v2.0.1, Hans Maerki. Minor bugfixes.
    2003-05-24, v2.0.2, Hans Maerki. Figaros Feature Request: Never enlarge images.
    2003-09-28, v2.0.3, Hans Maerki. 'Thumbs.db' wird ignoriert.
    2003-11-01, v2.0.4, Hans Maerki. Quality of the compression choosable now.
    2003-10-14, v2.0.5, Hans Maerki. Tested with Python 2.3
    2005-05-22, v2.0.6, Hans Maerki. Minor bugfixes.
    2005-09-10, v2.0.7, Hans Maerki. Refactoring - better structured. Added comments.
                                     Added Annotations.
    2005-09-13, v2.0.8, Hans Maerki. Fixed bugs introduced in v2.0.7.
    2006-12-24, v2.0.8, Hans Maerki. Tested on Ubuntu 6.10 and OsX Tiger
    2009-07-27, v2.1.0, Hans Maerki. Skips update of the image-files if date is newer
    2011-01-09, v2.2.0, Hans Maerki. Recurse over directory structure.
    2019-01-17, v2.2.1, Hans Maerki. Ported to python 3.7.2
    2019-01-17, v2.3.0, Hans Maerki. Recursion2: Now recurses down the filesytem
                                     to find 'alpuma_config.txt'
    2019-06-16, v2.3.1, Hans Maerki. config is not global anymmore
    2020-12-19, v2.3.2, Hans Maerki. Now rotates the image according to EXIF-transponse.
    2022-05-21, v2.3.3, Hans Maerki. Black. Replace % string fromatting by f strings.
"""

VERSION = "2.3.3"

import os
import stat
import filecmp
import PIL.Image
import PIL.ImageFont
import PIL.ImageDraw
import PIL.ImageStat
import PIL.ImageOps


CONFIG_DEFAULT = {
    "html_filename": None,
    # 'recurse': {'top_directory': '.',}
}

CONFIG_FILENAME = "alpuma_config.txt"


def go_recurse2():
    strTopDirectory = os.path.abspath(os.curdir)

    listAlpumaDirectories = []
    for strDirectory, _listDirectories, listFilenames in os.walk(strTopDirectory):
        if CONFIG_FILENAME in listFilenames:
            listAlpumaDirectories.append(strDirectory)

    listAlpumaDirectories.sort()

    for strAlpumaDirectory in listAlpumaDirectories:
        print(f'Found "{CONFIG_FILENAME}" in "{strAlpumaDirectory}"')

    for strAlpumaDirectory in listAlpumaDirectories:
        print(f'PROCESSING "{strAlpumaDirectory}"')
        os.chdir(os.path.join(strTopDirectory, strAlpumaDirectory))
        go()


def go():
    """
    Album assembler
    Precondition
      go_recurse2() set cwd to the directory where 'CONFIG_FILENAME'
    """
    with open(CONFIG_FILENAME, "r") as f:
        code = compile(f.read(), CONFIG_FILENAME, "exec")
    global_vars = {}
    config = CONFIG_DEFAULT.copy()
    exec(code, global_vars, config)
    if config.get("alpuma_config_version", None) != "1.0.0":
        raise Exception(
            "This Alpuma-Version is too old for this '%s'" % CONFIG_FILENAME
        )

    html_filename = config.get("html_filename")
    if html_filename != os.path.basename(html_filename):
        raise Exception(
            f'ERROR: "{os.path.abspath(os.path.curdir)}/{CONFIG_FILENAME}": Expecting just a simple filename but gut "html_filename = \'{html_filename}\'"!'
        )

    iModificationTimeConfig = os.stat(CONFIG_FILENAME)[stat.ST_MTIME]

    dictRecurse = config.get("recurse", None)
    if dictRecurse != None:
        go_recurse(config, iModificationTimeConfig, dictRecurse["top_directory"])
        return

    goDirectory(config, iModificationTimeConfig, ".")


def go_recurse(config, iModificationTimeConfig, strTop):
    """
    If there is a directory "input_path" (typically "images") in the current directory,
    we process this directory.
    Otherwise we recurse down into the subdirectories.
    """
    listDirectories = list(os.listdir(strTop))
    if config["input_path"] in listDirectories:
        goDirectory(config, iModificationTimeConfig, strTop)
        return

    listDirectoriesFull = []
    for strDirectory in listDirectories:
        if strDirectory.startswith("."):
            continue
        directoryFull = os.path.join(strTop, strDirectory)
        if not os.path.isdir(directoryFull):
            continue
        listDirectoriesFull.append(directoryFull)

    listDirectories = filter(lambda f: not f.startswith("."), listDirectories)
    for strDirectoryFull in listDirectoriesFull:
        go_recurse(config, iModificationTimeConfig, strDirectoryFull)


def goDirectory(config, iModificationTimeConfig, strDirectory):
    # Open the content-html file. If any or needed...
    if not os.path.exists(strDirectory):
        raise Exception(
            'ERROR: Directory does not exist "%s".' % os.path.abspath(strDirectory)
        )
    strFilenameHTML = os.path.join(strDirectory, config.get("html_filename"))
    strContent = config.get("html_template_file")
    if strFilenameHTML != None:
        try:
            with open(strFilenameHTML, "r") as fileContent:
                strContent = fileContent.read()
        except IOError as _e:
            print(
                f'Template "{config.get("html_filename")}" not found: Use template from "{CONFIG_FILENAME}".'
            )

    # Loop over all files in the images directory
    strOrigDirectory = os.path.join(strDirectory, config.get("input_path"))
    if not os.path.exists(strOrigDirectory):
        raise Exception(
            'ERROR: Directory does not exist "%s".' % os.path.abspath(strOrigDirectory)
        )
    for strFileRoot, strFileExt in getFiles(strOrigDirectory):
        strFilename = strFileRoot + strFileExt
        dictParams = {
            "file": strFilename,
            "fileroot": strFileRoot,
            "fileext": strFileExt,
        }
        print(
            f"Processing {os.path.join(os.path.abspath(strDirectory), strFilename)} ..."
        )

        # Convert the images
        for conversion in config.get("conversions"):
            strOutputPath = os.path.join(strDirectory, conversion["output_path"])
            if not os.path.exists(strOutputPath):
                print(f"  Create folder {strOutputPath} ...")
                os.mkdir(strOutputPath)
            convert_image(
                config, iModificationTimeConfig, strDirectory, strFilename, conversion
            )

        if strFilenameHTML != None:
            # Update the HTML-File if needed
            strContent = updateContent(
                config, strContent, strDirectory, strFilename, dictParams
            )

    if strFilenameHTML != None:
        print(f"  Write {strDirectory}\\{strFilenameHTML} ...")
        with open(strFilenameHTML, "w") as fileContent:
            fileContent.write(strContent)


def getFiles(strPath):
    # Loop over all files in the images directory
    files = os.listdir(strPath)
    files.sort(reverse=True)
    files = filter(lambda f: os.path.isfile(os.path.join(strPath, f)), files)
    files = map(os.path.splitext, files)
    files = filter(lambda f: f[1] in (".gif", ".jpg", ".png"), files)
    return files


def updateContent(config, strContent, strDirectory, strFilename, dictParams):
    strContentLower = strContent.lower()
    iStart = 0
    while 1:
        iStart = strContentLower.find("<img", iStart)
        iEnd = strContentLower.find(">", iStart + 1)
        if (iStart == -1) or (iEnd == -1):
            # Entry not found: Add new entry
            print("  Entry not found: Add new entry!")
            return updateContent(
                config,
                addEntry(config, strContent, dictParams),
                strDirectory,
                strFilename,
                dictParams,
            )
        for strFullPath in config.get("html_img_files"):
            strFullPath = getTemplate(strFullPath, dictParams)
            iPathStart = strContentLower.find(strFullPath.lower(), iStart, iEnd)
            if iPathStart != -1:
                # We found the entry we are looking for. Update it
                # Get the first image in the list
                for strFullImagePath in config.get("html_img_files"):
                    strHrefImagePath = getTemplate(strFullImagePath, dictParams)
                    strFullImagePath = os.path.join(strDirectory, strHrefImagePath)
                    if os.path.exists(strFullImagePath):
                        return updateEntryInContent(
                            strContent,
                            strFullPath,
                            strHrefImagePath,
                            strFullImagePath,
                            strFilename,
                            dictParams,
                            iStart,
                            iEnd,
                        )
        iStart = iEnd


def updateEntryInContent(
    strContent,
    strFullPath,
    strHrefImagePath,
    strFullImagePath,
    strFilename,
    dictParams,
    iStart,
    iEnd,
):
    strEntry = strContent[iStart:iEnd]
    if strFullPath != strHrefImagePath:
        strEntry = strEntry.replace(strFullPath, strHrefImagePath)
        print(f'  Renaming HTML "{strFullPath}" -> "{strHrefImagePath}".')
    if strHrefImagePath.find(strFilename) == -1:
        # Replace path if needed (case 'thumbs/{fileroot}_alpuma_override{fileext}')
        print(f'  Overriding HTML "{strHrefImagePath}".')
    strEntry = updateEntry(strEntry, strFullImagePath, dictParams)
    return strContent[:iStart] + strEntry + strContent[iEnd:]


def updateEntry(strEntry, strFullImagePath, dictParams):
    image = loadImage(strFullImagePath)
    iWidth, iHeight = image.size
    strEntry = replaceSize(strEntry, "width=", iWidth)
    strEntry = replaceSize(strEntry, "height=", iHeight)
    return strEntry


def addEntry(config, strContent, dictParams):
    if strContent.find("<!--AlpumaInsert-->") >= 0:
        strLeft, strRight = strContent.split("<!--AlpumaInsert-->", 1)
    else:
        strLeft = ""
        strRight = strContent
    strEntry = getTemplate(config.get("html_template_image"), dictParams)
    return strLeft + "<!--AlpumaInsert-->" + strEntry + strRight


def getTemplate(strTemplate, dictParams):
    for (strTag, strValue) in dictParams.items():
        strTemplate = strTemplate.replace("{%s}" % strTag, str(strValue))
    return strTemplate


def replaceSize(strEntry, strPattern, iValue):
    try:
        strStart, strValue = strEntry.split(strPattern + '"', 1)
        strValue, strEnd = strValue.split('"', 1)
    except ValueError:
        # strPattern not found. Add it at the end.
        return '%s %s"%d"' % (strEntry, strPattern, iValue)
    # Pattern found. Update the size.
    return '%s%s"%d"%s' % (strStart, strPattern, iValue, strEnd)


def loadImage(strFilename):
    with open(strFilename, "rb") as fp:
        image = PIL.Image.open(fp)
        image.load()
        image = PIL.ImageOps.exif_transpose(image)
        return image


def convert_image(
    config, iModificationTimeConfig, strDirectory, strFilename, conversion
):
    # Get default/configuration values
    iQuality = conversion.get("quality", 100)  # Default for quality if not defined.
    strPathInput = os.path.join(strDirectory, config.get("input_path"))
    strPathOutput = os.path.join(strDirectory, conversion["output_path"], strFilename)

    if os.path.exists(strPathOutput):
        iModificationTimeOutput = os.stat(strPathOutput)[stat.ST_MTIME]
        if iModificationTimeOutput > iModificationTimeConfig:
            # The configuration-file is older
            iModificationTimeInput = os.stat(strPathInput)[stat.ST_MTIME]
            if iModificationTimeOutput > iModificationTimeInput:
                # The input-file hasn't changed
                print(f'  ... "{strPathOutput}" not changed')
                return

    # open the image file
    image = loadImage(strPathInput + "/" + strFilename)

    # Resize
    image = resize(image, conversion, strPathOutput)

    # Attach a annotation
    annotate(image, conversion, strPathOutput)

    # Save to a the temporary file
    # image.save(strPathOutput)
    image.save(strPathOutput, quality=iQuality)

    # Replace the existing file if needed
    # replace_file_if_changed(strPathOutput, strPathOutputTmp)
    return


def resize(image, conversion, strPathOutput):
    """
    Resize the image
    """
    # Get default/configuration values
    iMaxHeight = conversion["size_max_height"]
    iMaxWidth = conversion["size_max_width"]

    # Calculate if resizeing is required/wanted
    iWidth, iHeight = image.size
    iOutputWidth = iMaxWidth
    iOutputHeight = iHeight * iOutputWidth // iWidth
    if iOutputHeight > iMaxHeight:
        iOutputHeight = iMaxHeight
        iOutputWidth = iWidth * iOutputHeight // iHeight
    if iOutputWidth > iWidth:
        # The image will be enlarged: This will result in bad image-quality
        # We leave the image as it was to avoid loss of quality
        print(f'  "{strPathOutput}": This image would be enlarged. Don\'t resize!')
        # shutil.copyfile(strPathInput + '/' + strFilename, strPathOutput + '/tmp_' + strFilename)
        # replace_file_if_changed(strPathOutput, strFilenameTmp, strFilename)
        # return (iWidth, iHeight)
        return image

    # Resize the image
    # return image.resize((iOutputWidth, iOutputHeight), PIL.Image.BILINEAR)
    return image.resize((iOutputWidth, iOutputHeight), PIL.Image.ANTIALIAS)


def replace_file_if_changed_obsolete(strPathOutput, strPathOutputTmp):
    """
    Do not change timestamps if file didn't change:
    The Ouput-Image is always written in a tmp-file
    and the existing file is replaced only if changed.
    """
    if not os.path.exists(strPathOutput):
        # File didn't exist yet
        os.rename(strPathOutputTmp, strPathOutput)
        return
    if filecmp.cmp(strPathOutputTmp, strPathOutput):
        # file didn't change
        os.remove(strPathOutputTmp)
        return
    # file changed
    os.remove(strPathOutput)
    os.rename(strPathOutputTmp, strPathOutput)


def annotate(image, conversion, strPathOutput):
    """
    Write an annotation to the image
    """
    # Get prepared
    dictAnnotation = conversion.get("annotation", None)
    if dictAnnotation == None:
        # No Annotation is requried
        return

    # Retrieve configuration/default values
    strText = dictAnnotation.get("text", "Created by Alpuma")
    strFont = dictAnnotation.get("font", "arial.ttf")
    iSize = dictAnnotation.get("size", 12)
    strPosition = dictAnnotation.get("position", "bottomright")
    iSpaceingH = dictAnnotation.get("spacingh", 10)
    iSpaceingV = dictAnnotation.get("spacingv", 3)
    color = dictAnnotation.get("color", "inverse")
    difference = int(dictAnnotation.get("difference", 126))

    # Prepare Annoation and calculate it's size inclusive spaceing
    while iSize >= 9:  # Solange die Schrift eine vernuenftige Groessse hat
        font = PIL.ImageFont.truetype(strFont, iSize)
        iAnnotationWidth, iAnnotationHeight = font.getsize(strText)
        iAnnotationWidth += iSpaceingH
        iAnnotationHeight += iSpaceingV
        iWidth, iHeight = image.size
        if not (iAnnotationWidth > iWidth) | (
            iAnnotationHeight > iHeight
        ):  # Genuegend Platz
            break
        iSize = iSize - 1
        print(f"Text too large; Try with smaller Font; Size {iSize}")
    else:
        print(
            f"  '{strPathOutput}': Image smaller than Annotation or Font is to smal:"
            " Don't write Annotation."
        )
        return

    # Calculate position
    if strPosition == "topleft":
        position = (iSpaceingH, iSpaceingV)
    elif strPosition == "bottomright":
        position = (iWidth - iAnnotationWidth, iHeight - iAnnotationHeight)
    else:
        print(
            f'Unknown position "{strPosition}". Please correction the configurationfile!'
        )
        position = (iSpaceingH, iSpaceingV)

    # Write Annotation
    # draw.text((0, 0), strText, font=font, fill='white')
    # draw.text((0, 0), strText, font=font, fill='red')
    draw = PIL.ImageDraw.Draw(image)
    if color != "inverse":
        draw.text(position, strText, font=font)
        return

    assert color == "inverse"
    bereich = (
        position[0],
        position[1],
        position[0] + iAnnotationWidth,
        position[1] + iAnnotationHeight,
    )
    color_n = PIL.ImageStat.Stat(image.crop(bereich)).median
    if len(color_n) == 3:  # rgb
        # print 'color old:', color_n
        # color = map(lambda x: int(255.0-x), color_n)
        def differentiate1(index):
            return differentiate(int(color_n[index]))

        def differentiate(wert):
            if wert > 127:
                wert = wert - difference
                if wert < 0:
                    return 0
                return wert
            wert = wert + difference
            if wert > 255:
                return 255
            return wert

        color = (differentiate1(0), differentiate1(1), differentiate1(2))
        # print 'color new:', color
        draw.text(position, strText, font=font, fill=color)


if __name__ == "__main__":
    go_recurse2()
