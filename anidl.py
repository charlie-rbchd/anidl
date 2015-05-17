import os
import shelve
import scrape
import download
import wx.dataview as dv

from wx.lib.delayedresult import startWorker

# Ignore wxWidgets/wxWidgets version mismatch warnings.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import wx

class AliasConfigWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Configure Aliases",  size=(625, 400))

        # Elements creation
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour("#ffffff")

        self.dataView = dv.DataViewListCtrl(self.panel, wx.ID_ANY)
        self.dataView.AppendTextColumn("Title", width=250,
                                       flags=dv.DATAVIEW_COL_RESIZABLE | dv.DATAVIEW_COL_SORTABLE)
        self.dataView.AppendTextColumn("Alias  (Separate multiple values with semicolons)", width=350,
                                       mode=dv.DATAVIEW_CELL_EDITABLE,
                                       flags=dv.DATAVIEW_COL_RESIZABLE | dv.DATAVIEW_COL_SORTABLE)

        # Event bindings
        self.Bind(dv.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.OnAliasChanged, self.dataView)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUp)
        self.Bind(wx.EVT_SHOW, self.OnShow, self)
        self.Bind(wx.EVT_CLOSE, self.OnClose, self)

        # Elements sizing and positing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.dataView, 1, wx.EXPAND | wx.ALL, 0)

        self.panel.SetSizer(sizer)
        self.panel.Layout()

        self.SetIcon(wx.Icon("anidl.exe" if os.path.exists("anidl.exe") else "anidl.ico", wx.BITMAP_TYPE_ICO))

    def OnAliasChanged(self, evt):
        updatedRow = self.dataView.ItemToRow(evt.GetItem())
        updatedRowTitle = self.dataView.GetTextValue(updatedRow, 0)
        updatedRowAlias = self.dataView.GetTextValue(updatedRow, 1)

        aliases = self.GetParent().userConfig["aliases"]
        aliases[updatedRowTitle] = [alias.strip() for alias in updatedRowAlias.split(";")] if updatedRowAlias else []

    def OnShow(self, evt):
        if evt.GetShow():
            for title, alias in self.GetParent().userConfig["aliases"].items():
                self.dataView.AppendItem([title, "; ".join(alias)])
        else:
            self.dataView.DeleteAllItems()

    def OnClose(self, evt):
        self.Show(False)

    def OnKeyUp(self, evt):
        if evt.GetKeyCode() == wx.WXK_DELETE and self.dataView.HasSelection():
            deletedRow = self.dataView.ItemToRow(self.dataView.GetSelection())
            deletedRowTitle = self.dataView.GetTextValue(deletedRow, 0)
            del self.GetParent().userConfig["aliases"][deletedRowTitle]
            self.dataView.DeleteItem(deletedRow)

        evt.Skip()

class MainWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Anidl", size=(400, 525))

        # Open config file
        self.userConfig = shelve.open("config", writeback=True)

        if "aliases" not in self.userConfig:
            self.userConfig["aliases"] = {}

        # Elements creation
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetBackgroundColour("#ffffff")

        dirPickerLabel = wx.StaticText(self.panel, wx.ID_ANY, "Download directory")
        dirPickerDefaultValue = self.userConfig["downloadDir"] if "downloadDir" in self.userConfig else ""
        self.dirPicker = wx.DirPickerCtrl(self.panel, wx.ID_ANY, dirPickerDefaultValue, "Select your download directory")

        listUrlLabel = wx.StaticText(self.panel, wx.ID_ANY, "Anilist username")
        listUrlTextInputDefaultValue = self.userConfig["anilistUsername"] if "anilistUsername" in self.userConfig else ""
        self.listUrlTextInput = wx.TextCtrl(self.panel, wx.ID_ANY, listUrlTextInputDefaultValue)

        listBoxLabel = wx.StaticText(self.panel, wx.ID_ANY, "Target qualities")
        self.listBoxItems = ["480p", "720p", "1080p"]
        self.listBox = wx.ListBox(self.panel, wx.ID_ANY, choices=self.listBoxItems, style=wx.LB_MULTIPLE)

        if "selectedListBoxItems" in self.userConfig:
            for item in self.userConfig["selectedListBoxItems"]:
                self.listBox.SetSelection(item)
        else:
            for i in range(len(self.listBoxItems)):
                self.listBox.SetSelection(i)

        comboBoxLabel = wx.StaticText(self.panel, wx.ID_ANY, "Episodes look-ahead")
        self.comboBox = wx.ComboBox(self.panel, wx.ID_ANY, choices=["1", "2", "3"], style=wx.CB_READONLY)
        self.comboBox.SetSelection(self.userConfig["selectedComboBoxItem"] if "selectedComboBoxItem" in self.userConfig else 0)

        self.checkListToggle = wx.CheckBox(self.panel, wx.ID_ANY, "Select/Deselect all")
        self.checkListToggle.SetValue(True)
        self.checkList = wx.CheckListBox(self.panel, wx.ID_ANY, choices=[""]*10)

        downloadButton = wx.Button(self.panel, wx.ID_ANY, "Download my chinese cartoons")

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
        self.Bind(wx.EVT_TEXT, self.OnUsernameChanged, self.listUrlTextInput)
        self.Bind(wx.EVT_DIRPICKER_CHANGED, self.OnDownloadPathChanged, self.dirPicker)
        self.Bind(wx.EVT_LISTBOX, self.OnQualityChanged, self.listBox)
        self.Bind(wx.EVT_COMBOBOX, self.OnEpisodeLookAheadChanged, self.comboBox)
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
        self.checkListItems = []

        unselectedQualities = [self.listBoxItems[i] for i in range(
            len(self.listBoxItems)) if i not in self.listBox.GetSelections()]

        startWorker(self.OnDataFetched, self.FetchDataWorker, wargs=(
            self.listUrlTextInput.GetLineText(0),
            unselectedQualities,
            int(self.comboBox.GetSelection()) + 1,
            self.userConfig["aliases"]))

        # Progress Dialog
        self.progress = 0
        self.keepGoing = True
        progressDialog = wx.ProgressDialog("Fetching data",
                                           "This may take a while...",
                                           parent=self,
                                           style=wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE)

        while self.keepGoing and self.progress < 100:
            wx.MilliSleep(250)
            wx.Yield()
            (self.keepGoing, skip) = progressDialog.Update(self.progress)
        progressDialog.Destroy()

    def FetchDataWorker(self, anilist_username, blacklisted_qualities, look_ahead, aliases):
        for (progress, entry) in scrape.fetch(anilist_username, blacklisted_qualities, look_ahead, aliases):
            self.progress = progress
            self.checkListItems.extend(entry)

            if not self.keepGoing:
                return False
        return True

    def OnDataFetched(self, result):
        if result.get():
            if len(self.checkListItems):
                self.checkList.InsertItems([entry["name"] for entry in self.checkListItems], 0)
                self.SelectAll()
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

    def OnEpisodeLookAheadChanged(self, evt):
        self.userConfig["selectedComboBoxItem"] = self.comboBox.GetSelection()

    def OnQualityChanged(self, evt):
        self.userConfig["selectedListBoxItems"] = self.listBox.GetSelections()

    def OnUsernameChanged(self, evt):
        self.userConfig["anilistUsername"] = self.listUrlTextInput.GetLineText(0)

    def OnDownloadPathChanged(self, evt):
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

class AnidlApp(wx.App):
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)

        # Event bindings
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)

    def OnInit(self):
        anidl = MainWindow(None)
        anidl.FetchData()
        return True

    def BringWindowToFront(self):
        try:
            self.GetTopWindow().Raise()
        except:
            pass

    def OnActivate(self, evt):
        if evt.GetActive():
            self.BringWindowToFront()
        evt.Skip()

    def MacReopenApp(self):
        self.BringWindowToFront()


if __name__ == "__main__":
    app = AnidlApp(False)
    app.MainLoop()
