
"""
  2004-02-08, Hans Maerki, License LGPL

  Doubleclicking this fill will create a backupset
  based on the configuration-file named 'pyckup_config.txt'.

  Installation:
    Run the following installers to install python.
    http://www.python.org/ftp/python/2.2.2/Python-2.2.2.exe
    It is a good idea to accept the installer's default settings.

    Now move this script into the folder with the images and
    double click it.
    If there is an error - you have about half a millisecond to
    see it. If this is to quick, open a dos-window, cd to the
    directory type "pyckup.py". Now you will see the error message.

  Description:
    Write ZIP-Backup-Files from a set of directories.
    Log-Output in HTML.
    The size of a ZIP-File may be limited to fit on a CDROM.
    Use regular expressions to define files to include/exclude.
    Use regular expressions to define files not to be compressed.

  Pseudocode:
    for backup in 'pyckup_config.txt':backups
      create zip-file
      for file in folder
        write file to zipfile
        if zipfile too big
          create new zipfile

  History:
    2004-02-09, v1.0.0, Hans Maerki. Python rules!
    2004-02-10, v1.0.1, Hans Maerki. Don't compress some files (zip, jpg, ...)
    2004-09-04, v1.0.2, Hans Maerki. Better error message for fatal-errors
    2006-08-20, v1.0.3, Hans Maerki. Now 'backup_filename' in 'pyckup_config.txt'
                                     may include date and time. This allows to
                                     write each backup-run in it's own directory.
    2006-08-20, v1.0.3, Hans Maerki. The logger uses relative path names in
                                     the href's now. Before the path names where
                                     absolute, confusing firefox.
    2007-11-25, v1.0.4, Hans Maerki. Bugfix: Files with Date 2099 made call
                                     to self.objZip.write(strFilename) crash.
                                       C:\data\backup\pyckup_allgemein\pyckup.py", line 499
                                       mtime = time.localtime(st.st_mtime)
    2007-11-10, v1.0.5, Hans Maerki. Bessere Fehlermeldung
    2008-05-28, v1.0.6, Hans Maerki. Angepasst an Python 2.5
    2012-07-22, v1.0.7, Hans Maerki. AllowZIP64 Extensions
    2015-04-25, v1.0.8, Hans Maerki. Skip directories including 'pyckup_skip.txt'
    2018-01-28, v1.0.9, Hans Maerki. Not prints the exception in case of an error.
    2018-01-28, v1.1.0, Hans Maerki. Bugfix with ZIP64.
                                     Now uses zipfile2 which is python 2.7.14: https://github.com/python/cpython/commits/2.7/Lib/zipfile.py
    2019-01-17, v1.1.1, Hans Maerki. Ported to python 3.7.2.
"""
PYCKUP_VERSION = "1.1.1"

# from logger import *
##########################################################################################
####################################### logger.py START
##########################################################################################
import string, sys, codecs, types, os
import html
import zipfile
from time import localtime, strftime

OK='OK'
FAILED='FAILED'
ERROR='ERROR'
FATAL='FATAL'
INFO='INFO'
TRACE='TRACE'
DEBUG='DEBUG'

