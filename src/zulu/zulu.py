#! /usr/bin/env python

#
# ZULU WEBSITE ASSEMBLER
#
# Copyright (C) 2002-2022 Peter Maerki und Hans Maerki
#
# This library is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation; either version 2.1 of the License, or (at your option) any later version.
# This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License along with this library; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# History
#   2003-05-27, Hans Maerki, Optimized access to dictionaries according to
#                            http://www.python.org/peps/pep-0290.html#looping-over-dictionaries
#   2004-02-03, Hans Maerki, Now using regular expressions for even more speed
#                            Unified the BaseDir algorithm
#                            Code review
#                            New Option: 'TraceStageOutput:'
#   2004-02-19, Hans Maerki, Tested on Mac OS X. No changes needed in this script
#   2004-02-19, Hans Maerki, Bugfix: Path will be displayed correctly in Multilanguage sites. Thanks to BeSe.
#   2004-05-11, Hans Maerki, v2.1.2: Bugfix: Sitemap: Hidden pages are hidden.
#   2004-05-30, Hans Maerki, v2.1.3: Bugfix: Sitemap: Hidden pages are hidden. Now reaaly fixed:-)
#   2005-03-09, Hans Maerki, v2.1.5: Bugfix: Better error messages.
#                                    Bugfix: v2.1.4 had version number v2.1.3!!!
#   2005-09-29, Hans Maerki, v2.1.6: Bugfix: The 'BaseDir'- and 'Input'-Entires are not mandatory anymore.
#   2005-10-24, Hans Maerki, v2.1.8--: Bugfix: Better errormessages for readonly files. Thanks to Gernot Segelbacher.
#   2006-12-24, Hans Maerki, v2.1.8: Now supports the OpenDocument format used by OpenOffice 2.x
#   2006-12-24, Hans Maerki, v2.1.8: Successfully tested on Ubuntu 6.10 and OsX Tiger
#   2019-01-17, Hans Maerki, v3.0.0: Ported to Python 3.7.2
#   2019-04-27, Hans Maerki, v4.0.0: Reads directly xlsx. The Excel-XML intermediate file becomes obsolete.
#                                    OpenOffice Write is not supported in this version.
#   2022-05-21, Hans Maerki, v4.0.1: Everything is UTF-8. Default encoding was Latin-1..
#   2025-10-24, Hans Maerki, v4.0.2: Moved to git and uv
#   2026-04-03, Hans Maerki, v4.0.3: Logfile refactored from html to text console output.
#   2026-07-13, Hans Maerki, v4.0.4: Improve error messages.
#   2026-10-21, Hans Maerki, v4.0.5: Write sitemap.xml.
#

import logging
import os
import re
import stat
import sys
import time
import typing
from xml.etree import ElementTree

from . import zulu_excel_reader

logger = logging.getLogger(__file__)

# This is needed to find zulu-modules which are stored in the current directory
sys.path.insert(0, os.path.join(os.path.abspath(os.getcwd())))

sCopyright = "Copyright Hans und Peter Maerki. LGPL."
sVersion = "v4.0.5"
sDate = "2026-10-21a"
sProduct = "Zulu Website-Assembler"


NAMESPACE_SITEMAPXML = "http://www.sitemaps.org/schemas/sitemap/0.9"
TAG_SITEMAPXML = "SitemapXml"
FILENAME_SITEMAPXML = "sitemap.xml"

dictEntries: dict[str, list[dict[str, str]]] = {}
dictOutputFiles: dict[str, str] = {}


class ZuluException(Exception):
    """Base class for exceptions in this module."""

    pass


class ZuluDontCreateFileException(Exception):
    """No need to create this file."""

    pass


patternZuluTemplate = re.compile(
    r"""#
# The whole expression matches strings like
#    <!--Zulu:Template:PathDelimiter:Page:Begin--> -> <!--Zulu:Template:PathDelimiter:Page:End-->
#
# This matches '<!--Zulu:Template:PathDelimiter:Page:Begin-->'. ':PathDelimiter:Page' -> tag
<!--Zulu:Template(?P<tag>.*?):Begin-->
#
# This matches the template itself ' -> '
(?P<template>.*?)
#
# This matches '<!--Zulu:Template:PathDelimiter:Page:Begin-->'
<!--Zulu:Template(?P=tag):End-->""",
    re.S | re.X,
)

strPatternZuluTag = r"""#
# The whole expression matches strings like (The inner Tag will be matched first)
#    Begin123<!--Zulu:Outer<!--Zulu:Inner-->-->456
#
# This matches '<!--Zulu:'
%s
#
# This matches the name of the tag: 'Inner'
# We don't allow all characters to disallow a match with inner tags.
# Zulu:Outer mustn't be matched for this example: <!--Zulu:Outer<!--Zulu:Inner-->-->
(?P<tag>[_:a-zA-Z0-9]*?)
#
# This matches '-->'
-->"""

patternZuluTag = re.compile(strPatternZuluTag % "<!--Zulu:Tag:", re.S | re.X)
patternZuluPythonTag = re.compile(strPatternZuluTag % "<!--Zulu:Python:", re.S | re.X)
ZULU_STRUCTURE = "zulu_structure"


