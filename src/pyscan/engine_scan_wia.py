# -*- coding: utf-8 -*-
import os
import sys
import win32com
import win32com.client
import pyscan.utils as utils

#
#  WIA Globals
#
WIA_COM = "WIA.CommonDialog"
WIA_DEVICE = "WIA.DeviceManager"
WIA_DEVICE_UNSPECIFIED = 0
WIA_INTENT_UNSPECIFIED = 0
WIA_BIAS_MIN_SIZE = 65536
WIA_IMG_FORMAT_PNG       = '{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}'
WIA_IMG_FORMAT_BMP       = '{B96B3CAB-0728-11D3-9D7B-0000F81EF32E}'

COMMAND_DELETE_ALL_ITEMS   = '{E208C170-ACAD-11D2-A093-00C04F72DC3C}'

WIA_INTENT_BIAS_MAXIMIZE_QUALITY = 0x20000
WIA_INTENT_BIAS_MINIMIZE_SIZE = 0x10000

if False:
  class WiaDeviceManagerSingleton:
    __wiaDeviceManager = None
    def __init__(self):
      WiaDeviceManagerSingleton.__wiaDeviceManager = win32com.client.Dispatch(WIA_DEVICE)
    def get(self):
      return WiaDeviceManagerSingleton.__wiaDeviceManager


def getPropertyByName(listProperties, strName):
  for wiaProperty in listProperties:
    if wiaProperty.Name == strName:
      return wiaProperty
  listNames = map(lambda p: p.Name, listProperties)
  raise Exception('Property "%s" nicht gefunden (%s).' % (strName, listNames))

def getPropertyValueByName(listProperties, strName):
  return getPropertyByName(listProperties, strName).Value

def setPropertyById(listProperties, iPropertyId, iValue):
  for wiaProperty in listProperties:
    if wiaProperty.PropertyID == iPropertyId:
      wiaProperty.Value = iValue
      return
  listNames = map(lambda p: p.Name, listProperties)
  raise Exception('Property "%d" nicht gefunden %s.' % (iPropertyId, str(listProperties)))

def getDeviceList():
  wiaDeviceManager = win32com.client.Dispatch(WIA_DEVICE)
  listNames = []
  print('Scanners:')
  for wiaDeviceInfo in wiaDeviceManager.DeviceInfos:
    # print(wiaDeviceInfo.Properties("Name") + " / " + wiaDeviceInfo.Properties("Description")
    strDescription = getPropertyValueByName(wiaDeviceInfo.Properties, 'Description')
    strDescription = strDescription.encode('ascii', 'ignore').decode('ascii')
    strName = getPropertyByName(wiaDeviceInfo.Properties, 'Name').Value
    strName = strName.encode('ascii', 'ignore').decode('ascii')
    print('  Scanner "%s" "%s"' % (strName, strDescription))
    listNames.append(strDescription)
  return listNames


def getDevice(strScannerDescription):
  wiaDeviceManager = win32com.client.Dispatch(WIA_DEVICE)
  for wiaDeviceInfo in wiaDeviceManager.DeviceInfos:
    strDescription = getPropertyValueByName(wiaDeviceInfo.Properties, 'Description')
    strDescription = strDescription.encode('ascii', 'ignore').decode('ascii')
    if strDescription == strScannerDescription:
      return wiaDeviceInfo.Connect()
  raise Exception('Scanner "%s" nicht gefunden (%s).' % (strScannerDescription, listNames))

def setProperties(listProperties, dictValues):
  listKeys = list(dictValues.keys())
  listNames = []
  for wiaProperty in listProperties:
    strName = wiaProperty.Name
    iValue = dictValues.get(strName, None)
    if iValue != None:
      wiaProperty.Value = iValue
      listKeys.remove(strName)
    else:
      listNames.append(strName)
  if len(listKeys) > 0:
    raise Exception('Properties %s nicht gefunden. Verfuebar sind %s' % (listKeys, listNames))

def printEvents(listEvents):
  for wiaEvent in listEvents:
    print('%s: %s' % (wiaEvent.Name, wiaEvent.EventID))

def printProperties(listProperties):
  for wiaProperty in listProperties:
    print('%s: %s (%s)' % (wiaProperty.Name, wiaProperty.Value, wiaProperty.IsReadOnly))

class scanner:
  def __init__(self, fCancelHandler=None):
    self.fCancelHandler = fCancelHandler

  def connect(self, strScanner):
    self.wiaDevice = getDevice(strScanner)
    self.wiaDeviceItem = self.wiaDevice.Items[0]
    dictDeviceItemValues = {
      'Bits Per Pixel': 24,
    }
    setProperties(self.wiaDeviceItem.Properties, dictDeviceItemValues)

  def close(self):
    pass
  
  def acquire(self, objVorlage, strPaperSize):
    iDPI, iIntentImageType = objVorlage.getDpi()

    dictDeviceItemValues = {
      'Current Intent': iIntentImageType + WIA_INTENT_BIAS_MAXIMIZE_QUALITY, # 4 is Black-white, gray is 2, color 1
    }
    setProperties(self.wiaDeviceItem.Properties, dictDeviceItemValues)
  
    # printEvents(wiaDevice.Events)
    # printProperties(self.wiaDeviceItem.Properties)

    """
    dictExtentZuBreit = {
      600: (5100, 7002),
      300: (2550, 3501),
      150: (1275, 1750),
      75: (637, 875),
      72: (612, 840),
    }
    dictExtent = {
      'A4': {
        600: (4920, 7002),
        300: (2460, 3501),
        200: (1640, 2334),
        150: (1230, 1750),
        75: (615, 875),
        72: (592, 840),
      },
      'Letter': {
        600: (5100, 7002),
        300: (2550, 3501),
        200: (1700, 2334),
        150: (1275, 1750),
        75: (637, 875),
        72: (612, 840),
      },
    }
    iHorizontalExtent, iVerticalExtent = dictExtent[strPaperSize][iDPI]
    """
    sizeInPixelsAt1200dpi = { # See http://www.a4papersize.org/a4-paper-size-in-pixels.php
      'A4':     (  9921, 14006 ), # 210mm x 297mm
      'Letter': ( 10200, 13200 ), # 216mm x 280mm
      'Max':    ( 10200, 14006 ), # 216mm x 297mm
    }
    iHorizontalExtent, iVerticalExtent = sizeInPixelsAt1200dpi[strPaperSize]
    iHorizontalExtent = iHorizontalExtent*iDPI/1200
    iVerticalExtent = iVerticalExtent*iDPI/1200
    dictDeviceItemValues = {
      'Horizontal Resolution': iDPI,
      'Vertical Resolution': iDPI,
      'Horizontal Extent': iHorizontalExtent, # (Scanning Area)
      # 'Vertical Extent': iVerticalExtent, # (Scanning Area)
      'Horizontal Start Position': 0, # (Scanning Area)
      'Vertical Start Position': 0, # (Scanning Area)
    }
    setProperties(self.wiaDeviceItem.Properties, dictDeviceItemValues)

    wiaImage = self.wiaDeviceItem.Transfer(WIA_IMG_FORMAT_BMP)
    import tempfile
    strFilename = tempfile.gettempdir() + r'\scanner_wia_tmp.bmp'
    if os.path.exists(strFilename):
      os.remove(strFilename)
    wiaImage.SaveFile(strFilename)


    # self.wiaDeviceItem.ExecuteCommand(COMMAND_DELETE_ALL_ITEMS)
    return strFilename
