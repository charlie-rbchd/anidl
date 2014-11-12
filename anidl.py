import wx
import shelve
import scrape
import download

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(365, 465))

        # Open database
        self.userConfig = shelve.open("config", writeback=True)
        download.open()

        # Elements creation
        self.SetBackgroundColour('white')
        self.CreateStatusBar()

        dirPickerLabel = wx.StaticText(self, -1, "Download directory")
        self.dirPicker = wx.DirPickerCtrl(self, -1, self.userConfig["downloadDir"] if "downloadDir" in self.userConfig else "", "Select your download directory")

        listUrlLabel = wx.StaticText(self, -1, "Anilist username")
        self.listUrlTextInput = wx.TextCtrl(self, -1, self.userConfig["anilistUsername"] if "anilistUsername" in self.userConfig else "")

        self.checkListToggle = wx.CheckBox(self, -1, "Select/Deselect all")
        self.checkListToggle.SetValue(True)
        self.checkList = wx.CheckListBox(self, -1)

        downloadButton = wx.Button(self, -1, "Download my chinese cartoons")

        # Menu creation
        fileMenu = wx.Menu()
        refreshMenuItem = fileMenu.Append(-1, "Refresh\tCtrl+R")
        fileMenu.AppendSeparator()
        downloadMenuItem = fileMenu.Append(-1, "Download and Exit\tCtrl+Shift+D", " Download selected cartoons and terminate the program.")
        exitMenuItem = fileMenu.Append(wx.ID_EXIT, "Exit without downloading\tCtrl+W", " Terminate the program.")

        editMenu = wx.Menu()
        selectAllMenuItem = editMenu.Append(-1, "Select All\tCtrl+A")
        deselectAllMenuItem = editMenu.Append(-1, "Deselect All\tCtrl+D")

        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(editMenu, "&Edit")
        self.SetMenuBar(menuBar)

        # Event bindings
        self.Bind(wx.EVT_BUTTON, self.OnDownload, downloadButton)
        self.Bind(wx.EVT_CHECKBOX, self.OnToggleSelection, self.checkListToggle)
        self.Bind(wx.EVT_TEXT, self.OnUsernameChange, self.listUrlTextInput)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDownloadPathChange, self.dirPicker)
        self.Bind(wx.EVT_CLOSE, self.OnClose, self)

        self.Bind(wx.EVT_MENU, self.OnRefresh, refreshMenuItem)
        self.Bind(wx.EVT_MENU, self.OnDownload, downloadMenuItem)
        self.Bind(wx.EVT_MENU, self.OnExit, exitMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAll, selectAllMenuItem)
        self.Bind(wx.EVT_MENU, self.OnDeselectAll, deselectAllMenuItem)

        # Elements sizing and positing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(dirPickerLabel, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)
        sizer.Add(self.dirPicker, 0, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.Add(listUrlLabel, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)
        sizer.Add(self.listUrlTextInput, 0, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.AddSpacer(15)
        sizer.Add(self.checkListToggle, 0, wx.ALL, 5)
        sizer.Add(self.checkList, 0, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT)
        sizer.Add(downloadButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 15)
        self.SetSizer(sizer)

        self.Show(True)
        self.FetchData()

    def SelectAll(self):
        for i in range(len(self.checkListItems)):
            self.checkList.Check(i)

    def DeselectAll(self):
        for i in range(len(self.checkListItems)):
            self.checkList.Check(i, False)

    def FetchData(self):
        self.checkList.Clear()
        self.checkListItems = scrape.fetch(self.userConfig["anilistUsername"])

        if (len(self.checkListItems) != 0):
            self.checkList.InsertItems([entry[0] for entry in self.checkListItems], 0)
            self.SelectAll()

        self.checkList.SetFocus()

    def OnRefresh(self, evt):
        self.FetchData()

    def OnDownload(self, evt):
        for i in range(len(self.checkListItems)):
            if (self.checkList.IsChecked(i)):
                download.torrent(self.checkListItems[i], self.userConfig["downloadDir"])

        self.Close(True)

    def OnToggleSelection(self, evt):
        if self.checkListToggle.IsChecked():
            self.SelectAll()
        else:
            self.DeselectAll()

    def OnUsernameChange(self, evt):
        self.userConfig["anilistUsername"] = self.listUrlTextInput.GetLineText(0)

    def OnDownloadPathChange(self, evt):
        self.userConfig["downloadDir"] = self.dirPicker.GetPath()

    def OnSelectAll(self, evt):
        self.SelectAll()

    def OnDeselectAll(self, evt):
        self.DeselectAll()

    def OnExit(self, evt):
        self.Close(True)

    def OnClose(self, evt):
        self.userConfig.close()
        download.close()

        self.Destroy()

app = wx.App(False)
frame = MainWindow(None, "Anidl")
app.MainLoop()