class Zulu:
    "The Zulu Class"

    def __init__(self):
        self.listNavigations = []
        self.dictTemplates = {}
        self.dictBaseDirs = {}
        self.listTransform = []
        self.sFilenameStructure = ZULU_STRUCTURE + ".xlsx"
        self.sFilenameTemplate = None

    def open(self):
        """
        Loads the structure file: OpenOffice 'structure.sxc' is used if it exists, otherwise
        'structure.xls'is ued.
        The file is parsed an all structures prepared.
        """
        if len(sys.argv) > 1:
            try:
                import getopt

                opts, args = getopt.getopt(
                    sys.argv[1:], "st:", ["structure=", "template="]
                )
            except getopt.GetoptError as e:
                # print(help information and exit:
                # self.usage()
                raise ZuluException() from e
            for o, a in opts:
                if o in ("-s", "--structure"):
                    self.sFilenameStructure = a
                if o in ("-t", "--template"):
                    self.sFilenameTemplate = a
        else:
            if not os.path.exists(self.sFilenameStructure):
                raise ZuluException(f'File "{self.sFilenameStructure}" does not exist!')

        sLogFilename = "zulu_errorlog.html"
        print(f"Zulu: {self.sFilenameStructure} -> {sLogFilename}")
        self.objLogger = Logger(self.sFilenameStructure)
        self.objLogger.info("python version: " + sys.version)
        try:
            self.objLogger.info(f'Assembling structure "{self.sFilenameStructure}".')
            excel = zulu_excel_reader.ExcelReader(self.sFilenameStructure)
        except Exception as e:
            self.objLogger.error(f"Failed to open the document. ({e})")
            raise ZuluException() from e
        if False:
            with open(
                self.sFilenameStructure.replace(".xlsx", ".dump.txt"), "w"
            ) as obj_file:
                excel.dump(obj_file)

        for obj_table in excel.dict_tables.values():
            self.listNavigations.append(Navigation(self, obj_table))

        global dictEntries
        dictEntries = excel.dict_entries

        for dictBaseDir in dictEntries.get("BaseDir", []):
            self.dictBaseDirs[dictBaseDir["tag"]] = ""
            self.listTransform.append(TransformBaseDir(dictBaseDir))
        if "Slash2backslash" in dictEntries:
            for listSlash2backslash in dictEntries["Slash2backslash"]:
                self.listTransform.append(TransformSlash2Backslash(listSlash2backslash))

        if len(self.listNavigations) == 0:
            self.objLogger.error('No keyword "<navigation>" found: Need at least one!')
            raise ZuluException()

        self.objLogger.info(f"<navigation>-Keywords found: {len(self.listNavigations)}")

    def callPython(self, objTemplate, objProcessingState, sText):
        """
        sText hast the form "MODULE_NAME:CLASS_NAME:PARAMETER"
        This method loads 'MODULE_NAME' and calls 'CLASS_NAME'.doit().
        This allows to write own handlers for additional functionality.
        """
        try:
            (sModule, sClass, sParameter) = sText.split(":", 2)
        except ValueError as e:
            self.objLogger.error(
                f'Expected something like "<!--Zulu:Python:MODULE_NAME:CLASS_NAME:PARAMETER-->" but got "<!--Zulu:Python:{sText}-->".',
                objTemplate.strTemplateFilename,
            )
            raise ZuluException() from e

        try:
            mod = __import__(sModule)
        except ImportError as e:
            self.objLogger.error(
                f'Could not import Module "{sModule}". See "<!--Zulu:Python:{sText}-->".',
                objTemplate.strTemplateFilename,
            )
            raise ZuluException() from e

        try:
            klass = getattr(mod, sClass)
        except AttributeError as e:
            self.objLogger.error(
                f'Could not find Class "{sClass}". See "<!--Zulu:Python:{sText}-->".',
                objTemplate.strTemplateFilename,
            )
            raise ZuluException() from e

        try:
            if isinstance(klass, type):
                instance = klass()
                instance.__init__()
                return instance.doit(self, objTemplate, objProcessingState, sParameter)
        except Exception as e:
            self.objLogger.error(
                f'Error in call to "<!--Zulu:Python:{sText}-->". See traceback.',
                objTemplate.strTemplateFilename,
            )
            raise ZuluException() from e

        self.objLogger.error(
            f'Error in call to "<!--Zulu:Python:{sText}-->". This class is not registered.',
            objTemplate.strTemplateFilename,
        )
        raise ZuluException()

    def getTransform(self, sValue):
        objTemplate = Template(sValue)
        objTemplate.replace_transform(self)
        return objTemplate.strTemplate

    def replace_tags(self, objProcessingState, strTemplate, listlistReplace):
        objTemplate = Template(strTemplate)
        objTemplate.replace_tags(HandlerNavTag(listlistReplace), objProcessingState)
        return objTemplate.strTemplate

    def get_navigation_by_name(self, sName):
        for objNavigation in self.listNavigations:
            if sName == objNavigation.strName:
                return objNavigation
        raise IndexError(f'get_navigation_by_name("{sName}") not found')

    def skip_page(self, objProcessingState) -> str | None:
        # Verify if we have to create the file: If Tag 'Folder' containts '-', the page creation may be skipped
        for strBaseDirTag in self.dictBaseDirs.keys():
            for objEntry in objProcessingState.listEntries:
                if objEntry.dictTags.get(strBaseDirTag) == "-":
                    return strBaseDirTag
        return None

    def create_page(self, objProcessingState):
        strBaseDirTag = self.skip_page(objProcessingState)
        if strBaseDirTag is not None:
            self.objLogger.info(
                f'File for "{objProcessingState.getIdentification()}" will not be created: Tag "{strBaseDirTag}" is "-".'
            )
            return

        #
        # get template
        #
        strTemplateFilename = self.getOptionSingle("Template")
        if self.sFilenameTemplate:
            # print('--template option given: "{}" overrides "{}" from "{}"'.format(self.sFilenameTemplate, strTemplateFilename, self.sFilenameStructure))
            strTemplateFilename = self.sFilenameTemplate
        objTemplate = Template(strTemplateFilename)
        objHandlerTag = HandlerTag(objProcessingState)
        objTemplate.replace_tags(objHandlerTag, objProcessingState)
        strTemplateFilename = objTemplate.strTemplate
        try:
            with open(strTemplateFilename, encoding="utf-8") as f:
                objTemplate = Template(f.read(), strTemplateFilename)
        except UnicodeDecodeError as e:
            self.objLogger.error(
                f"{os.path.abspath(strTemplateFilename)}: UnicodeDecodeError {e}"
            )
            return

        objProcessingState.dictGlobalTags["ZuluTemplateName"] = strTemplateFilename
        objProcessingState.dictGlobalTags["ZuluFilenameTemplate"] = strTemplateFilename

        #
        # Add input to dictGlobalTags
        #
        for dictInput in dictEntries.get("Input", []):
            strInputTag = dictInput["tag"]
            strInputFilename = dictInput["a"]

            objInputTemplate = Template(strInputFilename)
            objInputTemplate.replace_tags(
                HandlerTag(objProcessingState), objProcessingState
            )
            strInputFilename = objInputTemplate.strTemplate
            self.verifyFilename(objProcessingState, strInputFilename)

            timeLastModified = time.localtime(os.stat(strInputFilename)[stat.ST_MTIME])
            objProcessingState.dictGlobalTags["InputLastModifiedDateTime"] = (
                time.strftime("%Y-%m-%d %H:%M:%S", timeLastModified)
            )
            objProcessingState.dictGlobalTags["InputLastModifiedDate"] = time.strftime(
                "%Y-%m-%d", timeLastModified
            )
            objProcessingState.strInputFilename = strInputFilename

            try:
                with open(strInputFilename, encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError as e:
                self.objLogger.error(
                    f"{os.path.abspath(strInputFilename)}: UnicodeDecodeError {e}"
                )
                return
            except OSError as err:
                self.objLogger.error(f"{strInputFilename} does not exist ({err})")
                return

            objInputTemplate = Template(text, strInputFilename)

            #
            # extract the Comment-Template
            #
            objInputTemplate.extract_comment(self, "")
            objInputTemplate.extract_comment(self, "Input")

            # objProcessingState.dictGlobalTags[strInputTag] = objInputTemplate.strTemplate
            objTemplate.strTemplate = objTemplate.strTemplate.replace(
                f"<!--Zulu:Tag:{strInputTag}-->", objInputTemplate.strTemplate
            )

        #
        # extract the Comment-Template
        #
        objTemplate.extract_comment(self, "Template")

        #
        # extract the templates
        #
        self.dictTemplates = objTemplate.extract_templates()
        self.write_output(
            objTemplate, objProcessingState, "_ZULUTRACE_EXTRACT_TEMPLATE"
        )

        #
        # Replace everything in the replace list
        #
        objTemplate.replace_subst(self, "Template")
        self.write_output(objTemplate, objProcessingState, "_ZULUTRACE_SUBST-TEMPLATE")

        #
        # replace the Python-Tags
        #
        objTemplate.replace_tags(
            HandlerPython(self, objProcessingState, objTemplate), objProcessingState
        )
        self.write_output(objTemplate, objProcessingState, "_ZULUTRACE_PYTHON")

        try:
            #
            # transform
            #
            for objTransform in self.listTransform:
                objTransform.transform(objTemplate, objProcessingState)
            self.write_output(objTemplate, objProcessingState, "_ZULUTRACE_TRANSFROM")

            #
            # replace the tags
            #
            objTemplate.replace_tags(HandlerTag(objProcessingState), objProcessingState)

            #
            # Replace everything in the replace list
            #
            objTemplate.replace_subst(self, "Output")
            self.write_output(
                objTemplate, objProcessingState, "_ZULUTRACE_SUBST-OUTPUT"
            )

            #
            # write output
            #
            self.write_output(objTemplate, objProcessingState, "")
        except ZuluDontCreateFileException as e:
            self.objLogger.info(str(e))

    def write_output(self, objTemplate, objProcessingState, sStage):
        iTraceStageOutput = self.getOptionSingle("TraceStageOutput", "0")
        if iTraceStageOutput != "1":
            # Skip StageOutput
            if sStage != "":
                return
        strOutputFilename = self.getOptionSingle("Output")
        strOutputFilename = strOutputFilename.replace("<!--Zulu:Stage-->", sStage)
        objOutputTemplate = Template(strOutputFilename)
        # print('strOutputFilename', strOutputFilename
        objOutputTemplate.replace_tags(
            HandlerTag(objProcessingState), objProcessingState
        )
        strOutputFilename = objOutputTemplate.strTemplate
        # print('strOutputFilename', strOutputFilename
        self.verifyFilename(objProcessingState, strOutputFilename)
        if self.getOptionSingle("PreserveArchiveBit", "0") == "1":
            # On Windows, it is handy to send only the files to the
            # server which have the archive-bit set. But when using
            # this mechanism, it is important not to write a file
            # if it hasn't been changed: To rewrite a file will reset the
            # archive bit.
            try:
                if strOutputFilename not in dictOutputFiles:
                    # We don't know this file: Load it into the cache
                    with open(strOutputFilename, encoding="utf-8") as f:
                        try:
                            text = f.read()
                        except UnicodeDecodeError as err:
                            self.objLogger.error(
                                f"{strOutputFilename}: UnicodeDecodeError {err}"
                            )
                            text = "?"
                        dictOutputFiles[strOutputFilename] = text
                if dictOutputFiles[strOutputFilename] == objTemplate.strTemplate:
                    # Content didn't change
                    return
            except OSError:
                pass
            # We have to write the file
            dictOutputFiles[strOutputFilename] = objTemplate.strTemplate

        if False:
            try:
                f = open(strOutputFilename, "w", encoding="utf-8")
            except OSError as e:
                if e.errno == 13:  # Permission denied
                    self.objLogger.error(
                        f'This file is write protected. Please remove the write protection and try again. The error message was "{e}"',
                        strOutputFilename,
                    )
                    return
                self.zuluility_createFolderRecursive(strOutputFilename)
                f = open(strOutputFilename, "w", encoding="utf-8")
            f.write(objTemplate.strTemplate)
            f.close()

        try:
            self.zuluility_createFolderRecursive(strOutputFilename)
            with open(strOutputFilename, "w", encoding="utf-8") as f:
                f.write(objTemplate.strTemplate)
        except UnicodeEncodeError as e:
            self.objLogger.error(
                f'{strOutputFilename}: {e}. Retry with "replace" instead of "strict"'
            )
            with open(strOutputFilename, "w", encoding="utf-8", errors="replace") as f:
                f.write(objTemplate.strTemplate)
        except Exception as e:
            self.objLogger.error(f"{strOutputFilename}: {e}")

    def verifyFilename(self, objProcessingState, strFilename):
        if strFilename.find("//") >= 0:
            self.objLogger.warning(
                f'Filename for "{objProcessingState.getIdentification()}" includes double "//": "{strFilename}".'
            )
        if strFilename.find("...") >= 0:
            self.objLogger.warning(
                f'Filename for "{objProcessingState.getIdentification()}" includes tripple "..": "{strFilename}".'
            )
        if strFilename.find("/./") >= 0:
            self.objLogger.warning(
                f'Filename for "{objProcessingState.getIdentification()}" includes tripple "/./": "{strFilename}".'
            )

    def getOptionSingle(self, strOption, strDefault=None):
        if strDefault is None:
            return dictEntries[strOption][0]["a"]
        try:
            return dictEntries[strOption][0]["a"]
        except Exception as _:
            return strDefault

    def combine(self, listNavigations, listEntries):
        #
        # Use recursion to create all combinations of the navigations.
        # Example: 6 Pages, 2 Outputs (normal, print), 3 Languages (d, e, f)
        # This will create 6x2x3=36 cominations. Zulu will eventually
        # create 36 html-Pages.
        #
        for objEntry in listNavigations[0].listEntries:
            if len(listNavigations) == 1:
                try:
                    objProcessingState = ProcessingState(self, listEntries + [objEntry])
                    self.create_page(objProcessingState)
                except Exception as e:
                    self.objLogger.error(f"create_page(): {e}")
                    raise
            else:
                self.combine(listNavigations[1:], listEntries + [objEntry])

    def zulu(self):
        self.combine(self.listNavigations, [])

    def zuluility_get_now(self):
        return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())

    def zuluility_createFolderRecursive(self, strFilename):
        strPath = os.path.dirname(strFilename)
        if os.path.exists(strPath):
            return
        self.objLogger.info(
            f'Creating folder "{strPath}" for file "{strFilename}".', None
        )
        os.makedirs(strPath)

    def write_sitemapxml(self, filename: str, url: str, navigation: str) -> None:
        def write_element_tree() -> None:
            def get_list_url() -> typing.Iterator[str]:
                objNavigation = self.get_navigation_by_name(navigation)
                for objEntry in objNavigation.listEntries:
                    if objEntry.bHidden:
                        continue
                    # if objEntry.anchester_is_hidden():
                    #     continue

                    objOutputTemplate = Template(url)
                    objProcessingState = ProcessingState(self, [objEntry])
                    strBaseDirTag = self.skip_page(objProcessingState)
                    if strBaseDirTag is not None:
                        continue
                    objOutputTemplate.replace_tags(
                        HandlerTag(objProcessingState), objProcessingState
                    )
                    actual_url = objOutputTemplate.strTemplate
                    yield actual_url

            ElementTree.register_namespace("", NAMESPACE_SITEMAPXML)
            urlset = ElementTree.Element(f"{{{NAMESPACE_SITEMAPXML}}}urlset")
            for _url in get_list_url():
                url_element = ElementTree.SubElement(
                    urlset, f"{{{NAMESPACE_SITEMAPXML}}}url"
                )
                ElementTree.SubElement(
                    url_element, f"{{{NAMESPACE_SITEMAPXML}}}loc"
                ).text = _url

            ElementTree.indent(urlset, space="  ")
            ElementTree.ElementTree(urlset).write(
                filename,
                encoding="UTF-8",
                xml_declaration=True,
            )

        write_element_tree()
        self.objLogger.info(f'Wrote "{filename}".', None)

    def sitemapxml(self):
        class MyWarning(Exception):
            pass

        def get_entry(tag: str, subtag: str) -> str:
            try:
                entries = dictEntries[tag]
            except KeyError as e:
                raise MyWarning(
                    f'No entry "{TAG_SITEMAPXML}:" found in "{self.sFilenameStructure}": Skip "{FILENAME_SITEMAPXML}".'
                ) from e

            for entry in entries:
                try:
                    actual_tag = entry["tag"]
                except KeyError as e:
                    raise MyWarning(
                        f'Entry "{TAG_SITEMAPXML}:" found in "{self.sFilenameStructure}": Programming error A!'
                    ) from e
                if actual_tag == subtag:
                    try:
                        value = entry["a"]
                        return value
                    except KeyError as e:
                        raise MyWarning(
                            f'Entry "{TAG_SITEMAPXML}:" found in "{self.sFilenameStructure}": Programming error B!'
                        ) from e
            raise MyWarning(
                f'Entry "{TAG_SITEMAPXML}:" found in "{self.sFilenameStructure}": Subentry "{subtag}" not found!'
            )

        try:
            navigation = get_entry(tag=TAG_SITEMAPXML, subtag="Navigation")
            filename = get_entry(tag=TAG_SITEMAPXML, subtag="Filename")
            url = get_entry(tag=TAG_SITEMAPXML, subtag="Url")
            self.write_sitemapxml(filename=filename, navigation=navigation, url=url)
        except MyWarning as mywarning:
            self.objLogger.warning(str(mywarning), self.sFilenameStructure)


