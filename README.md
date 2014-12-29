# anidl #
## How to use ##
Before you can use the project, you must first install [wxPython](http://www.wxpython.org/). You must also have a valid [anilist API client identifier and secret key](http://anilist-api.readthedocs.org/en/latest/introduction.html#creating-a-client). Once you have that, you need to set the ```ANILIST_CLIENT_ID``` and ```ANILIST_CLIENT_SECRET``` constants to these values in the ```config.py``` file.

## Compiling the project ##
Before you can compile the project, you must first install [py2exe](http://www.py2exe.org/). You must also make sure you have the ```msvcp90.dll``` file __version 9.0.21022.8__ placed in your python DLLs folder.

Then, in a command prompt, enter the following commands:
```
cd /path/to/project/
python setup.py py2exe
```