class Logger:
  "The Logger Class"

  dictClasses = {
    OK: ('OK', 'Endanwender', 'Der Sonsor konnte erfolgreich abgeglichen werden.'),
    FAILED: ('FAILED', 'Endanwender', 'Der Sonsor konnte nicht abgeglichen werden.'),
    INFO: ('INFO', 'Endanwender', 'Eine Mitteilung'),
    ERROR: ('ERROR', 'Betreuer des Messplatzes', 'Fehler bei der Kommunikation mit der Peripherie'),
    TRACE: ('TRACE', 'Betreuer des Messplatzes', 'Hilfreiche Zusatzinformation'),
    DEBUG: ('DEBUG', 'Softwareentwickler', 'Fuer die Fehlersuche bestimmte Information'),
    FATAL: ('FATAL', 'Softwareentwickler', 'Programmierfehler'),
  }
  listClasses = (OK, FAILED, INFO, ERROR, TRACE, DEBUG, FATAL)

  def __init__(self, strFilenameLog, dictValues={'title': 'Title', 'html': '<h1>Title</h1>'}, iRefresh=0):
    strFilenameLog = strFilenameLog.replace('.html', '')
    sProduct = 'DDT663'
    sVersion = '0.0.1'
    self.iRef = 1
    dictValues.update({'now': self.get_now()})
    if iRefresh > 0:
      dictValues['refresh'] = '<meta http-equiv="refresh" content="%d">' % iRefresh
    else:
      dictValues['refresh'] = ''
    strHeader = """<html>
        <head>
        <title>%(title)s</title>
        %(refresh)s
        <meta http-equiv="content-type" content="text/html;charset=iso-8859-1">
              <style type="text/css">
              <!--
                code {font-family: "Courier New", Courier, mono; color: #336699}
                pre  {font-family: "Courier New", Courier, mono; font-size: 9pt;
                      color: black; background-color: #eeeeee;
                      border: 1pt solid; border-color: #336699; width: 0;
                      padding-right: 7pt; padding-left: 7pt; padding-top: 7pt; padding-bottom: 7pt;
                      overflow: auto; width: auto; white-space: pre; }
                body {font-family: Arial; color: #000000; margin: 1}
                p    {font-family: Arial; color: #000000; margin: 1}
                tr   {font-family: Arial; color: #000000; margin: 1}
                h1_   {font-family: Arial; font-weight: bold; color: #336699; margin-top: 14; margin-bottom: 10}
                h2_   {font-family: Arial; font-weight: bold; color: #336699; margin-top: 14; margin-bottom: 8}
                h3_   {font-family: Arial; font-weight: bold; color: #336699; margin-top: 14; margin-bottom: 8}
                h4_   {font-family: Arial; font-weight: bold; color: #336699; margin-top: 14; margin-bottom: 8}
                h1   {font-family: Arial; font-weight: bold; margin-top: 14; margin-bottom: 10}
                h2   {font-family: Arial; font-weight: bold; margin-top: 14; margin-bottom: 8}
                h3   {font-family: Arial; font-weight: bold; margin-top: 14; margin-bottom: 8}
                h4   {font-family: Arial; font-weight: bold; margin-top: 14; margin-bottom: 8}
                td   {font-family: Arial; font-size: small}
                th   {font-family: Arial; font-weight: bold; font-size: small}
                li   {font-family: Arial; color: #000000; margin-top: 1}
                ul   {margin-top: 2; margin-bottom: 2}
                ol   {margin-top: 2; margin-bottom: 2}
                hr   {color: #336699; height: 1px}
                b    {color: #336699}
                a          {color: #336699}
                a:hover    {color: #000077}
                a:visited  {color: #996699}
                .OK, a.OK, a.OK:hover, a.OK:visited
                  { COLOR: green; font-weight: bold }
                .FAILED, a.FAILED, a.FAILED:hover, a.FAILED:visited
                  { COLOR: blue; font-weight: bold }
                .ERROR, a.ERROR, a.ERROR:hover, a.ERROR:visited
                  { COLOR: orange; font-weight: bold }
                .FATAL, a.FATAL, a.FATAL:hover, a.FATAL:visited
                  { COLOR: red; font-weight: bold; padding-top: 14pt; padding-bottom: 0pt }
                .INFO, a.INFO, a.INFO:hover, a.INFO:visited
                  { COLOR: black }
                .TRACE, a.TRACE, a.TRACE:hover, a.TRACE:visited
                  { COLOR: gray;  font-size: x-small }
                .DEBUG, a.DEBUG, a.DEBUG:hover, a.DEBUG:visited
                  { COLOR: gray; font-style: italic;  font-size: xx-small }
                .SMALLLINK { COLOR: red; font-style: italic;  font-size: xx-small }
                .SMALLLINK:hover { COLOR: red; text-decoration: none }
                .SMALLLINK:visited { COLOR: red; text-decoration: none }
              -->
              </style>
	</head>
	<p><font size="-2">%(now)s</font></p>
	%(html)s\n""" % dictValues

    self.strLogFile = "%s.html" % strFilenameLog
    self.strDebugFile = "%s_debug.html" % strFilenameLog
    self.logFile = codecs.open(self.strLogFile, 'w', "utf-8")
    self.debugFile = codecs.open(self.strDebugFile, 'w', "utf-8")
    self.logFile.write(strHeader)
    self.debugFile.write(strHeader)
    self.dictCounters = {}
    for strClass in self.listClasses:
      self.dictCounters[strClass] = 0

  def write(self, strLine, strClass=OK):
    self.debugFile.write(strLine)
    self.debugFile.flush()
    if strClass in (TRACE, DEBUG):
      return
    self.logFile.write(strLine)
    self.logFile.flush()

  def log(self, strClass, strInfo, strLink=None, strTag='p'):
    print('%s: %s' % (strClass, strInfo))
    self.dictCounters[strClass] = self.dictCounters[strClass] + 1
    self.iRef = self.iRef + 1
    if strLink == None:
      # strInfo = escape(strInfo)
      pass
    else:
      strLink = self.relativepath(strLink)
      strInfo = '<a class="%s" href="%s">%s</a>' % (strClass, strLink, html.escape(strInfo))
    for objFile, strRefLink, listExclude in ((self.debugFile, self.strLogFile, ()), (self.logFile, self.strDebugFile, (TRACE, DEBUG))):
      if not strClass in listExclude:
        dictValues = {
          'tag': strTag,
          'class': strClass,
          'ref': self.iRef,
          'reflink': os.path.basename(strRefLink),
          'info': strInfo,
        }
        strLine = '<%(tag)s class="%(class)s"><a name="ref%(ref)d" class="SMALLLINK" href="%(reflink)s#ref%(ref)d">-&nbsp;&nbsp;</a>%(info)s</%(tag)s>\n' % dictValues
        try:
          objFile.write(strLine)
          if strClass == 'FATAL':
            self.print_exception(objFile)
        except UnicodeError as e:
          objFile.write("<<< UnicodeError: Meldung unterdruckt>>>")
        try:
          objFile.flush()
        except:
          pass

  def title(self, strClass, strInfo, strLink=None):
    self.log(strClass, strInfo, strLink, 'h1')

  def pre(self, strClass, strInfo, strLink=None):
    self.log(strClass, strInfo, strLink, 'pre')

  def table(self, strClass, strTitle, listHeader, listRows):
    # strLine = '<h3>%s</h3>\n' % escape(strTitle)
    # self.write(strLine, strClass)
    self.log(strClass, strTitle, None, 'h2')
    self.write('<table border="1" cellpadding="3" cellspacing="0" bordercolordark="white" bordercolorlight="gray">\n', strClass)
    self.write('<tr>\n', strClass)
    for listColumn in listHeader:
      # self.write('<th>%s</th>\n' % (listColumn), strClass)
      self.write('<td>%s</td>\n' % (listColumn), strClass)
    self.write('</tr>\n', strClass)
    for listRow in listRows:
      self.write('<tr>\n', strClass)
      for listColumn in listRow:
        # Transform Tuple into List
        if len(listColumn) == 3:
          listText = [listColumn[0], listColumn[1], listColumn[2]]
        else:
          listText = [listColumn[0], listColumn[1]]
        if listText[1] == '':
          # Leere Felder in Tabellen erhalten keinen Rahmen, was haesslich aussieht.
          # Ein '-' hingegen wird mir Rahmen gezeichnet!
          listText[1] = '-'
        self.write('<td>%s</td>\n' % (self.__get_text(listText[1:], listText[0])), strClass)
      self.write('</tr>\n', strClass)
    self.write('</table>\n', strClass)

  def log_dict(self, strClass, dictDump, strTitle):
    listMembers = []
    for strMember, objMember in dictDump.iteritems():
      listMembers.append(((INFO, strMember), (INFO, str(objMember))))
    self.table(strClass, strTitle, ('Member', 'Wert'), listMembers)

  def log_image(self, strClass, strFilename, strLink=None, strAlt=""):
    self.write('<p>', strClass)
    if strLink != None:
      strLink = self.relativepath(strLink)
      self.write('<a href="%s">' % strLink, strClass)
    self.write('<img src="%s" alt="%s">' % (strFilename, strAlt), strClass)
    if strLink != None:
      self.write('</a>\n', strClass)
    self.write('</p>', strClass)

  def log_object(self, strClass, objDump, strTitle):
    listTypes = (types.StringType, types.DictType, types.FloatType, types.IntType, types.ListType, types.LongType, types.NoneType, types.TupleType, types.UnicodeType)
    dict = {}
    for strElement in dir(objDump):
        objElement = getattr(objDump, strElement)
        if type(objElement) in listTypes:
          dict[strElement] = objElement
    self.log_dict(strClass, dict, strTitle)

  def __get_text(self, listText, strClass=None):
    #
    # Beispiel
    #   listText = ('Python', 'http://www.python.org')
    #   strClass = None
    #   -> return '<a href="http://www.python.org">Python</a>
    #
    # Beispiel
    #   listText = ('Python', 'http://www.positron.ch')
    #   strClass = ERROR
    #   -> return '<a href="http://www.python.org"><code class="ERROR">Python</code></a>
    #
    # Beispiel
    #   listText = ('Python')
    #   strClass = ERROR
    #   -> return '<code class="ERROR">Python</code>
    #
    strInfo = listText[0]
    if strClass != None:
      strInfo = '<code class="%s">%s</code>' % (strClass, cgi.escape(strInfo))
    # Linefeeds sollen in HTML als <br> wiedergegeben werden
    strInfo = string.replace(strInfo, '\n', '<br>')
    if len(listText) == 2:
      # Ein Link
      return '<a href="%s">%s</a>' % (listText[1], strInfo)
    # ein simple Text

    return '%s' % strInfo

  def exception(self, e):
    self.log(e.strClass, e.strInfo)

  def print_exception(self, objFile, type=None, value=None, tb=None, limit=None):
    if type is None:
      type, value, tb = sys.exc_info()
    import traceback
    list = traceback.format_tb(tb, limit) + \
        traceback.format_exception_only(type, value)
    strMsg = "<PRE>Traceback (most recent call last):\n%s<B>%s</B></PRE>" % (
      html.escape("".join(list[:-1])),
      html.escape(list[-1]),
      )
    objFile.write(strMsg)
    del tb
    objFile.flush()

  def get_now(self):
    return strftime("%Y-%m-%d_%H:%M:%S", localtime())

  def relativepath(self, strLink):
    """
      Returns the relative path from the current Logfile (self.strLogFile)
      to the file to be linked.
      This Method was taken from 'pathlib.py' of the
      projekt 'griesser'.
    """
    strAbsFrom = os.path.abspath(self.strLogFile)
    strAbsTo = os.path.abspath(strLink)
    # Find common path
    listAbsFrom = strAbsFrom.split(os.sep)
    listAbsTo = strAbsTo.split(os.sep)
    bSameRoot = False
    for f, t in zip(listAbsFrom, listAbsTo):
      if f == t:
        bSameRoot = True
        listAbsFrom.pop(0)
        listAbsTo.pop(0)
        continue
      break
    if bSameRoot:
      return '..\\'*(len(listAbsFrom)-1) + os.sep.join(listAbsTo)
    # This case happens on window if strAbsFrom='x:/rs' and strAbsTo='y:/rc'.
    # On unix, this will never happen because all filesystems share the same root
    return "file://" + strAbsTo

  def close(self):
    self.logFile.write("""</body>
              </html>""")
    self.logFile.close();