class TransformBaseDir:
    "Transform BaseDir"

    def __init__(self, dictBaseDir):
        self.strTag = dictBaseDir["tag"]
        self.strSearch = dictBaseDir["a"]

    def transform(self, objTemplate, objProcessingState):
        """
        print('strTag=', self.strTag, ' strValue=', strValue, ' base_dir()=', self.base_dir(objProcessingState, strValue)

        BaseDir
        Tag             Transform        Resulting Path for '/install/index.html'
        ''              '.'                  './install/index.html'
        '/x'            '..'                '../install/index.html'
        '/x/y'          '../..'          '../../install/index.html'
        '-'             This case should never get here
        """
        strValue = HandlerTag(objProcessingState).getValue(self.strTag)
        if strValue == "-":
            raise ValueError("Internal programming error")

        if strValue == "":
            # Special case
            objTemplate.strTemplate = objTemplate.strTemplate.replace(
                self.strSearch, "."
            )
            return

        if strValue == "/":
            objProcessingState.objZulu.objLogger.error(
                f'"{objProcessingState.getIdentification()}": "/" does not make sense. If the file is in the root folder, leave the field empty.'
            )
            return

        if not strValue.startswith("/"):
            objProcessingState.objZulu.objLogger.error(
                f'"{objProcessingState.getIdentification()}": "{self.strTag}" is "{strValue}", expected to start with "/".'
            )
            return

        iCount = strValue.count("/") - 1
        strReplace = ".." + iCount * "/.."
        objTemplate.strTemplate = objTemplate.strTemplate.replace(
            self.strSearch, strReplace
        )


