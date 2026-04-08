"""
2005-2026, Hans Maerki, License LGPL

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
  2025-10-24, v2.3.5, Hans Maerki. Moved to git and uv.
  2026-04-02, v2.3.6, Hans Maerki. Add typehints and use pathlib.
"""

import filecmp
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import PIL.ImageOps
import PIL.ImageStat

VERSION = "2.3.6"

CONFIG_DEFAULT = {
    "html_filename": None,
    # 'recurse': {'top_directory': '.',}
}

CONFIG_FILENAME = "alpuma_config.txt"


def main() -> None:
    topDirectory = Path.cwd().resolve()

    listAlpumaDirectories: list[Path] = []
    for strDirectory, _listDirectories, listFilenames in os.walk(topDirectory):
        if CONFIG_FILENAME in listFilenames:
            listAlpumaDirectories.append(Path(strDirectory))

    listAlpumaDirectories.sort()

    for strAlpumaDirectory in listAlpumaDirectories:
        print(f"Found: {strAlpumaDirectory / CONFIG_FILENAME}")

    for strAlpumaDirectory in listAlpumaDirectories:
        print(f'PROCESSING "{strAlpumaDirectory}"')
        os.chdir(strAlpumaDirectory)
        go(strAlpumaDirectory)


def read_text(filename: Path) -> str:
    for encoding, mandatory in (("utf-8", False), ("iso-8859-1", True)):
        try:
            return filename.read_text(encoding=encoding)
        except UnicodeDecodeError:
            if mandatory:
                raise
            continue
    raise NotImplementedError()


def go(strAlpumaDirectory: Path) -> None:
    """
    Album assembler
    Precondition
      go_recurse2() set cwd to the directory where 'CONFIG_FILENAME'
    """
    config_file = strAlpumaDirectory / CONFIG_FILENAME
    try:
        config_file_text = read_text(config_file)
    except UnicodeDecodeError as e:
        print(f"ERROR processing: {config_file}")
        print(repr(e))
        return
    try:
        code = compile(config_file_text, config_file, "exec")
    except Exception as e:
        print(f"ERROR processing: {config_file}")
        print(repr(e))
        return

    global_vars = {}
    config = CONFIG_DEFAULT.copy()
    exec(code, global_vars, config)
    if config.get("alpuma_config_version", None) != "1.0.0":
        raise ValueError(f"This Alpuma-Version is too old for this '{CONFIG_FILENAME}'")

    html_filename = config.get("html_filename")
    if (html_filename is None) or (html_filename != Path(html_filename).name):
        raise ValueError(
            f'ERROR: "{Path.cwd().resolve() / CONFIG_FILENAME}": Expecting just a simple filename but gut "html_filename = \'{html_filename}\'"!'
        )

    iModificationTimeConfig = Path(CONFIG_FILENAME).stat().st_mtime

    dictRecurse = config.get("recurse", None)
    if dictRecurse is not None:
        go_recurse(
            config,
            iModificationTimeConfig,
            strAlpumaDirectory / dictRecurse["top_directory"],
        )
        return

    goDirectory(config, iModificationTimeConfig, strAlpumaDirectory)


def go_recurse(
    config: dict[str, Any],
    iModificationTimeConfig: float,
    topDirectory: Path,
) -> None:
    """
    If there is a directory "input_path" (typically "images") in the current directory,
    we process this directory.
    Otherwise we recurse down into the subdirectories.
    """
    listDirectories = list(topDirectory.iterdir())
    if any(path.name == config["input_path"] for path in listDirectories):
        goDirectory(config, iModificationTimeConfig, topDirectory)
        return

    listDirectoriesFull: list[Path] = []
    for directory in listDirectories:
        if directory.name.startswith("."):
            continue
        if not directory.is_dir():
            continue
        listDirectoriesFull.append(directory)

    for directoryFull in listDirectoriesFull:
        go_recurse(config, iModificationTimeConfig, directoryFull)


