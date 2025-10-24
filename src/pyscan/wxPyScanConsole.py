import io
import os
import os.path
import queue
import sys
import threading
import time
import traceback

import wx
import wx.xrc

import pyscan.engine_scan_wia
import pyscan.utils as utils

# constants
strVersion = "v1.1.0"
ID_TIMER_STATUS = 200

MULTISCAN = "MULTISCAN"
SCAN = "SCAN"
CLOSE = "CLOSE"

directory = os.path.dirname(os.path.abspath(__file__))
directory_vorlagen = os.path.join(directory, "vorlagen")
sys.path.append(directory_vorlagen)

# ----------------------------------------------------------------------------


class WorkerThread(threading.Thread):
    def __init__(self, ctrlApp):
        threading.Thread.__init__(self)
        self.objQueue = queue.Queue()
        self.ctrlApp = ctrlApp
        self.bWorking = False
        self.bMultiscanStop = False
        self.objScanner = None
        self.start()

    def size(self):
        if self.bWorking:
            return self.objQueue.qsize() + 1
        return 0

    def put(self, strCommand):
        self.objQueue.put(strCommand, block=False)

    def ScannerConnect(self):
        if self.objScanner == None:
            # self.objScanner = pyscan.engine_scan_wia.scanner(self.ctrlFrame, self.ScannerDoneHandler, self.ScannerCancelHandler)
            self.objScanner = pyscan.engine_scan_wia.scanner()
            strScanner = self.ctrlApp.ctrlChoiceScanner.GetStringSelection()
            self.objScanner.connect(strScanner)

    def ScannerAcquire(self):
        self.ctrlApp.SetStatus(True)
        strTemplate = self.ctrlApp.ctrlChoiceTemplate.GetStringSelection()
        strTemplate = strTemplate.replace(".py", "")
        modTemplate = __import__(strTemplate)
        objVorlage = modTemplate.Vorlage()
        strPaperSize = self.ctrlApp.ctrlChoicePaperSize.GetStringSelection()
        strFilename = self.objScanner.acquire(objVorlage, strPaperSize)
        return strFilename, objVorlage

    def ScannerClose(self):
        self.bMultiscanStop = True
        if self.objScanner != None:
            self.objScanner.close()
            self.objScanner = None

    def _scan_page(self):
        strFilename, objVorlage = self.ScannerAcquire()
        strFolder = self.ctrlApp.ctrlTextFolder.GetValue()
        strFilenameFinal = os.path.join(
            strFolder, self.ctrlApp.ctrlStaticFilenameSimpleScan.GetLabel()
        )
        if strFilenameFinal.find("<<NEXT>>"):
            # Find next empty slot
            strFilenameTemplate = strFilenameFinal
            for i in range(1, 1000):
                strFilenameFinal = strFilenameTemplate.replace("<<NEXT>>", "%03d" % i)
                if not os.path.exists(strFilenameFinal):
                    break
        self.ScannerPostprocessImage(objVorlage, strFilename, strFilenameFinal)

    def OnButtonScan(self):
        try:
            self.ScannerConnect()
            self._scan_page()
            self.ctrlApp.SetStatus(False)
        except Exception as e:
            self.ctrlApp.handleException(e)

    def OnButtonMultiScan(self):
        try:
            self.bMultiscanStop = False
            self.ScannerConnect()
            while not self.bMultiscanStop:
                self._scan_page()
            self.ctrlApp.SetStatus(False)
        except Exception as e:
            self.ctrlApp.handleException(e)

    def ScannerPostprocessImage(self, objVorlage, strFilename, strFilenameFinal):
        objVorlage.postProcess(strFilename, strFilenameFinal)
        os.remove(strFilename)

        if False:
            strFilenameBmp = strFilenameFinal.replace(".png", ".bmp")
            # Das Image in den entsprechenden Ordner verschieben und umbenennen
            if os.path.exists(strFilenameBmp):
                os.remove(strFilenameBmp)
            os.rename(strFilename, strFilenameBmp)

            objVorlage.postProcess(strFilenameBmp, strFilenameFinal)

    def run(self):
        while True:
            import pythoncom

            pythoncom.CoInitialize()

            try:
                self.bWorking = False
                print("Thread: Queue waiting")
                strCommand = self.objQueue.get()
                print("Thread: Queue returned")
                self.bWorking = True
                if strCommand == SCAN:
                    self.OnButtonScan()

                if strCommand == MULTISCAN:
                    self.OnButtonMultiScan()

                if strCommand == CLOSE:
                    self.ScannerClose()
                    return

            except Exception as e:
                self.ctrlApp.handleException(e, "Exception in Postprocessing-Thread")