class LogException(Exception):
  def __init__(self, strClass, strInfo):
      Exception.__init__(self, '%s: %s' % (strClass, strInfo))
      self.strClass = strClass
      self.strInfo = strInfo

def test():
  objLogger = Logger('logger_test', {'title': 'Logger - Test', 'html': '<h1>Logger Test</h1><p>K. O. R. was here</p><hr>'})
  objLogger.title(INFO, 'Output der Testmethode')

  listKlassifizierung = []
  for iClass in Logger.listClasses:
    (strClass, strBetrifft, strComment) = Logger.dictClasses[iClass]
    listKlassifizierung.append(((iClass, strClass), (INFO, strBetrifft), (INFO, strComment)))
  objLogger.table(OK, 'Klassifizierung der Meldungen', ('Klasse', 'Die Meldung betrifft', 'Bemerkungen'), listKlassifizierung)

  objLogger.table(OK, 'Tabelle mit Links', ('Sensorname', 'Kalibration', 'Kommentar'), (
    ((INFO, '33a', 'http://www.python.org'), (FAILED, 'Fehler', 'http://www.python.org'), (FAILED, 'Ausserhalb Toleranz')),
  ))

  objLogger.log('INFO', 'Eine Meldung mit Umlauten: äöüÄÖÜ.')
  objLogger.log('INFO', 'Eine Meldung mit Umlauten: M\xe4rki.')
  objLogger.log('INFO', 'Ein Image.')
  objLogger.log_image('INFO', "logger_test.gif")
  objLogger.log('INFO', 'Ein Image mit hinterlegtem Link und Alt-Text.')
  objLogger.log_image('INFO', "logger_test.gif", "http://www.python.org", "Dies ist der Alt-Text")
  objLogger.log_object('INFO', objLogger, 'Das objLogger-Objekt')

  objLogger.log(TRACE, 'Spezialzeichen <->')

  for iClass in Logger.listClasses:
    (strClass, strBetrifft, strComment) = Logger.dictClasses[iClass]
    objLogger.log(strClass, 'Logeintrag ohne Link (%s)' % strClass)

  for iClass in Logger.listClasses:
    (strClass, strBetrifft, strComment) = Logger.dictClasses[iClass]
    objLogger.log(strClass, 'Logeintrag mit Link (%s)' % strClass, 'http://www.python.org')

  try:
    # Error
    (1,2)[5]
  except:
    objLogger.log(FATAL, "Es wurde absichtlich auf ein nicht existierendes Element zugegriffen")
  try:
    raise LogException(OK, "Testaufruf von LogException")
  except LogException as e:
    objLogger.exception(e)

  import iteration
  iteration.test(objLogger)

