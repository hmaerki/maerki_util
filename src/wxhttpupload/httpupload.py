#! python3.7
#!/usr/bin/env python

import os
import re
import ssl
import sys
import http
import http.client
import html
import base64
import socket
from urllib import parse as urlparse
from time import localtime, strftime, daylight

# The WebDAV-Protocol is specified here:
# http://www.webdav.org/specs/rfc2518.html

# HISTORY

# 1.1.7
# Upload will be done in four rounds
# 0: First all .html and .css
# 1: Then all files smaller than 100k
# 2: Then all files smaller than 5M
# 3: Rest

#----------------------------------------------------------------------------

sCopyright = "Copyright Hans Maerki. LGPL."
sVersion = "v1.1.6"
sProduct = "HTTP Upload"

#----------------------------------------------------------------------------

#
# The command-line-interface and the user-interface each use
# a Mediator-Class as an interface to HttpUpload.
#

class Mediator:
  """The commandline-interface for httpupload"""

  def __init__(self):
    strConfigFilename = 'http_upload_config.txt'
    self.dictConfig = {}
    try:
      execfile(strConfigFilename, self.dictConfig)
      with open(strConfigFilename) as f:
        code = compile(f.read(), strConfigFilename, 'exec')
        global_vars = {}
        exec(code, global_vars, self.dictConfig)
    except IOError as e:
      self.writeLine("Configuration File '%s not found in Folder '%s'." % (strConfigFilename, os.getcwd()))
    if self.dictConfig.get('httpupload_config_version', None) != '1.0.0':
      self.writeLine("This Configuration-Version is too old for this '%s'" % strConfigFilename)
    self.dictArguments = self.dictConfig.get('httpupload_configuration', {})
    self.dictArguments['FilenameHtmlLog'] = os.path.normpath("%s/tmp_httpupload_log.html" % self.dictArguments['local'])
    self.dictArguments['ForceUpload'] = False
    try:
      import getopt
      opts, args = getopt.getopt(sys.argv[1:], "hflr:", ["help", "structure="])
    except getopt.GetoptError:
      # print help information and exit:
      self.usage()
      raise
    for o, a in opts:
      if o in ("-h", "--help"):
        self.usage()
        raise Exception
      if o in ("-f", "--force"):
        self.dictArguments['ForceUpload'] = True

  def usage(self):
    print("Usage: %s --force" % sys.argv[0])
    sys.exit()

  def writeLine(self, strLine):
    print(strLine)

  def setStatus(self, strLine):
    print("   %s" % strLine)

  def keepRunning(self):
    return True

  def getArgument(self, strName, objDefault=None):
    return self.dictArguments.get(strName, objDefault)

  def end(self, iErrors):
    print
    if iErrors == 0:
      print("Success!")
    else:
      print("Failed (iErrors==%d)." % iErrors)
    print("Hit return to close...")
    raw_input()

#----------------------------------------------------------------------------

def HttpUpload(objMediator_):
  global objMediator
  objMediator = objMediator_
  objCore = http_upload_core()
  iErrors = objCore.upload()
  objMediator.end(iErrors)
  return iErrors

#----------------------------------------------------------------------------

UPLOAD_ROUNDS = 4

class http_upload_core:
  def __init__(self):
    self.dictFileSizeCache = {}
    self.dictFileTimeCache = {}
    self.objConnection = None
    self.archive_bit = 0x00000020
    self.strRemoteProtocol, self.strRemoteHost, self.strRemotePath, dummy, dummy, dummy = urlparse.urlparse(objMediator.getArgument('remote'))
    self.strLocal = os.path.normpath(objMediator.getArgument('local'))

    strUserPassword = '%s:%s' % (objMediator.getArgument('user'), objMediator.getArgument('password'))
    strUserPassword = base64.encodebytes(bytes(strUserPassword, 'utf-8'))
    strUserPassword = strUserPassword.decode('utf-8').replace('\n', '')
    self.strAuthorization = "Basic %s" % strUserPassword

    self.strFilenameTimestamps = os.path.normpath("%s/tmp_httpupload_timestamps_cache.txt" % objMediator.getArgument('local'))
    self.iFilesUploaded = 0
    self.objLogger = Logger(objMediator.getArgument('FilenameHtmlLog'), objMediator.getArgument('local'))

    # Compile the regular expressions
    self.listRegexpExclude = list(map(lambda strRegexp: re.compile(strRegexp, re.IGNORECASE), objMediator.getArgument('exclude', [])))

    self.listRegexpExclude.append(re.compile('\\.pyc$', re.IGNORECASE))
    self.listRegexpExclude.append(re.compile('/__pycache__/', re.IGNORECASE))

  def mediator_write_info(self, strLine):
    objMediator.writeLine(strLine)
    self.objLogger.info(strLine)

  def mediator_write_warning(self, strLine):
    objMediator.writeLine(strLine)
    self.objLogger.warning(strLine)

  def mediator_write_error(self, strLine):
    objMediator.writeLine(strLine)
    self.objLogger.error(strLine)

  def http(self, strVerb, strRelativePath, strPage=""):
    if self.objConnection == None:
      if self.strRemoteProtocol == 'https':
        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.objConnection = http.client.HTTPSConnection(self.strRemoteHost, context=sslContext, timeout=30)
      else:
        self.objConnection = http.client.HTTPConnection(self.strRemoteHost, timeout=30)
      # Need to comment, to allow access to the socket below
