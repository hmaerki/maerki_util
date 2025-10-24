#! python3.7
#!/usr/bin/env python

# ----------------------------------------------------------------------------
# Name:     wxhttpupload.py
# Author:     XXXX
# Created:    XX/XX/XX
# Copyright:
# ----------------------------------------------------------------------------

import os
import pathlib
import threading
import time

import wx

from wxhttpupload import httpupload
from wxhttpupload.wxhttpupload_wdr import *

# constants
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_RESOURCES = DIRECTORY_OF_THIS_FILE / "resources"
assert DIRECTORY_RESOURCES.is_dir()

ID_QUIT = 100
strWxHttpUpload = "v1.1.8"
objLogger = None
dictConfig = None


# WDR: classes
class HttpUploadFrame(wx.Frame):
    def __init__(
        self,
        parent,
        id,
        title,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.DEFAULT_FRAME_STYLE,
    ):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self.isClosing = False

        def get_icon(filename: str):
            return wx.Icon(
                str(DIRECTORY_RESOURCES / filename), wx.BITMAP_TYPE_ICO
            )

        self.dictIcons = {
            "error": get_icon("wxhttpupload_error.ico"),
            "work": get_icon("wxhttpupload_work.ico"),
            "success": get_icon("wxhttpupload_success.ico"),
            "idle": get_icon("wxhttpupload_idle.ico"),
        }

        self.bWebdriveMount = True

        # insert main window here
        panel = wx.Panel(self, -1)
        tabbedDialogFunc(panel)

        objLogger.SetCtrlText(self.FindWindowById(ID_TEXTCTRL_LOG))
        objUploadMediator.setCtrlFrame(self)

        self.ctrlTextConfig = self.FindWindowById(ID_TEXTCTRL_ZULU_FOLDER)
        self.ctrlUploadConfig = self.FindWindowById(ID_CHOICE_UPLOAD_CONFIGURATIONS)
        self.ctrlTextStatus = self.FindWindowById(ID_TEXT_STATUS)
        self.ctrlButtonUpload = self.FindWindowById(ID_BUTTON_UPLOAD_GO)
        self.ctrlButtonForceUpload = self.FindWindowById(ID_BUTTON_UPLOAD_FORCE)
        UploadFileDropTarget(self.ctrlUploadConfig)
        self.setIcon()

        # WDR: handler declarations for HttpUploadFrame

        self.Bind(
            wx.EVT_BUTTON,
            self.OnUploadConfig,
            self.FindWindowById(ID_BUTTON_UPLOAD_CONFIG),
        )
        self.Bind(
            wx.EVT_BUTTON,
            self.OnUploadConfigFolder,
            self.FindWindowById(ID_BUTTON_UPLOAD_CONFIGFOLDER),
        )
        self.Bind(
            wx.EVT_BUTTON,
            self.OnUploadWebdrive,
            self.FindWindowById(ID_BUTTON_UPLOAD_WEBDRIVE),
        )
        self.Bind(
            wx.EVT_BUTTON, self.OnUploadGo, self.FindWindowById(ID_BUTTON_UPLOAD_GO)
        )
        self.Bind(
            wx.EVT_BUTTON,
            self.OnUploadForce,
            self.FindWindowById(ID_BUTTON_UPLOAD_FORCE),
        )
        self.Bind(
            wx.EVT_BUTTON,
            self.OnUploadErrorlog,
            self.FindWindowById(ID_BUTTON_UPLOAD_ERRORLOG),
        )
        self.Bind(
            wx.EVT_CHECKBOX,
            self.OnUploadAuto,
            self.FindWindowById(ID_CHECKBOX_AUTOUPLOAD),
        )
        self.Bind(
            wx.EVT_BUTTON, self.OnUploadLocal, self.FindWindowById(ID_BUTTON_LOCAL)
        )
        self.Bind(
            wx.EVT_BUTTON, self.OnUploadRemote, self.FindWindowById(ID_BUTTON_REMOTE)
        )
        self.Bind(
            wx.EVT_BUTTON, self.OnZuluFolder, self.FindWindowById(ID_BUTTON_ZULU_FOLDER)
        )
        self.Bind(
            wx.EVT_BUTTON,
            self.OnZuluErrorlog,
            self.FindWindowById(ID_BUTTON_ZULU_ERRORLOG),
        )
        self.Bind(wx.EVT_BUTTON, self.OnZuluGo, self.FindWindowById(ID_BUTTON_ZULU_GO))
        self.Bind(
            wx.EVT_BUTTON,
            self.OnZuluUploadGo,
            self.FindWindowById(ID_BUTTON_ZULU_UPLOAD_GO),
        )
        self.Bind(wx.EVT_MENU, self.OnQuit, self.FindWindowById(ID_QUIT))
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(
            wx.EVT_CHOICE,
            self.EvtChoice,
            self.FindWindowById(ID_CHOICE_UPLOAD_CONFIGURATIONS),
        )

    # WDR: methods for HttpUploadFrame
    def setIcon(self, strTag="idle"):
        self.SetIcon(self.dictIcons[strTag])

    def setStatus(self, strLine):
        self.ctrlTextStatus.SetLabel(strLine)

    def setRunning(self, isRunning):
        if isRunning:
            objUploadMediator.ctrlFrame.ctrlButtonUpload.SetLabel("Stop")
        else:
            objUploadMediator.ctrlFrame.ctrlButtonUpload.SetLabel("Upload")
            ctrlCheckBox = objUploadMediator.ctrlFrame.FindWindowById(
                ID_CHECKBOX_AUTOUPLOAD
            )
            ctrlCheckBox.SetValue(False)
        self.ctrlButtonForceUpload.Enable(not isRunning)

    def InsertConfigurations(self, listConfigurations):
        self.ctrlUploadConfig.Clear()
        for dictSingleConfig in listConfigurations:
            self.ctrlUploadConfig.Append(
                dictSingleConfig.get("name", "Error: name not defined ..."),
                dictSingleConfig,
            )
        self.ctrlUploadConfig.SetSelection(0)
        self.UpdateConfiguration()

        ctrlConfigFolder = self.FindWindowById(ID_TEXT_UPLOAD_CONFIGFOLDER)
        ctrlConfigFolder.SetLabel(dictConfig["configfile_path"])
        ctrlWebdriveText = self.FindWindowById(ID_TEXTCTRL_UPLOAD_WEBDRIVE)
        ctrlWebdriveText.SetValue(dictConfig["webdrive_drive"])

    def UpdateConfiguration(self, bGetValues=False):
        dictFields = {
            "local": ID_TEXTCTRL_UPLOAD_LOCAL,
            "remote": ID_TEXTCTRL_UPLOAD_REMOTE,
            "user": ID_TEXTCTRL_UPLOAD_USER,
            "password": ID_TEXTCTRL_UPLOAD_PASSWORD,
            "zulu": ID_TEXTCTRL_ZULU_FOLDER,
        }

        if bGetValues:
            # Get the default-values from the file
            dictValues = self.ctrlUploadConfig.GetClientData(
                self.ctrlUploadConfig.GetSelection()
            )
            for strTagName, iID in dictFields.items():
                dictValues[strTagName] = self.GetValue(iID)
            return dictValues

        dictUploadConfig = self.ctrlUploadConfig.GetClientData(
            self.ctrlUploadConfig.GetSelection()
        )
        for strTagName, iID in dictFields.items():
            ctrl = self.FindWindowById(iID)
            ctrl.SetValue(
                dictUploadConfig.get(
                    strTagName, 'Error: Tag "%s" not defined ...' % strTagName
                )
            )

    def GetValue(self, iID):
        ctrlText = self.FindWindowById(iID)
        strValue = ctrlText.GetValue()
        strValue = strValue.replace("{CONFIG}", dictConfig["configfile_path"])
        return strValue

    # WDR: handler implementations for HttpUploadFrame

    def EvtChoice(self, event):
        # objLogger.WriteText('EvtChoice: %s\n' % event.GetString())
        self.UpdateConfiguration()

    def OnUploadWebdrive(self, event):
        ctrlButton = self.FindWindowById(ID_BUTTON_UPLOAD_WEBDRIVE)
        if self.bWebdriveMount:
            ctrlButton.SetLabel("Unmount")
        else:
            ctrlButton.SetLabel("Mount")

        if False:
            from win32com.shell.shell import SHGetSpecialFolderPath

            # see http://aspn.activestate.com//ASPN/Python/Reference/Products/ActivePython/win32com/shell__SHGetSpecialFolderPath_meth.html
            # CSIDL_PROGRAM_FILES = &H26 (38)
            strProgramFolder = SHGetSpecialFolderPath(0, 38, 0)
        else:
            strProgramFolder = os.getenv("ProgramFiles")
        strPathWebDrive = r"{PROGRAMS}\WebDrive\webdrive.exe"
        strPathWebDrive = strPathWebDrive.replace("{PROGRAMS}", strProgramFolder)

        strArgs = "%s /d" % self.FindWindowById(ID_TEXTCTRL_UPLOAD_WEBDRIVE).GetValue()
        # win32_ShellExecute(strPathWebDrive, strArgs)
        wx.Execute("%s %s" % (strPathWebDrive, strArgs), wx.EXEC_ASYNC)

        if self.bWebdriveMount:
            # from win32api import Sleep
            # Sleep(1000, 0)
            strArgs = (
                '/s:"http_upload_test" /u:"%s" /p:"%s" /url:"%s" /d:%s /pr:1 /exp'
                % (
                    self.GetValue(ID_TEXTCTRL_UPLOAD_USER),
                    self.GetValue(ID_TEXTCTRL_UPLOAD_PASSWORD),
                    self.GetValue(ID_TEXTCTRL_UPLOAD_REMOTE),
                    self.GetValue(ID_TEXTCTRL_UPLOAD_WEBDRIVE),
                )
            )
            # win32_ShellExecute(strPathWebDrive, strArgs)
            wx.Execute("%s %s" % (strPathWebDrive, strArgs), wx.EXEC_ASYNC)
        self.bWebdriveMount = not self.bWebdriveMount

    def OnUploadLocal(self, event):
        win32_ShellExecute(self.GetValue(ID_TEXTCTRL_UPLOAD_LOCAL))

    def OnUploadRemote(self, event):
        win32_ShellExecute(self.GetValue(ID_TEXTCTRL_UPLOAD_REMOTE))

    def OnUploadConfigFolder(self, event):
        win32_ShellExecute(self.FindWindowById(ID_TEXT_UPLOAD_CONFIGFOLDER).GetLabel())

    def OnUploadAuto(self, event):
        objUploadWrapper.GoAutoUpload()

    def OnUploadConfig(self, event):
        win32_ShellExecute(
            "%s\\wxhttpupload_config.txt" % dictConfig["configfile_path"], "notepad"
        )

    def OnUploadErrorlog(self, event):
        win32_ShellExecute(objUploadWrapper.getFilenameHtmlLog())

    def OnUploadGo(self, event):
        objUploadWrapper.GoOneShot(False)

    def OnUploadForce(self, event):
        objUploadWrapper.GoOneShot(True)

    def OnZuluFolder(self, event):
        win32_ShellExecute(self.GetValue(ID_TEXTCTRL_ZULU_FOLDER))

    def OnZuluErrorlog(self, event):
        win32_ShellExecute(
            "%s\\zulu_errorlog.html" % self.GetValue(ID_TEXTCTRL_ZULU_FOLDER)
        )

    def OnZuluGo(self, event):
        objZuluWrapper.go()

    def OnZuluUploadGo(self, event):
        iError = objZuluWrapper.go()
        if iError:
            return
        objUploadWrapper.GoOneShot(False)

    def OnQuit(self, event):
        if objUploadWrapper.running:
            objUploadWrapper.Stop()
            wx.MessageBox(
                "Stopping the active upload.", "Exit Application", wx.OK, self
            )
            return
        self.isClosing = True
        self.Close(True)
        self.Destroy()

    def OnCloseWindow(self, event):
        if self.isClosing:
            # Avoid recursion
            return
        self.OnQuit(event)

    def OnSize(self, event):
        event.Skip(True)