# if __name__ == "__main__":
#  test()
##########################################################################################
####################################### logger.py END
##########################################################################################

#
# PyCkup implementation starts here!
#
import os, string, filecmp, shutil, time, re
timeNow = time.localtime()

config = {
  # A Zip-File will never be bigger than:
  'max_size': 650000000,  # Bytes
  # A Zip-File will never contain more files than:
  'max_files': 32000,
  # Define all files to include
  'regexp_include': [],
  # Define the file to be excluded
  'regexp_exclude': [],
  # Define the file not be be compressed
  'regexp_nocompress': [
    '\.png$',    # '.png' will not be compressed
    '\.gif$',    # '.gif' will not be compressed
    '\.jpg$',    # '.jpg' will not be compressed
    '\.zip$',    # '.zip' will not be compressed
  ],
}

dictCounterDefaults = {
  'count': 0,
  'compressed': 0,
  'strCompressed': '0',
  'uncompressed': 0,
  'strUncompressed': '0',
}

def add_mille_sep(strVal):
    """
        >> add_mille_sep(str(0))
        "0"
        >> add_mille_sep(str(9))
        "9"
        >> add_mille_sep(str(11))
        "11"
        >> add_mille_sep(str(123))
        "123"
        >> add_mille_sep(str(1234))
        "1'234"
        >> add_mille_sep(str(123456789))
        "123'456'789"
        >> print(add_mille_sep(str(1234567890))
        "1'234'567'890"
        >> print(add_mille_sep(str(12345678901))
        "12'345'678'901"
    """
    strVal = str(strVal)
    for iSep in range(3, 99, 4):
        if iSep >= len(strVal):
            return strVal
        strVal = "%s'%s" % (strVal[:-iSep], strVal[-iSep:])