#      self.objConnection.connect()
      # Set the socket timeout
      # self.objConnection._conn.sock.set_timeout(300)
#      socket.setdefaulttimeout(300.0)

    headers = {
      'Accept': 'text/html',
      'User-Agent': 'wxhttpupload',
      'Host': self.strRemoteHost,
      # 'Content-Length': str(len(strPage)),
      'Authorization': self.strAuthorization,
    }

    try:
      #
      strRelativePath = strRelativePath.replace(' ', '%20')
      self.objConnection.request(strVerb, strRelativePath, strPage, headers)
      response = self.objConnection.getresponse()
      data = response.read()
      # self.objConnection.close()
    except Exception as e:
      self.objConnection.close()
      self.objConnection = None
      self.objLogger.print_exception()
      raise Exception('"%s", "%s": "%s"' % (strVerb, strRelativePath, str(e)))
    return response.status, response.reason

  def http_create_folder(self, strRelativePath):
    return self.http("MKCOL", strRelativePath)

  def http_create_folder_recursive(self, strRelativePath):
    iPos = strRelativePath.rfind('/')
    if iPos <= 1:
      # There will never be more than 10 nested directories
      return
    strRelativePath = strRelativePath[:iPos]
    errorcode, errormessage = self.http_create_folder(strRelativePath)
    if errorcode != 201:
      self.http_create_folder_recursive(strRelativePath)
      self.http_create_folder(strRelativePath)

  def http_upload_file_put(self, strPath, strRelativePath):
    """return 0 if 0 error. return 1 if 1 error."""
    with open(strPath, "rb") as objFile:
      return self.http("PUT", strRelativePath, objFile)

  def http_upload_file(self, strPath):
    strRelativePath = strPath[len(self.strLocal):]
    strRelativePath = (self.strRemotePath + strRelativePath).replace('\\', '/')
    errorcode, errormessage = self.http_upload_file_put(strPath, strRelativePath)
    if errorcode >= 200 and errorcode < 300:
      # SUCCESS
      # 201 Created.
      # 204 No Content (File ueberschrieben ...)
      return 0
    if errorcode in (
        403,  # Forbidden
        409,  # Conflict. Missing one or more intermediate collections.
              # --> Folder missing
      ):
      self.http_create_folder_recursive(strRelativePath)
      errorcode, errormessage = self.http_upload_file_put(strPath, strRelativePath)
      if errorcode == 201 or errorcode == 204:
        return 0
    strMessage = "%d %s:   %s  ://  %s  %s" % (errorcode, errormessage, self.strRemoteProtocol, self.strRemoteHost, strRelativePath)
    self.objLogger.warning(strMessage)
    raise UserWarning(strMessage)

    # self.objLogger.error(strMessage)
    return 1

  def skip_file(self, strPath):
    """Returns if the filename ends with '.httpupload.skip'
    or there is a file ending with '.httpupload.skip'."""
    if strPath.endswith('.httpupload.skip'):
      return True
    if os.path.exists(strPath + '.httpupload.skip'):
      # os.path.exists() works for folders and for files
      return True
    if self.strFilenameTimestamps == strPath:
      # This is the cache-file. Skip it.
      return True
    if objMediator.getArgument('FilenameHtmlLog') == strPath:
      # This is the log-file. Skip it.
      return True

    strPathSlash = strPath.replace('\\', '/')
    for reExp in self.listRegexpExclude:
      if reExp.search(strPathSlash):
        # objMediator.writeLine(strPath + 'skip!')
        # A exclude-pattern matched
        return True

    return False

  def upload_file(self, strPath):
    """return 0 if 0 error. return 1 if 1 error."""

    if self.skip_file(strPath):
      return 0
    if not objMediator.keepRunning():
      return 0
      raise UserWarning("Stopped by user!")
    strRelativePath = strPath[len(self.strLocal)+1:]
    strUrl = self.strRemoteHost + self.strRemotePath + '/' + strRelativePath.replace('\\', '/')
    # attr = os.stat(strPath)
    timeCached = self.get_cache(strUrl)

    timeFile = self.dictFileTimeCache.get(strPath, None)
    if timeFile is None:
      timeFile = os.path.getmtime(strPath)
      self.dictFileTimeCache[strPath] = timeFile

    # If daylight savings (Sommerzeit), has an influence
    # on the POSIX time. I couldn't figure out, which
    # mechanism is used.
    # We used some fuzzy logic now.
    # if timeCached >= attr.st_mtime:
    # if timeCached >= timeFile:
    timeFile = int(timeFile)
    if timeFile in (timeCached-3600, timeCached, timeCached+3600):
      # File hasn't changed
      return 0

    objMediator.setStatus("%d: File '%s'" % (self.iFilesUploaded+1, strRelativePath))

    iErrors = self.http_upload_file(strPath)
    if iErrors == 0:
      # self.dictLastModifiedTimes[strPath] = attr.st_mtime
      self.add_cache(strUrl, timeFile)

    return iErrors

  def select_file(self, strFilePath, round):
    if round == 0:
      s = strFilePath.lower()
      for extension in ('.html', '.css', '.htaccess'):
        if s.endswith(extension):
          return True
      return False

    # Cache the filesize
    size = self.dictFileSizeCache.get(strFilePath)
    if size == None:
      size = os.path.getsize(strFilePath)
      self.dictFileSizeCache[strFilePath] = size

    if round == 1:
      return size < 100 * 1000
    if round == 2:
      return size < 5 * 1000 * 1000
    assert round < UPLOAD_ROUNDS
    return True

  def recurse_folder(self, strPath, round):
    """returns the error count"""
    iErrors = 0
    for strFile in os.listdir(strPath):
      if not objMediator.keepRunning():
        return iErrors
      strCurrentPath = os.path.normpath(os.path.join(strPath, strFile))
      if not self.skip_file(strCurrentPath):
        if os.path.isdir(strCurrentPath):
          iErrors += self.recurse_folder(strCurrentPath, round=round)
        else:
          if self.select_file(strCurrentPath, round=round):
            iErrors += self.upload_file(strCurrentPath)
    return iErrors

  def upload_2(self, strPath, round):
    iErrors = self.recurse_folder(strPath, round=round)
    for i in range(2):
      if iErrors == 0:
        return 0
      self.mediator_write_info("%d errors occurred during this loop! Trying a %d'd time." % (iErrors, i+2))
      iErrors = self.recurse_folder(strPath, round=round)
    return iErrors

  def upload_1(self):
    self.dictLastModifiedTimes = {}
    if objMediator.getArgument('ForceUpload'):
      self.objFileTimestamps = open(self.strFilenameTimestamps, 'w')
    else:
      if os.path.exists(self.strFilenameTimestamps):
        self.objFileTimestamps = open(self.strFilenameTimestamps, 'r')
        for strLine in self.objFileTimestamps:
          strLine = strLine.strip()
          if len(strLine) == 0:
            # Skip empty lines
            continue
          part = strLine.partition('\t')
          strTime = part[0]
          strPath = part[2]
          # self.objLogger.info("-%d-%s-%s-" % (int(strTime), strPath, strLine))
          self.dictLastModifiedTimes[strPath] = int(strTime)
      self.objFileTimestamps = open(self.strFilenameTimestamps, 'a+')

    # for strPath, iTime in self.dictLastModifiedTimes.items():
    #  self.objLogger.warning("'%s':%i" % (strPath, iTime))

    for round in range(UPLOAD_ROUNDS):
      iErrors = self.upload_2(strPath=objMediator.getArgument('local'), round=round)
      if self.objConnection is not None:
        # After a run, we might run into a timeout.
        # Closing the connection could be a bit more stable
        self.objFileTimestamps.flush()
        self.objConnection.close()
        self.objConnection = None
      if iErrors > 0:
        break

    self.objFileTimestamps.close()
    if self.iFilesUploaded > 0:
      # Purge duplicated entries
      self.objFileTimestamps = open(self.strFilenameTimestamps, 'w')
      for strPath in sorted(self.dictLastModifiedTimes.keys()):
        iTime = self.dictLastModifiedTimes[strPath]
        self.objFileTimestamps.write("%d\t%s\n" % (iTime, strPath))

    self.mediator_write_info("%d Files uploaded." % self.iFilesUploaded)

    if iErrors == 0:
      self.objLogger.info('---- SUCCESS')
    else:
      self.objLogger.error('---- FAILED')

    return iErrors

  def get_cache(self, strPath):
    return self.dictLastModifiedTimes.get(strPath, 0)

  def add_cache(self, strPath, iTime):
    self.iFilesUploaded = self.iFilesUploaded + 1
    self.objFileTimestamps.write("%d\t%s\n" % (iTime, strPath))
    self.dictLastModifiedTimes[strPath] = iTime

  def upload(self):
    try:
      return self.upload_1()
    except UserWarning as e:
      s = '    Error: ' + str(e)
      self.mediator_write_error(s)
      return 1
    except socket.gaierror as e:
      s = '    Error: Host "%s" not found! %s' % (self.strRemoteHost, str(e))
      self.mediator_write_error(s)
      return 1
    except Exception as e:
      self.mediator_write_error('    Unknown Error: ' + str(e))
      self.objLogger.print_exception()
      return 1

  def win32_is_archived_obsolete(self, strPath):
    from win32file import GetFileAttributes
    "see: http://aspn.activestate.com//ASPN/Python/Reference/Products/ActivePython/PythonWin32Extensions/win32file__GetFileAttributes_meth.html"
    attributes = GetFileAttributes(strPath)
    return GetFileAttributes(strPath) & self.archive_bit

  def win32_archived_obsolete(self, strPath):
    from win32file import SetFileAttributes
    attributes = GetFileAttributes(strPath)
    SetFileAttributes(strPath, GetFileAttributes(strPath) & ~self.archive_bit)