# ----------------------------------------------------------------------------


class wxPyScanApp(wx.App):
    def OnInit(self):
        try:
            self.dictConfig = pyscan.utils.dictConfigConfig

            self.ctrlErrorMessageDialog = None
            self.res = wx.xrc.XmlResource(os.path.join(directory, "wxPyScan.xrc"))
            try:
                self.InitFrame()
            except Exception as e:
                self.handleException(e, "Interner Fehler")
            if not self.InitApplication():
                return False
            self.objThread = WorkerThread(self)
            self.ctrlFrame.SetTitle("wxPyScan %s" % strVersion)
            # self.ctrlFrame.Layout()
            # self.ctrlFrame.SetSize((600, 850))
            self.OnUpdateFilename()
            self.OnInitTemplates()
            self.SetStatus(False)

            return True
        except Exception as e:
            self.handleException(e, "Interner Fehler")
            return False

    def InitApplication(self):
        try:
            strPatternFilebase = self.dictConfig["strPatternFilebase"]
            self.ctrlTextFilebase.SetValue(self.ReplaceFields(strPatternFilebase))

            self.ctrlStatusBar.SetStatusText("...", 0)
            self.objTimerStatus.Start(2000)
            return True
        except Exception as e:
            self.handleException(e, "Interner Fehler")
            return False

    def InitFrame(self):
        self.ctrlFrame = self.res.LoadFrame(None, "ID_WXFRAME")

        # Status Bar
        self.ctrlStatusBar = wx.xrc.XRCCTRL(self.ctrlFrame, "ID_STATUSBAR")
        # This status bar has three fields
        self.ctrlStatusBar.SetFieldsCount(2)
        # Sets the three fields to be relative widths to each other.
        self.ctrlStatusBar.SetStatusWidths([150, -1])

        self.ctrlChoiceScanner = wx.xrc.XRCCTRL(self.ctrlFrame, "ID_CHOICE_SCANNER")
        self.ctrlChoicePaperSize = wx.xrc.XRCCTRL(
            self.ctrlFrame, "ID_CHOICE_PAPER_SIZE"
        )
        self.ctrlChoiceTemplate = wx.xrc.XRCCTRL(self.ctrlFrame, "ID_CHOICE_TEMPLATE")

        self.ctrlTextFolder = wx.xrc.XRCCTRL(self.ctrlFrame, "ID_TEXTCTRL_FOLDER")
        ReloadDropTarget(self, self.ctrlTextFolder)

        strFolder = os.path.abspath(os.path.curdir)
        self.ctrlTextFolder.SetValue(strFolder)

        self.ctrlTextFilebase = wx.xrc.XRCCTRL(self.ctrlFrame, "ID_TEXTCTRL_FILEBASE")
        self.ctrlFrame.Bind(wx.EVT_TEXT, self.OnUpdateFilename, self.ctrlTextFilebase)

        self.ctrlStaticFilenameSimpleScan = wx.xrc.XRCCTRL(
            self.ctrlFrame, "ID_STATIC_FILENAME_SIMPLESCAN"
        )

        self.ctrlButtonMultiScan = wx.xrc.XRCCTRL(self.ctrlFrame, "ID_BUTTON_MULTISCAN")
        self.ctrlFrame.Bind(
            wx.EVT_BUTTON,
            self.OnButtonMultiScan,
            wx.xrc.XRCCTRL(self.ctrlFrame, "ID_BUTTON_MULTISCAN"),
        )
        self.ctrlButtonScan = wx.xrc.XRCCTRL(self.ctrlFrame, "ID_BUTTON_SCAN")
        self.ctrlFrame.Bind(
            wx.EVT_BUTTON,
            self.OnButtonScan,
            wx.xrc.XRCCTRL(self.ctrlFrame, "ID_BUTTON_SCAN"),
        )

        self.ctrlPanelStatus = wx.xrc.XRCCTRL(self.ctrlFrame, "ID_PANEL")

        # wx.EVT_MENU(self.ctrlFrame, wx.xrc.XRCID("wxID_EXIT"), self.OnQuit)
        self.ctrlFrame.Bind(
            wx.EVT_MENU, self.OnQuit, wx.xrc.XRCCTRL(self.ctrlFrame, "wxID_EXIT")
        )
        self.ctrlFrame.Bind(
            wx.EVT_CLOSE,
            self.OnCloseWindow,
            wx.xrc.XRCCTRL(self.ctrlFrame, "wxID_CLOSE"),
        )

        self.objTimerStatus = wx.Timer(self.ctrlFrame, ID_TIMER_STATUS)
        # wx.EVT_TIMER(self, ID_TIMER_STATUS, self.OnTimerStatus)
        self.ctrlFrame.Bind(wx.EVT_TIMER, self.OnTimerStatus, self.objTimerStatus)

        self.ctrlFrame.Show(1)
        self.SetTopWindow(self.ctrlFrame)

    def handleException(self, exception, strMessage=None):
        if self.ctrlErrorMessageDialog != None:
            # self.ctrlErrorMessageDialog.DoOk()
            self.ctrlErrorMessageDialog.Destroy()

        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        if strMessage:
            out = io.StringIO()
            traceback.print_exc(file=out)
            strValue = out.getvalue()
            # wx.MessageBox(strValue, strMessage)
            self.ctrlErrorMessageDialog = wx.MessageDialog(
                self.ctrlFrame, strValue, strMessage, wx.OK | wx.ICON_ERROR
            )
            self.ctrlErrorMessageDialog.ShowModal()
            self.ctrlErrorMessageDialog = None
            return
        out = io.StringIO()
        traceback.print_exc(file=out)
        strValue = out.getvalue()
        # wx.MessageBox('Programmierfehler...\n %s ' % strValue, 'Fehler')
        self.ctrlErrorMessageDialog = wx.MessageDialog(
            self.ctrlFrame,
            "Programmierfehler...\n %s " % strValue,
            "Fehler",
            wx.OK | wx.ICON_ERROR,
        )
        self.ctrlErrorMessageDialog.ShowModal()
        self.ctrlErrorMessageDialog = None

    def OnInitTemplates(self):
        try:
            for strScanner in pyscan.engine_scan_wia.getDeviceList():
                self.ctrlChoiceScanner.Append(strScanner)
            strDefaultScanner = self.dictConfig["strDefaultScanner"]
            self.ctrlChoiceScanner.SetStringSelection(strDefaultScanner)

            for strPaperSize in ("A4", "Letter", "Max"):
                self.ctrlChoicePaperSize.Append(strPaperSize)
            strDefaultPaperSize = self.dictConfig["strDefaultPaperSize"]
            self.ctrlChoicePaperSize.SetStringSelection(strDefaultPaperSize)

            for strFilename in os.listdir(directory_vorlagen):
                if not strFilename.startswith("skip_"):
                    if strFilename.endswith(".py"):
                        self.ctrlChoiceTemplate.Append(strFilename)
            self.ctrlChoiceTemplate.Select(0)

            strDefaultTemplate = self.dictConfig["strDefaultTemplate"]
            self.ctrlChoiceTemplate.SetStringSelection(strDefaultTemplate)
        except Exception as e:
            self.handleException(e)

    def OnTimerStatus(self, event):
        try:
            if True:
                iQueueSize = self.objThread.size()
                if iQueueSize > 0:
                    self.ctrlStatusBar.SetStatusText(
                        "Postprocessing: %d images." % iQueueSize, 0
                    )
                else:
                    self.ctrlStatusBar.SetStatusText("Postprocessing: Idle...", 0)
        except Exception as e:
            self.handleException(e)

    def SetStatus(self, bBusy=True):
        if bBusy:
            self.ctrlPanelStatus.SetBackgroundColour(wx.Colour(255, 127, 0))
            self.ctrlButtonScan.Disable()
        else:
            self.ctrlPanelStatus.SetBackgroundColour(wx.Colour(0, 255, 0))
            self.ctrlButtonScan.Enable()
            self.ctrlButtonMultiScan.Enable()
        self.ctrlPanelStatus.Refresh()
        self.Yield()

    def ScannerCancelHandler(self, objException):
        "User Pressed: Cancel"
        try:
            self.ScannerClose()
            self.SetStatus(False)
        except Exception as e:
            self.handleException(e)

    def OnButtonScan(self, event):
        try:
            self.objThread.put(SCAN)
        except Exception as e:
            self.handleException(e)

    def OnButtonMultiScan(self, event):
        try:
            strStop = "Stop"
            strLabel = self.ctrlButtonMultiScan.GetLabel()
            if strLabel == strStop:
                self.ctrlButtonMultiScan.SetLabel("Multiscan")
                self.objThread.bMultiscanStop = True
                return
            self.ctrlButtonMultiScan.SetLabel(strStop)
            self.objThread.put(MULTISCAN)
        except Exception as e:
            self.handleException(e)

    def ReplaceFields(self, strFilename):
        iTime = time.localtime()
        strDayYYYY_MM_DD = time.strftime("%Y-%m-%d", iTime)
        strDayYYYYMMDD = time.strftime("%Y%m%d", iTime)
        strFilename = strFilename.replace(
            "<<FILEBASE>>", self.ctrlTextFilebase.GetValue()
        )
        strFilename = strFilename.replace("<<YYYYMMDD>>", strDayYYYYMMDD)
        strFilename = strFilename.replace("<<YYYY-MM-DD>>", strDayYYYY_MM_DD)
        return strFilename

    def OnUpdateFilename(self, event=None):
        try:
            for ctrl, strPattern in (
                (
                    self.ctrlStaticFilenameSimpleScan,
                    self.dictConfig["strPatternSimplescan"],
                ),
            ):
                strFilename = self.ReplaceFields(strPattern)
                ctrl.SetLabel(strFilename)
        except Exception as e:
            self.handleException(e)

    def OnQuit(self, event):
        try:
            self.objThread.put(CLOSE)
            self.ctrlFrame.Close(True)
        except Exception as e:
            self.handleException(e)

    def OnCloseWindow(self, event):
        try:
            self.objThread.put(CLOSE)
            self.ctrlFrame.Destroy()
        except Exception as e:
            self.handleException(e)


# ----------------------------------------------------------------------------


class ReloadDropTarget(wx.FileDropTarget):
    def __init__(self, ctrlFrame, ctrlText):
        wx.FileDropTarget.__init__(self)
        ctrlText.SetDropTarget(self)
        self.ctrlFrame = ctrlFrame
        self.ctrlText = ctrlText

    def OnDropFiles(self, x, y, listFilenames):
        try:
            # self.window.SetInsertionPointEnd()
            # print("\n%d file(s) dropped at %d,%d:\n" % (len(filenames), x, y))
            # for file in filenames:
            #    print(file + '\n')
            if len(listFilenames) <= 0:
                return
            for strFilename in listFilenames:
                if not os.path.isdir(strFilename):
                    strFilename = os.path.dirname(strFilename)
                self.ctrlText.SetValue(strFilename)
                return
        except Exception as e:
            self.ctrlFrame.handleException(e)


# ----------------------------------------------------------------------------


def main():
    filename_log = os.path.join(directory, "wxPyScan_log.txt")
    wx.InitAllImageHandlers()
    app = wxPyScanApp(1, filename_log)
    # app = wxPyScanApp(0)
    app.MainLoop()


if __name__ == "__main__":
    main()