class TransformSlash2Backslash:
    def __init__(self, dictSlash2Backslash):
        self.strTag = dictSlash2Backslash("tag")
        self.strSearch = dictSlash2Backslash("a")

    def transform(self, objTemplate, objProcessingState):
        pass


class Entry:
    "The Entry Class"

    def __init__(self, objNavigation, obj_table, obj_row):
        self.objNavigation = objNavigation
        self.dictTags = obj_table.get_row_as_dict(obj_row)
        self.strPath = self.dictTags[objNavigation.strName]
        if self.strPath.find("-hidden") == -1:
            self.bHidden = 0
        else:
            self.bHidden = 1
            self.strPath = self.strPath.replace("-hidden", "")
            self.dictTags[objNavigation.strName] = self.strPath

    def to_be_displayed(self, strPathOfPageToBeCreated):
        # ActualEntry.to_be_displayed(strPathOfPageToBeCreated)
        # true if the parent of 'ActualEntry' is a parent
        # of 'strPathOfPageToBeCreated' or one of its parents.
        if self.objParent is None:
            # Entries with no parent are always displayed
            if self.bHidden:
                # This entry is marked as hidden (has '-hidden' in its path).
                # The entry is only displayed if a child is selected.
                return strPathOfPageToBeCreated.find(self.strPath) == 0
            return 1
        iPos = self.strPath.rfind("/")
        if iPos == -1:
            raise ValueError("to_be_displayed(): Internal programming error")
        strParent = self.strPath[:iPos]
        if strPathOfPageToBeCreated.find(strParent) == 0:
            if self.bHidden:
                # This entry is marked as hidden (has '-hidden' in its path).
                # The entry is only displayed if a child is selected.
                return strPathOfPageToBeCreated.find(self.strPath) == 0
            return 1
        return 0

    def anchester_is_hidden(self):
        if self.objParent is None:
            return 0
        if self.objParent.bHidden:
            return 1
        return self.objParent.anchester_is_hidden()