# ----------------------------------------------------------------------------


class wxhttpuploadApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        self.frameMain = HttpUploadFrame(
            None,
            -1,
            "wxhttpupload %s" % strWxHttpUpload,
            wx.Point(20, 20),
            wx.Size(540, 500),
        )
        self.frameMain.Show(True)

        self.InsertConfigurations(pathlib.Path.cwd() / "wxhttpupload_config.txt")
        return True

    def InsertConfigurations(self, strConfigFilename: pathlib.Path):
        global dictConfig
        dictConfig = {"webdrive_drive": "W:"}
        try:
            with open(strConfigFilename) as f:
                code = compile(f.read(), strConfigFilename, "exec")
                global_vars = {}
                exec(code, global_vars, dictConfig)
        except IOError:
            objLogger.WriteLine(
                f"Configuration File '{strConfigFilename.name} not found in folder '{strConfigFilename.parent}'."
            )
        if dictConfig.get("wxhttpupload_config_version", None) != "1.0.0":
            objLogger.WriteLine(
                "This Configuration-Version is too old for this '%s'"
                % strConfigFilename
            )

        dictConfig["configfile_path"], dictConfig["configfile_filename"] = (
            os.path.split(strConfigFilename)
        )
        self.frameMain.InsertConfigurations(
            dictConfig.get("wxhttpupload_configurations", None)
        )