def goDirectory(
    config: dict[str, Any],
    iModificationTimeConfig: float,
    directory: Path,
) -> None:
    # Open the content-html file. If any or needed...
    if not directory.exists():
        raise FileNotFoundError(
            f'ERROR: Directory does not exist "{directory.resolve()}".'
        )
    html_filename = config.get("html_filename")
    FilenameHTML = directory / html_filename if html_filename is not None else None
    strContent: str = config.get("html_template_file", "")
    if FilenameHTML is not None:
        try:
            strContent = FilenameHTML.read_text()
        except OSError as _e:
            print(
                f'Template "{config.get("html_filename")}" not found: Use template from "{CONFIG_FILENAME}".'
            )

    # Loop over all files in the images directory
    OrigDirectory = directory / str(config.get("input_path"))
    if not OrigDirectory.exists():
        raise FileNotFoundError(f'ERROR: Directory does not exist "{OrigDirectory}".')
    for filePath in getFiles(OrigDirectory):
        strFileRoot = filePath.stem
        strFileExt = filePath.suffix
        strFilename = filePath.name
        dictParams = {
            "file": strFilename,
            "fileroot": strFileRoot,
            "fileext": strFileExt,
        }
        print(f"Processing {directory.resolve() / strFilename} ...")

        # Convert the images
        for conversion in config.get("conversions", []):
            strOutputPath = directory / str(conversion["output_path"])
            if not strOutputPath.exists():
                print(f"  Create folder {strOutputPath} ...")
                strOutputPath.mkdir()
            convert_image(
                config, iModificationTimeConfig, directory, strFilename, conversion
            )

        if FilenameHTML is not None:
            # Update the HTML-File if needed
            strContent = updateContent(
                config,
                strContent,
                str(directory),
                strFilename,
                dictParams,
            )

    if FilenameHTML is not None:
        print(f"  Write {FilenameHTML} ...")
        FilenameHTML.write_text(strContent)


def getFiles(path: Path) -> list[Path]:
    # Loop over all files in the images directory
    files = sorted(path.iterdir(), reverse=True)
    return [
        entry
        for entry in files
        if entry.is_file() and entry.suffix in (".gif", ".jpg", ".png")
    ]


def updateContent(
    config: dict[str, Any],
    strContent: str,
    strDirectory: str,
    strFilename: str,
    dictParams: Mapping[str, Any],
) -> str:
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
        for strFullPath in config.get("html_img_files", []):
            strFullPath = getTemplate(strFullPath, dictParams)
            iPathStart = strContentLower.find(strFullPath.lower(), iStart, iEnd)
            if iPathStart != -1:
                # We found the entry we are looking for. Update it
                # Get the first image in the list
                for strFullImagePath in config.get("html_img_files", []):
                    strHrefImagePath = getTemplate(strFullImagePath, dictParams)
                    strFullImagePath = str(Path(strDirectory) / strHrefImagePath)
                    if Path(strFullImagePath).exists():
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
    return strContent


def updateEntryInContent(
    strContent: str,
    strFullPath: str,
    strHrefImagePath: str,
    strFullImagePath: str,
    strFilename: str,
    dictParams: Mapping[str, Any],
    iStart: int,
    iEnd: int,
) -> str:
    strEntry = strContent[iStart:iEnd]
    if strFullPath != strHrefImagePath:
        strEntry = strEntry.replace(strFullPath, strHrefImagePath)
        print(f'  Renaming HTML "{strFullPath}" -> "{strHrefImagePath}".')
    if strHrefImagePath.find(strFilename) == -1:
        # Replace path if needed (case 'thumbs/{fileroot}_alpuma_override{fileext}')
        print(f'  Overriding HTML "{strHrefImagePath}".')
    strEntry = updateEntry(strEntry, strFullImagePath, dictParams)
    return strContent[:iStart] + strEntry + strContent[iEnd:]


def updateEntry(
    strEntry: str,
    strFullImagePath: str,
    _dictParams: Mapping[str, Any],
) -> str:
    image = loadImage(strFullImagePath)
    iWidth, iHeight = image.size
    strEntry = replaceSize(strEntry, "width=", iWidth)
    strEntry = replaceSize(strEntry, "height=", iHeight)
    return strEntry


def addEntry(
    config: dict[str, Any],
    strContent: str,
    dictParams: Mapping[str, Any],
) -> str:
    if strContent.find("<!--AlpumaInsert-->") >= 0:
        strLeft, strRight = strContent.split("<!--AlpumaInsert-->", 1)
    else:
        strLeft = ""
        strRight = strContent
    strEntry = getTemplate(config.get("html_template_image", ""), dictParams)
    return strLeft + "<!--AlpumaInsert-->" + strEntry + strRight


