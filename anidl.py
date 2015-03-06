import os
import shelve
import scrape
import download

# Ignore wxWidgets/wxWidgets version mismatch warnings.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import wx

from wx.lib.delayedresult import startWorker
import wx.dataview as dv
import wx.lib.agw.pyprogress as pp


class AliasConfigWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Configure Aliases",  size=(725, 400))

        # Elements creation
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour("#ffffff")

        self.dataView = dv.DataViewListCtrl(self.panel, -1)
        self.dataView.AppendTextColumn("Title", width=250)
        self.dataView.AppendTextColumn("Alias", width=450, mode=dv.DATAVIEW_CELL_EDITABLE)

        # Event bindings
        self.Bind(dv.EVT_DATAVIEW_ITEM_EDITING_DONE, self.OnAliasChange, self.dataView)
        self.Bind(wx.EVT_SHOW, self.OnShow, self)
        self.Bind(wx.EVT_CLOSE, self.OnClose, self)

        # Elements sizing and positing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.dataView, 1, wx.EXPAND | wx.ALL, 0)

        self.panel.SetSizer(sizer)
        self.panel.Layout()

        self.SetIcon(wx.Icon("anidl.exe" if os.path.exists("anidl.exe") else "anidl.ico", wx.BITMAP_TYPE_ICO))

    def OnAliasChange(self, evt):
        # TODO: Update the aliases user config.
        # TODO: Separate multiple values with semi-colons.
        pass

    def OnShow(self, evt):
        if evt.GetShow():
            for title, alias in self.GetParent().userConfig["aliases"].items():
                self.dataView.AppendItem([title, "; ".join(alias)])
        else:
            self.dataView.DeleteAllItems()

    def OnClose(self, evt):
        self.Show(False)


class MainWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Anidl", size=(400, 525))

        # Open config file
        self.userConfig = shelve.open("config", writeback=True)

        if "aliases" not in self.userConfig:
            self.userConfig["aliases"] = {}

        # Elements creation
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour("#ffffff")

        dirPickerLabel = wx.StaticText(self.panel, -1, "Download directory")
        dirPickerDefaultValue = self.userConfig["downloadDir"] if "downloadDir" in self.userConfig else ""
        self.dirPicker = wx.DirPickerCtrl(self.panel, -1, dirPickerDefaultValue, "Select your download directory")

        listUrlLabel = wx.StaticText(self.panel, -1, "Anilist username")
        listUrlTextInputDefaultValue = self.userConfig["anilistUsername"] if "anilistUsername" in self.userConfig else ""
        self.listUrlTextInput = wx.TextCtrl(self.panel, -1, listUrlTextInputDefaultValue)

        listBoxLabel = wx.StaticText(self.panel, -1, "Target qualities")
        self.listBoxItems = ["480p", "720p", "1080p"]
        self.listBox = wx.ListBox(self.panel, -1, choices=self.listBoxItems, style=wx.LB_MULTIPLE)

        if "selectedListBoxItems" in self.userConfig:
            for item in self.userConfig["selectedListBoxItems"]:
                self.listBox.SetSelection(item)
        else:
            for i in range(len(self.listBoxItems)):
                self.listBox.SetSelection(i)

        comboBoxLabel = wx.StaticText(self.panel, -1, "Episodes look-ahead")
        self.comboBox = wx.ComboBox(self.panel, -1, choices=["1", "2", "3"], style=wx.CB_READONLY)
        self.comboBox.SetSelection(self.userConfig["selectedComboBoxItem"] if "selectedComboBoxItem" in self.userConfig else 0)

        self.checkListToggle = wx.CheckBox(self.panel, -1, "Select/Deselect all")
        self.checkListToggle.SetValue(True)
        self.checkList = wx.CheckListBox(self.panel, -1, choices=[""]*10)

        downloadButton = wx.Button(self.panel, -1, "Download my chinese cartoons")

        self.aliasConfigWindow = AliasConfigWindow(self)

        # Menu creation
        fileMenu = wx.Menu()
        refreshMenuItem = fileMenu.Append(-1, "Refresh\tCtrl+R")
        fileMenu.AppendSeparator()
        downloadMenuItem = fileMenu.Append(-1, "Download and Exit\tCtrl+Shift+D",
                                           "Download selected cartoons and terminate the program.")
        exitMenuItem = fileMenu.Append(wx.ID_EXIT, "Exit without downloading\tCtrl+W", " Terminate the program.")

        editMenu = wx.Menu()
        selectAllMenuItem = editMenu.Append(-1, "Select All\tCtrl+A")
        deselectAllMenuItem = editMenu.Append(-1, "Deselect All\tCtrl+D")
        editMenu.AppendSeparator()
        configureAliasesMenuItem = editMenu.Append(-1, "Configure Aliases\tCtrl+Shift+A")

        menuBar = wx.MenuBar()
        menuBar.Append(fileMenu, "&File")
        menuBar.Append(editMenu, "&Edit")
        self.SetMenuBar(menuBar)

        # Event bindings
        self.Bind(wx.EVT_BUTTON, self.OnDownload, downloadButton)
        self.Bind(wx.EVT_CHECKBOX, self.OnToggleSelection, self.checkListToggle)
        self.Bind(wx.EVT_TEXT, self.OnUsernameChange, self.listUrlTextInput)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDownloadPathChange, self.dirPicker)
        self.Bind(wx.EVT_LISTBOX, self.OnQualityChange, self.listBox)
        self.Bind(wx.EVT_COMBOBOX, self.OnEpisodeLookAheadChange, self.comboBox)
        self.Bind(wx.EVT_CLOSE, self.OnClose, self)

        self.Bind(wx.EVT_MENU, self.OnRefresh, refreshMenuItem)
        self.Bind(wx.EVT_MENU, self.OnDownload, downloadMenuItem)
        self.Bind(wx.EVT_MENU, self.OnExit, exitMenuItem)
        self.Bind(wx.EVT_MENU, self.OnSelectAll, selectAllMenuItem)
        self.Bind(wx.EVT_MENU, self.OnDeselectAll, deselectAllMenuItem)
        self.Bind(wx.EVT_MENU, self.OnConfigureAliases, configureAliasesMenuItem)

        # Elements sizing and positing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(dirPickerLabel, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)
        sizer.Add(self.dirPicker, 0, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.Add(listUrlLabel, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)
        sizer.Add(self.listUrlTextInput, 0, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT, 5)

        filtersSizer = wx.FlexGridSizer(2, 2)
        filtersSizer.Add(listBoxLabel, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)
        filtersSizer.Add(comboBoxLabel, 0, wx.TOP | wx.LEFT | wx.RIGHT | wx.ALIGN_LEFT, 5)
        filtersSizer.Add(self.listBox, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        filtersSizer.Add(self.comboBox, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        sizer.Add(filtersSizer, 0)

        sizer.AddSpacer(15)
        sizer.Add(self.checkListToggle, 0, wx.ALL, 5)
        sizer.Add(self.checkList, 0, wx.EXPAND | wx.ALL | wx.ALIGN_LEFT)
        sizer.Add(downloadButton, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 15)

        self.panel.SetSizer(sizer)
        self.panel.Layout()

        self.SetIcon(wx.Icon("anidl.exe" if os.path.exists("anidl.exe") else "anidl.ico", wx.BITMAP_TYPE_ICO))
        self.Show(True)

        self.FetchData()

    def SelectAll(self):
        self.checkListToggle.SetValue(True)

        for i in range(len(self.checkListItems)):
            self.checkList.Check(i)

    def DeselectAll(self):
        self.checkListToggle.SetValue(False)

        for i in range(len(self.checkListItems)):
            self.checkList.Check(i, False)

    def FetchData(self):
        self.checkList.Clear()

        unselectedQualities = [self.listBoxItems[i] for i in range(
            len(self.listBoxItems)) if i not in self.listBox.GetSelections()]

        startWorker(self.OnDataFetched, self.FetchDataWorker, wargs=(
            self.listUrlTextInput.GetLineText(0),
            unselectedQualities,
            int(self.comboBox.GetSelection()) + 1,
            self.userConfig["aliases"]))

        # Progress Dialog
        self.progressComplete = False
        self.progressDialog = pp.PyProgress(self, -1, "Fetching data", "This may take a while...",
                                            wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME)
        self.progressDialog.SetGaugeProportion(0.33)
        self.progressDialog.SetGaugeSteps(60)
        self.progressDialog.SetSecondGradientColour("#19202c")

        keepGoing = True
        while keepGoing and not self.progressComplete:
            wx.MilliSleep(30)
            keepGoing = self.progressDialog.UpdatePulse()

        self.progressDialog.ReenableOtherWindows()
        self.progressDialog.Destroy()
        del self.progressComplete, self.progressDialog

    def FetchDataWorker(self, anilist_username, blacklisted_qualities, look_ahead, aliases):
        return scrape.fetch(anilist_username, blacklisted_qualities, look_ahead, aliases)

    def OnDataFetched(self, result):
        try:
            self.checkListItems = result.get()
        except Exception as e:
            print e
            self.checkListItems = []

        if len(self.checkListItems) != 0:
            self.checkList.InsertItems([entry["name"] for entry in self.checkListItems], 0)
            self.SelectAll()

        self.progressComplete = True
        self.checkList.SetFocus()

    def OnRefresh(self, evt):
        self.FetchData()

    def OnConfigureAliases(self, evt):
        self.aliasConfigWindow.Show(True)

    def OnDownload(self, evt):
        download.open()
        for i in range(len(self.checkListItems)):
            if self.checkList.IsChecked(i):
                download.torrent(self.checkListItems[i], self.dirPicker.GetPath())
        download.close()

        self.Close(True)

    def OnToggleSelection(self, evt):
        if self.checkListToggle.IsChecked():
            self.SelectAll()
        else:
            self.DeselectAll()

    def OnEpisodeLookAheadChange(self, evt):
        self.userConfig["selectedComboBoxItem"] = self.comboBox.GetSelection()

    def OnQualityChange(self, evt):
        self.userConfig["selectedListBoxItems"] = self.listBox.GetSelections()

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
        self.Destroy()


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None)
    app.MainLoop()