class ZipFile:
  def __init__(self, strZipFilenameBase, objBackup):
    self.strZipFilenameBase = strZipFilenameBase
    self.objBackup = objBackup
    self.iBackupSet = 1

  def open(self):
    # Create Zipfile
    self.strZipFilename = "%s_%d.zip"% (self.strZipFilenameBase, self.iBackupSet)
    self.objZip = zipfile.ZipFile(self.strZipFilename, "w", compression=zipfile.ZIP_DEFLATED, allowZip64=True)
    self.objBackup.objLogger.log(TRACE, os.path.basename(self.strZipFilename), self.strZipFilename)
    self.iFiles = 0
    self.iBytes = 0

  def close(self):
    self.objZip.close()

  def reopen_(self, strFilename):
    iBytesFile = os.path.getsize(strFilename)
    iBytesArchive = os.path.getsize(self.strZipFilename)

    # Begin a new ZipFile if needed
    if (self.iFiles < self.objBackup.dictBackup['max_files']):
      if iBytesArchive+iBytesFile < self.objBackup.dictBackup['max_size']:
        return

  def reopen(self, strFilename):
    # try:
    #   objZipInfo = self.objZip.infolist()[-1]
    # except IndexError:
    #   return
    iBytesFile = os.path.getsize(strFilename)
    iBytesArchive = os.path.getsize(self.strZipFilename)
    # In Python 2.5 nicht mehr vorhanden: objZipInfo.file_offset
    # iBytesArchive = objZipInfo.file_offset + objZipInfo.compress_size

    # Begin a new ZipFile if needed
    if (self.iFiles < self.objBackup.dictBackup['max_files']):
      if iBytesArchive+iBytesFile < self.objBackup.dictBackup['max_size']:
        return
    # Open a new file
    self.close()
    self.iBackupSet = self.iBackupSet + 1
    self.open()

  def write(self, strFilename, strAchiveFilename):
    self.reopen(strFilename)

    if self.objBackup.match(strAchiveFilename, self.objBackup.listRegexpNocompress):
      iCompression = zipfile.ZIP_STORED # not compressed
    else:
      iCompression = zipfile.ZIP_DEFLATED # compressed

    try:
      r'''
      Bei File ab 2 Gigabyte Grösse:
      File "N:\Projekte\Project Märki Informatik\Diverse kleine Projekte\Automated Backup\20071130\centrinox\pyckup.py", line 504, in write
        self.objZip.write(strFilename, strAchiveFilename, iCompression)
      File "C:\programme\Python25\lib\zipfile.py", line 561, in write
        self._writecheck(zinfo)
      File "C:\programme\Python25\lib\zipfile.py", line 536, in _writecheck
        raise LargeZipFile("Zipfile size would require ZIP64 extensions")
      '''
      self.objZip.write(strFilename, strAchiveFilename, iCompression)
    except ValueError as e:
      # self.objBackup.objSummaryLogger.log(ERROR, '%s. Error: %s' % (strFilename, str(e)))
      # self.objBackup.objSummaryLogger.log(INFO, 'st: %s' % str(st))
      print('%s: %s' % (strAchiveFilename, e))
      self.objBackup.objSummaryLogger.exception(LogException(ERROR, '%s: Nicht archiviert! (%s)' % (strAchiveFilename, e)))
      return None

    except Exception as e:
      print('%s: %s' % (strAchiveFilename, e))
      self.objBackup.objSummaryLogger.exception(LogException(FATAL, '%s: Nicht archiviert! (%s)' % (strAchiveFilename, e)))
      return None
    objZipInfo = self.objZip.infolist()[-1]

    # Increment the counters
    self.iFiles = self.iFiles + 1
    self.iBytes = self.iBytes + objZipInfo.compress_size
    # Return the information about this file
    return objZipInfo

