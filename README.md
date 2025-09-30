# unreal plugin rebuilder
this is a simple python application that provides a GUI for rebuilding/migrating Unreal Engine plugins using the Unreal Automation Tool (UAT). simply a wrapper - nothing fancy. extends @mickexd's not maintained version. 

## features over a standard CLI call

- caches your previously given paths for engine, plugin and the destination folder for quicker simulatenous operations.
- a cleaner interface for when your favorite terminal isn't there and/or you're configuring/building on the fly

## usage
1. download a release from https://github.com/sudotman/unreal-plugin-rebuilder/releases and open the application 
2. select the `.uplugin` file you want to rebuild, select the plugin destination folder and your UE installation's root [e.g. C:\Program Files\Epic Games\UE_5.5].
3. click on the "rebuild" button to rebuild.

## contribution
pull anything relevant and I shall review!