class Navigation:
    "The Navigation Class"

    def __init__(self, objZulu, obj_table):
        self.i = 0
        self.listEntries = []
        self.obj_table = obj_table
        self.strName = obj_table.str_table_name
        for obj_row in self.obj_table.list_rows:
            self.listEntries.append(Entry(self, obj_table, obj_row))

        # Calculate iLevel for each 'Entry'
        for objEntry in self.listEntries:
            objEntry.iLevel = self.get_level(objEntry.strPath)

        for objEntry in self.listEntries:
            objEntry.objParent = self.get_parent(objEntry.strPath)
            if objEntry.objParent is None:
                if objEntry.strPath.find("/", 1) != -1:
                    if not objEntry.bHidden:
                        objZulu.objLogger.warning(
                            f'Navigation "{self.strName}": Hidden entry "{objEntry.strPath}".',
                            objZulu.sFilenameStructure,
                        )

    def get_parent(self, strPath):
        # if strPath == '/referenz/private/child':
        #   print('hallo'
        iPos = strPath.rfind("/", 1)
        if iPos == -1:
            # We are a top-item
            return None
        strPath = strPath[:iPos]
        for objEntry in self.listEntries:
            if strPath == objEntry.strPath:
                # This is our Parent!
                return objEntry
        return None

    def get_level(self, strPath):
        #
        # Examples:  strPath                  return
        #            '/'                       0
        #            '/anleitung'              0
        #            '/anleitung/einfuehrung'  1
        #
        if strPath == "/":
            # special case
            return 0
        return strPath.count("/", 1)