#----------------------------------------------------------------------------

class Logger:
  "A HTML Logger"
  def __init__(self, sFilenameLog, sFilenameStructure):
    import codecs
    self.iErrors = 0
    self.iWarnings = 0
    self.iInfos = 0
    self.dictMessages = { }
    self.sFilenameStructure = sFilenameStructure
    self.file = codecs.open(sFilenameLog, 'w', "utf-8")
    self.file.write("""<html>
              <style>
              <!--
                .info { COLOR: green }
                .warning { COLOR: orange }
                .error { COLOR: red }
              -->
              </style>
              <body>
              <h1>%s %s</h1>
              running on %s<br>
              from \"%s\"<br>""" % (sProduct, sVersion, self.get_now(), self.sFilenameStructure))

  def warning(self, sWarning, sFilename = None):
    self.iWarnings = self.iWarnings + 1
    self.generic('warning', sWarning, sFilename)

  def error(self, sError, sFilename = None):
    self.iErrors = self.iErrors + 1
    self.generic('error', sError, sFilename)
    self.print_exception()

  def info(self, sInfo, sFilename = None):
    self.iInfos = self.iInfos + 1
    self.generic('info', sInfo, sFilename)

  def generic(self, sClass, sInfo, sFilename):
    if sFilename is None:
      sFilename = self.sFilenameStructure
    strMessage = '<a href="%s">%s</a>: <code class="%s">%s</code><br>' % (sFilename, sFilename, sClass, html.escape(sInfo))
    strMessage = '<code class="%s">%s</code><br>' % (sClass, html.escape(sInfo))
    if not strMessage in self.dictMessages:
      self.file.write(strMessage)
      self.dictMessages[strMessage] = ""
    self.file.flush()


  def print_exception(self, type=None, value=None, tb=None, limit=None):
    if type is None:
      import sys
      type, value, tb = sys.exc_info()
    import traceback
    self.file.write("<H3>Traceback (most recent call last):</H3>")
    list = traceback.format_tb(tb, limit) + \
        traceback.format_exception_only(type, value)
    self.file.write("<PRE>%s<B>%s</B></PRE>" % (
        html.escape("".join(list[:-1])),
        html.escape(list[-1]),
      ))
    self.file.flush()
    del tb

  def get_now(self):
    return strftime("%Y-%m-%d_%H:%M:%S", localtime())

  def close(self):
    self.file.write("""</body>
              </html>""")
    self.file.close()

#----------------------------------------------------------------------------


if __name__=="__main__":
  HttpUpload(Mediator())
