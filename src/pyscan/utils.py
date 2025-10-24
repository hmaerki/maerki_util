import os
import socket
import time

# import engine_scan

WIA_INTENT_IMAGE_TYPE_COLOR = 1
WIA_INTENT_IMAGE_TYPE_GRAYSCALE = 2
WIA_INTENT_IMAGE_TYPE_TEXT = 4


directory = os.path.dirname(os.path.abspath(__file__))

strConfigFile = os.path.join(directory, "config_%s.py" % socket.gethostname())
dictConfigConfig = {}
_dictGlobal = {}
try:
    with open(strConfigFile) as f:
        code = compile(f.read(), strConfigFile, "exec")
        exec(code, _dictGlobal, dictConfigConfig)
except IOError as e:
    raise Exception(r"Konfigurationsdatei nicht gefunden: %s" % strConfigFile)
    # return False

"""
  This module contains handy helper-functions.
"""
if False:
    iTime = time.localtime()
    strDay = time.strftime("%Y-%m-%d", iTime)
    strTime = time.strftime("%H-%M-%S", iTime)
    strFolder = "../scans/%s/%s" % (socket.gethostname(), strDay)
    if not os.path.exists(strFolder):
        os.makedirs(strFolder)

# scan = engine_scan.scan
# wxScan = engine_scan.wxScan


def createFilename(strPrefix):
    """
    Example: strPrefix = 'a4_bw'
    Return:  ../hostname/2006-06-04/2006-06-04_10-59-07_a4_bw.png
    """
    strFilename = "%s_%s_%s" % (strDay, strTime, strPrefix)

    return os.path.join(strFolder, strFilename)


def openFolder():
    """
    Opens the Windows-Explorer showing the actual Scans.
    """
    # os.startfile(strFolder)
    os.execl(
        r"%s\explorer.exe" % os.environ["windir"],
        "explorer",
        '"%s"' % os.path.abspath(strFolder),
    )
    # os.system(r'explorer.exe "%s"' % os.path.abspath(strFolder))