class ProcessingState:
    "This calls keeps track of the current state of the processing of the Zulu-Site"

    def __init__(self, objZulu, listEntries):
        self.objZulu = objZulu
        self.listEntries = listEntries
        self.dictGlobalTags = {
            "ZuluVersion": sVersion,
            "ZuluProductName": sProduct + " " + sVersion,
            "ZuluExcelName": objZulu.sFilenameStructure,
            "ZuluFilenameStructure": objZulu.sFilenameStructure,
            "ZuluAssembledDateTime": objZulu.zuluility_get_now(),
        }

    def getPath(self, sTag):
        'Example: sTag="Page", return="<!--Zulu:Root-->sample_sites/index.html"'

        for objEntry in self.listEntries:
            if sTag in objEntry.dictTags:
                return objEntry.dictTags[sTag]

    def getIdentification(self):
        entries = (entry.strPath for entry in self.listEntries)
        return " <-> ".join(entries)


class HandlerTag:
    "This class handles '<!--Zulu:Tag:XXX-->'"

    def __init__(self, objProcessingState):
        self.patternZuluTag = patternZuluTag
        self.objProcessingState = objProcessingState

    def getValue(self, sTag):
        for objEntry in self.objProcessingState.listEntries:
            if sTag in objEntry.dictTags:
                return objEntry.dictTags[sTag]
        try:
            return self.objProcessingState.dictGlobalTags[sTag]
        except KeyError:
            error_tag = "ERROR_ACVX"
            msg = (
                f'"{self.objProcessingState.getIdentification()}": '
                f'Tag <!--Zulu:Tag:{sTag}--> not found. Used "{error_tag}" instead.'
            )
            self.objProcessingState.objZulu.objLogger.error(msg)
            return error_tag
            # raise IndexError('"%s": Tag <!--Zulu:Tag:%s--> not found.' % (self.objProcessingState.getIdentification(), sTag))


class HandlerNavTag:
    "This class handles '<!--Zulu:Tag:XXX-->'"

    def __init__(self, listEntries):
        self.patternZuluTag = patternZuluTag
        self.listEntries = listEntries

    def getValue(self, sTag):
        for objEntry in self.listEntries:
            if sTag in objEntry.dictTags:
                return objEntry.dictTags[sTag]
        return f"<!--Hidden_Zulu:Tag:{sTag}-->"


class HandlerPython:
    "This class handles '<!--Zulu:Python:XXX-->'"

    def __init__(self, objZulu, objProcessingState, objTemplate):
        self.patternZuluTag = patternZuluPythonTag
        self.objZulu = objZulu
        self.objProcessingState = objProcessingState
        self.objTemplate = objTemplate

    def getValue(self, sTag):
        return self.objZulu.callPython(self.objTemplate, self.objProcessingState, sTag)


def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc


class Template:
    "The Template Class"

    def __init__(self, strTemplate, strTemplateFilename=None):
        self.strTemplate = strTemplate
        self.strTemplateFilename = strTemplateFilename

    def extract_comment(self, objZulu, strType):
        for dictComment in dictEntries["Comment"]:
            if dictComment["tag"] == strType:
                strStart = dictComment["a"]
                strEnd = dictComment["b"]
                while True:
                    # Find 'strStart'
                    if strStart == "^":
                        iStartPos = 0
                    else:
                        # Find 'strEnd'
                        iStartPos = self.strTemplate.find(strStart)
                        if iStartPos == -1:
                            # Keine Template gefunden
                            break
                    if strEnd == "$":
                        iEndPos = len(self.strTemplate) - 1
                    else:
                        iEndPos = self.strTemplate.find(
                            strEnd, iStartPos + len(strStart)
                        )
                        if iEndPos == -1:
                            if strStart == "^":
                                break
                            objZulu.objLogger.error(
                                f'After "{strStart}", expected to find "{strEnd}".',
                                self.strTemplateFilename,
                            )
                            raise ZuluException()
                    # remove comment
                    self.strTemplate = (
                        self.strTemplate[0:iStartPos]
                        + self.strTemplate[iEndPos + len(strEnd) :]
                    )

    def extract_templates(self):
        def template_replace(objMatch):
            dictMatch = objMatch.groupdict()
            dictTemplates[dictMatch["tag"]] = dictMatch["template"]
            return ""

        dictTemplates = {}
        self.strTemplate = re.sub(
            patternZuluTemplate, template_replace, self.strTemplate
        )
        return dictTemplates

    def replace_tags(self, objHandler, objProcessingState):
        # Substitute now the Zulu-Tags
        def tag_replace(objMatch):
            strTag = objMatch.groupdict()["tag"]
            # TODO:
            # strTmp = objHandler.getValue(strTag)
            return objHandler.getValue(strTag)

        while True:
            strBefore = self.strTemplate
            self.strTemplate = re.sub(objHandler.patternZuluTag, tag_replace, strBefore)
            if strBefore == self.strTemplate:
                # Keep replaceing: This will allow inner Tags: "<!--Zulu:Tag:Title<!--Zulu:Tag:Langextension-->-->"
                return

    def replace_subst(self, objZulu, strType):
        try:
            for dictSubst in dictEntries["Subst"]:
                if dictSubst["tag"] == strType:
                    self.strTemplate = self.strTemplate.replace(
                        dictSubst["a"], dictSubst["b"]
                    )
        except Exception as _:
            objZulu.objLogger.warning(
                f'Subst: "{dictSubst["a"]}"->"{dictSubst["b"]}". No classification ("Template" or "Output").',
                objZulu.sFilenameStructure,
            )