class backup:
  def __init__(self, objSummaryLogger, dictBackup):
    self.objSummaryLogger = objSummaryLogger

    # Update 'dictBackup' with the default parameters
    self.dictBackup = dictBackup
    for strKey, objDefaultValue in config['default_backup'].items():
      self.dictBackup[strKey] = dictBackup.get(strKey, objDefaultValue)

    # Expand time in 'dictBackup'
    self.dictBackup['backup_filename'] = time.strftime(self.dictBackup['backup_filename'], timeNow)
    self.dictBackup['backup_directory'] = time.strftime(self.dictBackup['backup_directory'], timeNow)

    # Build Filenames
    strZipFilenameBase = os.path.abspath('%(backup_directory)s/%(backup_filename)s' % self.dictBackup)
    strFilenameLog = strZipFilenameBase + '.html'

    # Create Sublogfile
    self.objLogger = Logger(strFilenameLog, {'title': '%(backup_filename)s' % dictBackup, 'html': '<h1>%(backup_filename)s</h1>' % dictBackup}, 5)
    self.objLogger.log(INFO, 'Summary', objSummaryLogger.strLogFile)
    self.objLogger.log(INFO, 'PYCKUP_VERSION=' + PYCKUP_VERSION);

    # Create Zip-Object
    self.objZip = ZipFile(strZipFilenameBase, self)
    self.objZip.open()

    # Compile the regular expressions
    self.listRegexpInclude    = list(map(lambda strRegexp: re.compile(strRegexp, re.IGNORECASE), self.dictBackup['regexp_include']))
    self.listRegexpExclude    = list(map(lambda strRegexp: re.compile(strRegexp, re.IGNORECASE), self.dictBackup['regexp_exclude']))
    self.listRegexpNocompress = list(map(lambda strRegexp: re.compile(strRegexp, re.IGNORECASE), self.dictBackup['regexp_nocompress']))

    self.objSummaryLogger.log(INFO, self.dictBackup['backup_filename'], self.objLogger.strLogFile, 'h2')

  def close(self):
    # Write entry in mail-logfile
    if (self.objLogger.dictCounters[FATAL] > 0):
      strStatus = FATAL
    else:
      if (self.objLogger.dictCounters[ERROR] > 0):
        strStatus = ERROR
      else:
        strStatus = OK

    strCounters = '%(count)d files, %(strUncompressed)s -> %(strCompressed)s bytes' % self.dictTotalCounters
    self.objLogger.log(strStatus, strCounters)
    self.objSummaryLogger.log(strStatus, '%s: %s' % (self.dictBackup['backup_filename'], strCounters))

    # Close Zipfile
    self.objZip.close()

    # Close Sublogfile
    self.objLogger.close()

  def match(self, strRelativePath, listRegexp):
    for reExp in listRegexp:
      if reExp.search(strRelativePath):
        return True
    return False

  def funcVisit(self, strSourceBaseDirectory, strDirectory, listNames):
    strSkipFilename = 'pyckup_skip.txt'
    strSkipFilenameFull = os.path.abspath(os.path.join(strDirectory, strSkipFilename))
    if os.path.exists(strSkipFilenameFull):
      self.objLogger.log(INFO, '%s: "%s" found: SKIPPED' % (strDirectory, strSkipFilename))
      return

    for strFilename in listNames:
      strFilenameFull = os.path.abspath(os.path.join(strDirectory, strFilename))
      if os.path.isfile(strFilenameFull):
        if not strFilenameFull.startswith(strSourceBaseDirectory):
          self.objLogger.log(FATAL, 'internal programming error (if not strFilenameFull.startswith(strSourceBaseDirectory):)')
        strRelativePath = strFilenameFull[len(strSourceBaseDirectory)+1:]
        if len(self.listRegexpInclude) != 0:
          if not self.match(strRelativePath, self.listRegexpInclude):
            # No include-pattern matched
            continue
        if len(self.listRegexpExclude) != 0:
          if self.match(strRelativePath, self.listRegexpExclude):
            # A exclude-pattern matched
            continue
        if os.path.getsize(strFilenameFull) > self.dictBackup['max_size']:
          self.objLogger.log(ERROR, '%s: File is bigger then "max_size". Skipped!' % strFilenameFull)
          continue

        # Do the job: Write the file to the zip-archive
        objZipInfo = self.objZip.write(strFilenameFull, strRelativePath)
        if objZipInfo == None:
          self.objLogger.log(INFO, '%s: Nicht archiviert!' % strFilename)
          continue
        # Increment the counters
        for strKey, iValue in (('count', 1), ('compressed', objZipInfo.compress_size), ('uncompressed', objZipInfo.file_size)):
          self.dictCounters[strKey] = self.dictCounters[strKey] + iValue
        self.dictCounters['strCompressed'] = add_mille_sep(self.dictCounters['compressed'])
        self.dictCounters['strUncompressed'] = add_mille_sep(self.dictCounters['uncompressed'])
        # print("adding '%s' -> '%s'" % (strFilenameFull, strRelativePath))
    print("adding '%s'" % strDirectory)

  def go(self):
    strSourceBaseDirectory = os.path.abspath(self.dictBackup['src_basedirectory'])
    self.dictTotalCounters = dict(dictCounterDefaults)
    for strSourceDirectoryRelative in self.dictBackup['src_directories']:
      self.dictCounters = dict(dictCounterDefaults)
      strSourceDirectory = os.path.abspath(os.path.join(strSourceBaseDirectory, strSourceDirectoryRelative))
      self.objLogger.log(INFO, 'backing up directory: %s' % strSourceDirectoryRelative, strSourceDirectory, 'h3')
      # os.walk(strSourceDirectory, self.funcVisit, strSourceBaseDirectory)
      for strRootDirectory, listDirectories, listFiles in os.walk(strSourceDirectory):
        self.funcVisit(strSourceDirectory, strRootDirectory, listFiles)
      self.objLogger.log(INFO, '%(count)d files, %(strUncompressed)s -> %(strCompressed)s bytes' % self.dictCounters)
      if self.dictCounters['count'] == 0:
        self.objLogger.log(ERROR, 'Directory is empty! Is the directory name misspelled?')
      # Increment the counters
      for strKey, iValue in self.dictCounters.items():
        self.dictTotalCounters[strKey] = self.dictTotalCounters[strKey] + iValue
      self.dictTotalCounters['strCompressed'] = add_mille_sep(self.dictTotalCounters['compressed'])
      self.dictTotalCounters['strUncompressed'] = add_mille_sep(self.dictTotalCounters['uncompressed'])
 