# ----------------------------------------------------------------------------


class Logger:
    def SetCtrlText(self, ctrlText):
        self.ctrlText = ctrlText

    def WriteLine(self, strLine):
        self.WriteText("\n" + strLine)

    def WriteText(self, strText):
        self.ctrlText.AppendText(strText)
        self.ctrlText.SetInsertionPointEnd()


# ----------------------------------------------------------------------------


class UploadFileDropTarget(wx.FileDropTarget):
    def __init__(self, ctrlText):
        wx.FileDropTarget.__init__(self)
        self.ctrlText = ctrlText
        self.ctrlText.SetDropTarget(self)

    def OnDropFiles(self, x, y, filenames):
        # self.window.SetInsertionPointEnd()
        # print("\n%d file(s) dropped at %d,%d:\n" % (len(filenames), x, y))
        # for file in filenames:
        #  print(file + '\n')
        if len(filenames) >= 1:
            app.InsertConfigurations(filenames[0])


# ----------------------------------------------------------------------------


class UploadWrapper:
    def __init__(self):
        self.running = False
        self.keepGoing = False

    def GoAutoUpload(self):
        if self.running:
            # Already running: Ignore and stop
            self.Stop()
            return

        ctrlCheckBox = objUploadMediator.ctrlFrame.FindWindowById(
            ID_CHECKBOX_AUTOUPLOAD
        )
        if ctrlCheckBox.IsChecked():
            self.GoOneShot(False, False)
        else:
            self.Stop()

    def SetRunning(self, running):
        # This method will be called everytime 'self.running' changes
        self.running = running
        objUploadMediator.ctrlFrame.setRunning(running)

    def Stop(self):
        self.keepGoing = False

    def GoOneShot(self, bForce, oneShot=True):
        if self.running:
            # Already running: Stop
            self.keepGoing = False
            return
        self.keepGoing = True
        self.prepareConfiguraton(bForce)
        objThread = threading.Thread(target=self.Run, args=(oneShot,))
        objThread.start()

    def Run(self, oneShot):
        try:
            self.Run_(oneShot)
        except Exception as e:
            objLogger.WriteLine("----- ERROR in Thread! %s" % str(e))

    def Run_(self, oneShot):
        self.SetRunning(True)
        iRetries = 1
        iMaxRetries = 20
        iWaitSeconds = 30

        while self.keepGoing:
            objUploadMediator.ctrlFrame.setIcon("work")
            iError = httpupload.HttpUpload(objUploadMediator)
            if oneShot:
                if iError == 0:
                    break
                iRetries += 1
                if iRetries > iMaxRetries:
                    break
                objLogger.WriteLine(
                    "Versuch %d von %d folgt in %d Sekunden."
                    % (iRetries, iMaxRetries, iWaitSeconds)
                )
                # Wait and allow user to interrupt
                for i in range(iWaitSeconds):
                    time.sleep(1.0)
                    if not self.keepGoing:
                        break
                continue
            if self.keepGoing:
                time.sleep(5.0)

        self.SetRunning(False)

    def getFilenameHtmlLog(self):
        dictArguments = objUploadMediator.ctrlFrame.UpdateConfiguration(True)
        objUploadMediator.setArguments(dictArguments)
        return objUploadMediator.getArgument("FilenameHtmlLog")

    def prepareConfiguraton(self, bForce=False):
        dictArguments = objUploadMediator.ctrlFrame.UpdateConfiguration(True)
        objLogger.WriteLine("Go '%s':" % dictArguments["local"])
        # objLogger.WriteLine("Folder: %s" % objMediator.getFolder())
        objUploadMediator.setArguments(dictArguments)
        objUploadMediator.setSingleArgument("ForceUpload", bForce)


