# unreal plugin rebuilder
this is a simple python application that provides a GUI for rebuilding/migrating Unreal Engine plugins using the Unreal Automation Tool (UAT). simply a wrapper - nothing fancy. extends @mickexd's not maintained version. 

![Unreal Plugin Rebuilder Demo](https://raw.githubusercontent.com/sudotman/sudotman/refs/heads/main/demos/unrealPlugin/demo.png)


## features over a standard CLI call
- pretty UI ;) [frame-less and click the 'unreal plugin rebuilder' text to switch theme]
- caches your previously given paths for engine, plugin and the destination folder for quicker simulatenous builds.
- a cleaner interface for when your favorite terminal isn't there and/or you're configuring/building on the fly
- allows your designer friends to rebuild! :D

## usage
1. download a release from https://github.com/sudotman/unreal-plugin-rebuilder/releases and open the application 
2. select the `.uplugin` file you want to rebuild, select the plugin destination folder and your UE installation's root [e.g. C:\Program Files\Epic Games\UE_5.5].
3. click on the "rebuild" button to rebuild.

## building from py
build the application using PyInstaller:

1. install pyinstaller:
   ```
   pip install pyinstaller
   ```

2. run the following command to create a standalone executable:
   ```
   pyinstaller --onefile --windowed --name="UnrealPluginRebuilder" UnrealPluginMigrationTool.py
   ```

this will generate a `dist` folder containing the `UnrealPluginRebuilder` executable, which you can run independently of Python.

## contribution
pr anything relevant and I shall review!