def go():
  """Python Backup"""

  strPyckupConfigFilename = 'pyckup_config.txt'
  with open(strPyckupConfigFilename) as f:
    strPyckupConfig = f.read()

  code = compile(strPyckupConfig, strPyckupConfigFilename, 'exec')
  global_vars = {}
  exec(code, global_vars, config)
  if config.get('pyckup_config_version', None) != '1.0.0':
    raise Exception("This PyCkup-Version is too old for this 'pyckup_config.txt'")

  # Create Logfile
  strFilenameSummary = os.path.abspath('%(backup_directory)s/%(summary_filename)s.html' % config['default_backup'])
  strFilenameSummary = time.strftime(strFilenameSummary, timeNow)
  try:
    os.makedirs(os.path.dirname(strFilenameSummary))
  except OSError as e:
    pass # Directory already exists
  objSummaryLogger = Logger(strFilenameSummary, {'title': os.path.basename(strFilenameSummary), 'html': '<h1>Summary</h1>'}, 5)
  objSummaryLogger.log(TRACE, 'The Configuration File:')
  objSummaryLogger.log(INFO, 'PYCKUP_VERSION=' + PYCKUP_VERSION);
  objSummaryLogger.pre(TRACE, strPyckupConfig)

  # import webbrowser
  # webbrowser.open(strLogFilename)
  os.startfile(objSummaryLogger.strLogFile)

  try:
    # Loop for all archives
    for dictBackup in config['backups']:
      objBackup = backup(objSummaryLogger, dictBackup)
      objBackup.go()
      objBackup.close()
  except:
    import io, traceback
    out = io.StringIO()
    traceback.print_exc(file=out)
    objSummaryLogger.pre(FATAL, out.getvalue())
    objSummaryLogger.log(FATAL, 'Fehler')

  # Close Logfile
  if (objSummaryLogger.dictCounters[FATAL] > 0):
    objSummaryLogger.log(FATAL, 'FAILED')
  else:
    if (objSummaryLogger.dictCounters[ERROR] > 0):
      objSummaryLogger.log(ERROR, 'FAILED')
    else:
      objSummaryLogger.log(OK, 'SUCCESS')
  objSummaryLogger.close()

if __name__=="__main__":
  go()
