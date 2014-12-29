from distutils.core import setup
import py2exe

includes = []
excludes = ["_gtkagg", "_tkagg", "bsddb", "curses", "email", "pywin.debugger",
            "pywin.debugger.dbgcon", "pywin.dialogs", "tcl", "Tkconstants", "Tkinter"]
packages = []
dll_excludes = ["libgdk-win32-2.0-0.dll", "libgobject-2.0-0.dll", "tcl84.dll", "tk84.dll", "w9xpopen.exe"]

for dbmodule in ["dbhash", "gdbm", "dbm", "dumbdbm"]:
    try:
        __import__(dbmodule)
    except ImportError:
        pass
    else:
         # If we found the module, ensure it"s copied to the build directory.
        packages.append(dbmodule)

setup(windows=["anidl.py"], zipfile = None,
      options = {"py2exe": {"compressed": 2,
                            "optimize": 2,
                            "includes": includes,
                            "excludes": excludes,
                            "packages": packages,
                            "dll_excludes": dll_excludes,
                            "bundle_files": 1,
                            "dist_dir": "dist",
                            "xref": False,
                            "skip_archive": False,
                            "ascii": False,
                            "custom_boot_script": ""}})