def getTemplate(strTemplate: str, dictParams: Mapping[str, Any]) -> str:
    for strTag, strValue in dictParams.items():
        strTemplate = strTemplate.replace(f"{{{strTag}}}", str(strValue))
    return strTemplate


def replaceSize(strEntry: str, strPattern: str, iValue: int) -> str:
    try:
        strStart, strValue = strEntry.split(strPattern + '"', 1)
        strValue, strEnd = strValue.split('"', 1)
    except ValueError:
        # strPattern not found. Add it at the end.
        return f'{strEntry} {strPattern}"{iValue}"'
    # Pattern found. Update the size.
    return f'{strStart}{strPattern}"{iValue}"{strEnd}'


def loadImage(strFilename: str | Path) -> PIL.Image.Image:
    with open(strFilename, "rb") as fp:
        image = PIL.Image.open(fp)
        image.load()
        image = PIL.ImageOps.exif_transpose(image)
        return image


def convert_image(
    config: dict[str, Any],
    iModificationTimeConfig: float,
    directory: Path,
    strFilename: str,
    conversion: Mapping[str, Any],
) -> None:
    # Get default/configuration values
    iQuality = conversion.get("quality", 100)  # Default for quality if not defined.
    strPathInput = directory / str(config.get("input_path"))
    strPathOutput = directory / str(conversion["output_path"]) / strFilename

    if strPathOutput.exists():
        iModificationTimeOutput = strPathOutput.stat().st_mtime
        if iModificationTimeOutput > iModificationTimeConfig:
            # The configuration-file is older
            iModificationTimeInput = strPathInput.stat().st_mtime
            if iModificationTimeOutput > iModificationTimeInput:
                # The input-file hasn't changed
                print(f'  ... "{strPathOutput}" not changed')
                return

    # open the image file
    image = loadImage(strPathInput / strFilename)

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


def resize(
    image: PIL.Image.Image,
    conversion: Mapping[str, Any],
    strPathOutput: str | Path,
) -> PIL.Image.Image:
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
    return image.resize((iOutputWidth, iOutputHeight), PIL.Image.Resampling.LANCZOS)


def replace_file_if_changed_obsolete(strPathOutput: str, strPathOutputTmp: str) -> None:
    """
    Do not change timestamps if file didn't change:
    The Ouput-Image is always written in a tmp-file
    and the existing file is replaced only if changed.
    """
    path_output = Path(strPathOutput)
    path_output_tmp = Path(strPathOutputTmp)
    if not path_output.exists():
        # File didn't exist yet
        path_output_tmp.rename(path_output)
        return
    if filecmp.cmp(path_output_tmp, path_output):
        # file didn't change
        path_output_tmp.unlink()
        return
    # file changed
    path_output.unlink()
    path_output_tmp.rename(path_output)


def annotate(
    image: PIL.Image.Image,
    conversion: Mapping[str, Any],
    strPathOutput: str | Path,
) -> None:
    """
    Write an annotation to the image
    """
    # Get prepared
    dictAnnotation = conversion.get("annotation", None)
    if dictAnnotation is None:
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

    def load_font(font_name: str, size: int) -> PIL.ImageFont.FreeTypeFont:
        # Arial is often missing on Linux; try common alternatives before fallback.
        for candidate in (font_name, "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
            try:
                font = PIL.ImageFont.truetype(candidate, size)
                assert isinstance(font, PIL.ImageFont.FreeTypeFont)
                return font
            except OSError:
                continue
        print(
            f"Font '{font_name}' not found for '{strPathOutput}'. "
            "Using Pillow default font."
        )
        font = PIL.ImageFont.load_default()
        assert isinstance(font, PIL.ImageFont.FreeTypeFont)
        return font

    # Prepare Annotation and calculate it's size inclusive spaceing
    while iSize >= 9:
        # Solange die Schrift eine vernuenftige Groessse hat
        font = load_font(strFont, iSize)
        bbox = font.getbbox(strText)
        iAnnotationWidth = bbox[2] - bbox[0]
        iAnnotationHeight = bbox[3] - bbox[1]
        iAnnotationWidth += iSpaceingH
        iAnnotationHeight += iSpaceingV
        iWidth, iHeight = image.size
        if not (iAnnotationWidth > iWidth) | (iAnnotationHeight > iHeight):
            # Genuegend Platz
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
    main()