class Logger:
    "A HTML Logger - Now just using python loggin"

    def __init__(self, sFilenameStructure):
        self.iErrors = 0
        self.iWarnings = 0
        self.iInfos = 0
        self.sFilenameStructure = sFilenameStructure
        logger.info(f"{sProduct} {sVersion} {self.sFilenameStructure}")

    def warning(self, sWarning, sFilename=None):
        self.iWarnings = self.iWarnings + 1
        self.generic(logger.warning, sWarning, sFilename)

    def error(self, sError, sFilename=None):
        self.iErrors = self.iErrors + 1
        self.generic(logger.error, sError, sFilename)
        logger.exception(sys.exc_info())

    def info(self, sInfo, sFilename=None):
        self.iInfos = self.iInfos + 1
        self.generic(logger.info, sInfo, sFilename)

    def generic(self, logger_func, sInfo, sFilename):
        if sFilename is None:
            sFilename = self.sFilenameStructure

        logger_func(f"{sFilename}: {sInfo}")

    def close(self):
        f = logger.info
        if self.iWarnings > 0:
            f = logger.warning
        if self.iErrors > 0:
            f = logger.error
        f(f"Errors: {self.iErrors}, Warnings: {self.iWarnings}")


#
# PageNavigation
#
# The following code only refers:
# from zulu import Zulu
# import string
class path:
    "This class creates a HTML-Path based on templates"

    def __init__(self):
        pass

    def doit(self, objZulu, objTemplate, objProcessingState, sParameter):
        """Example: sParameter='Page'   # The path will be created for the navigation 'Page'"""

        objNavigation = objZulu.get_navigation_by_name(sParameter)
        # sPagePath ist the path of the page we are going to create
        sPagePath = objProcessingState.getPath(sParameter)
        # Get template '<!--Zulu:Template:PathDelimiter:Page'
        strTemplate = objZulu.dictTemplates[":PathDelimiter:" + sParameter]
        strTemplateDelimiter = objZulu.replace_tags(objProcessingState, strTemplate, [])
        strReturn = ""
        for objEntry in objNavigation.listEntries:
            # sCurrentPath is the page of the page we actually loop throu
            sCurrentPath = objEntry.strPath
            if sPagePath.find(sCurrentPath) == 0:
                # Example:
                #   sCurrentPath = '/anleitung'
                #   sPagePath = '/anleitung/einfuehrung'
                # Get template '<!--Zulu:Template:Path:Page'
                strTemplate = objZulu.dictTemplates[":Path:" + sParameter]
                # strTemplatePath = objZulu.replace_tags(objProcessingState, strTemplate, [objEntry])
                strTemplatePath = objZulu.replace_tags(
                    objProcessingState,
                    strTemplate,
                    [objEntry] + objProcessingState.listEntries,
                )
                strTemplatePath = strTemplatePath.replace(
                    "<!--Hidden_Zulu:", "<!--Zulu:"
                )
                if sPagePath == sCurrentPath:
                    return strReturn + strTemplatePath
                else:
                    strReturn = strReturn + strTemplatePath + strTemplateDelimiter
        raise IndexError("Internal Programming error")


#
# PageNavigation
#
class menu:
    "This class creates a menu based on templates"

    def __init__(self):
        pass

    def doit(self, objZulu, objTemplate, objProcessingState, sParameter):
        """Example: sParameter='Page:0:0'   # The menu will be created for the navigation 'Page'. 0:0 stands for 'openAllMenues':'selectParentEntries'"""

        try:
            (sNavigation, sOpenAllMenues, sSelectParentEntries) = sParameter.split(":")
        except ValueError as e:
            objZulu.objLogger.error(
                f'Expected something like "<!--Zulu:Python:MODULE_NAME:CLASS_NAME:NAVIGATION:1:1-->" but got "<!--Zulu:Python:menu:{sParameter}-->".',
                objTemplate.strTemplateFilename,
            )
            raise ZuluException() from e

        objNavigation = objZulu.get_navigation_by_name(sNavigation)
        strReturn = ""
        sPagePath = objProcessingState.getPath(sNavigation)
        for objEntry in objNavigation.listEntries:
            sCurrentPath = objEntry.strPath
            # if self.to_be_displayed(sOpenAllMenues, objEntry):
            if sOpenAllMenues == "1" or objEntry.to_be_displayed(sPagePath):
                if sCurrentPath == sPagePath or (
                    sSelectParentEntries == "1" and sPagePath.find(sCurrentPath) == 0
                ):
                    strTemplateName = (
                        f":Selected:{objNavigation.strName}:{objEntry.iLevel}"
                    )
                else:
                    strTemplateName = (
                        f":Normal:{objNavigation.strName}:{objEntry.iLevel}"
                    )
                # Examples ':Normal:Page:0', ':Selected:Page:0'
                try:
                    strTemplate = objZulu.dictTemplates[strTemplateName]
                    sTmp = objZulu.replace_tags(
                        objProcessingState,
                        strTemplate,
                        [objEntry] + objProcessingState.listEntries,
                    )
                    sTmp = sTmp.replace("<!--Hidden_Zulu:", "<!--Zulu:")
                    strReturn = strReturn + sTmp
                except KeyError:
                    objZulu.objLogger.warning(
                        f"Template <!--Zulu:Template{strTemplateName}--> not found.",
                        objTemplate.strTemplateFilename,
                    )
        return strReturn