# ----------------------------------------------------------------------------


class UploadMediator:
    def setCtrlFrame(self, ctrlFrame):
        self.ctrlFrame = ctrlFrame

    def writeLine(self, strLine):
        objLogger.WriteLine(strLine)

    def setStatus(self, strLine):
        self.ctrlFrame.setStatus(strLine)

    def setSingleArgument(self, strKey, objValue):
        self.dictArguments[strKey] = objValue

    def setArguments(self, dictArguments):
        self.dictArguments = dictArguments
        self.dictArguments["FilenameHtmlLog"] = os.path.normpath(
            "%s/tmp_httpupload_log.html" % self.getArgument("local")
        )

    def getArgument(self, strName, objDefault=None):
        return self.dictArguments.get(strName, objDefault)

    def keepRunning(self):
        return objUploadWrapper.keepGoing

    def end(self, iError):
        if iError == 0:
            objLogger.WriteLine("----- SUCCESS!")
            self.ctrlFrame.setIcon("success")
        else:
            objLogger.WriteLine("----- ERROR (iError==%d)!" % iError)
            self.ctrlFrame.setIcon("error")


# ----------------------------------------------------------------------------


class ZuluWrapper:
    def getZuluPath(self):
        return objUploadMediator.ctrlFrame.GetValue(ID_TEXTCTRL_ZULU_FOLDER)

    def go(self):
        strCurrentDirectory = os.getcwd()
        strZuluPath = self.getZuluPath()
        objLogger.WriteLine("ZULU")
        objLogger.WriteLine("Folder: %s" % strZuluPath)
        try:
            os.chdir(strZuluPath)
            iError = os.system("zulu")
        except OSError as e:
            objLogger.WriteLine("Fehler: " + str(e))
            iError = 1
        if iError == 0:
            objLogger.WriteLine("----- SUCCESS!")
        else:
            objLogger.WriteLine("----- ERROR (iError==%d)!" % iError)
        objLogger.WriteLine("")
        os.chdir(strCurrentDirectory)
        return iError


# ----------------------------------------------------------------------------


def win32_ShellExecute(strFile, strCommand="explorer", strArgs=None):
    if False:
        "see http://aspn.activestate.com/ASPN/Python/Reference/Products/ActivePython/PythonWin32Extensions/win32api__ShellExecute_meth.html"
        from win32api import ShellExecute

        ShellExecute(0, "open", strFile, strArgs, ".", 1)
    else:
        if strArgs != None:
            wx.Execute("%s %s" % (strFile, strArgs), wx.EXEC_ASYNC)
        else:
            os.startfile(strFile)
            # wx.Execute('%s %s' % (strCommand, strFile), wx.EXEC_ASYNC)


# ----------------------------------------------------------------------------


def main():
    global objLogger
    global dictConfig
    global objUploadMediator
    global objUploadWrapper
    global objZuluWrapper
    objUploadMediator = UploadMediator()
    objUploadWrapper = UploadWrapper()
    objZuluWrapper = ZuluWrapper()
    objLogger = Logger()
    dictConfig = {}
    app = wxhttpuploadApp(1)
    app.MainLoop()


if __name__ == "__main__":
    main()