#
# Sitemap
#
class sitemap(menu):
    "This class creates a sitemap based on templates"

    def __init__(self):
        pass

    def doit(self, objZulu, objTemplate, objProcessingState, sParameter):
        """Example: sParameter='Page'   # The menu will be created for the navigation 'Page'."""

        try:
            (sNavigation, sOpenAllMenues, sSelectParentEntries) = sParameter.split(":")
            # Backward-Compatibility
            objZulu.objLogger.warning(
                f'This version of Zulu expects something like "<!--Zulu:Python:sitemap:Page-->" but got "<!--Zulu:Python:sitemap:{sParameter}-->".',
                objProcessingState.strInputFilename,
            )
        except ValueError:
            # This is the normal case
            sNavigation = sParameter

        objNavigation = objZulu.get_navigation_by_name(sNavigation)
        strReturn = ""
        for objEntry in objNavigation.listEntries:
            if objEntry.bHidden:
                continue
            if objEntry.anchester_is_hidden():
                continue
            strTemplateName = f":Sitemap:{objNavigation.strName}:{objEntry.iLevel}"
            # Examples ':Sitemap:Page:0', ':Selected:Page:0'
            try:
                strTemplate = objZulu.dictTemplates[strTemplateName]
                sTmp = objZulu.replace_tags(
                    objProcessingState,
                    strTemplate,
                    [objEntry] + objProcessingState.listEntries,
                )
                sTmp = sTmp.replace("<!--Hidden_Zulu:", "<!--Zulu:")
                strReturn = strReturn + sTmp
            except KeyError:
                objZulu.objLogger.warning(
                    f"Template <!--Zulu:Template{strTemplateName}--> not found.",
                    objTemplate.strTemplateFilename,
                )
        return strReturn


#
# PageNavigation
#
class menu_level:
    "This class creates a menu based on templates. Only the menu at the selected levels will be created."

    def __init__(self):
        pass

    def doit(self, objZulu, objTemplate, objProcessingState, sParameter):
        """Example: sNavigation='Page:0:1'   # The menu will be created for the navigation 'Page'. The levels 0 to 1 will be created."""

        try:
            (sNavigation, sLevelFrom, sLevelTo) = sParameter.split(":")
            iLevelFrom = int(sLevelFrom)
            iLevelTo = int(sLevelTo)
        except ValueError as e:
            objZulu.objLogger.error(
                f'Expected something like "<!--Zulu:Python:MODULE_NAME:CLASS_NAME:NAVIGATION:1:1-->" but got "<!--Zulu:Python:menu:{sParameter}-->".',
                objProcessingState.strInputFilename,
            )
            raise ZuluException() from e

        objNavigation = objZulu.get_navigation_by_name(sNavigation)
        strReturn = ""
        sPagePath = objProcessingState.getPath(sNavigation)
        for objEntry in objNavigation.listEntries:
            sCurrentPath = objEntry.strPath
            if objEntry.to_be_displayed(sPagePath):
                if (objEntry.iLevel >= iLevelFrom) and (objEntry.iLevel <= iLevelTo):
                    if (sCurrentPath == sPagePath) or (
                        sPagePath.find(sCurrentPath) == 0
                    ):
                        strTemplateName = (
                            f":Selected:{objNavigation.strName}:{objEntry.iLevel}"
                        )
                    else:
                        strTemplateName = (
                            f":Normal:{objNavigation.strName}:{objEntry.iLevel}"
                        )
                    # Examples ':Normal:Page:0', ':Selected:Page:0'
                    try:
                        strTemplate = objZulu.dictTemplates[strTemplateName]
                        sTmp = objZulu.replace_tags(
                            objProcessingState,
                            strTemplate,
                            [objEntry] + objProcessingState.listEntries,
                        )
                        sTmp = sTmp.replace("<!--Hidden_Zulu:", "<!--Zulu:")
                        strReturn = strReturn + sTmp
                    except KeyError:
                        objZulu.objLogger.warning(
                            f"Template <!--Zulu:Template{strTemplateName}--> not found.",
                            objTemplate.strTemplateFilename,
                        )
        return strReturn


def main_():
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")
    if True:
        zulu = Zulu()
        zulu.open()
        zulu.zulu()
        zulu.sitemapxml()
        zulu.objLogger.close()

    return 0

    zulu = Zulu()
    try:
        zulu.open()
        zulu.zulu()
    except ZuluException:
        # Error was already logged
        pass
    except:  # noqa: E722
        zulu.objLogger.error("")
    if zulu.objLogger.iErrors > 0:
        return 1
    return 0


def main():
    sys.exit(main_())


if __name__ == "__main__":
    main()
