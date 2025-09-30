import flet as ft
import subprocess
import json
import os
from pathlib import Path

# Database file path
DB_FILE = "path_cache.json"

def load_path_cache():
    """Load cached paths from JSON file"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"uplugin_paths": [], "save_paths": [], "ue_paths": []}
    return {"uplugin_paths": [], "save_paths": [], "ue_paths": []}

def save_path_cache(cache_data):
    """Save cached paths to JSON file"""
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
    except IOError:
        pass  # Silently fail if can't save

def add_to_cache(cache_data, path_type, path):
    """Add a path to the cache if it's valid and not already present"""
    if path and path not in cache_data[path_type]:
        cache_data[path_type].insert(0, path)  # Add to beginning
        # Keep only last 10 entries
        cache_data[path_type] = cache_data[path_type][:10]
        save_path_cache(cache_data)

def remove_from_cache(cache_data, path_type, path):
    """Remove a path from the cache"""
    if path in cache_data[path_type]:
        cache_data[path_type].remove(path)
        save_path_cache(cache_data)

def main(page: ft.Page):
    page.title = "Unreal Plugin Migration Tool"
    page.window_resizable = True
    page.update()

    # Load cached paths
    path_cache = load_path_cache()

    # Theme selector
    def theme_changed(e):
        page.theme_mode = (
            ft.ThemeMode.LIGHT
            if page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        color_switch.label = "🌙" if page.theme_mode == ft.ThemeMode.DARK else "☀️"
        page.update()

    page.theme_mode = ft.ThemeMode.DARK
    color_switch = ft.Switch(label="🌙", on_change=theme_changed)

    # UPlugin file dropdown and picker
    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            uplugin_dropdown.value = file_path
            add_to_cache(path_cache, "uplugin_paths", file_path)
            uplugin_dropdown.options = [ft.dropdown.Option(path) for path in path_cache["uplugin_paths"]]
        else:
            uplugin_dropdown.value = "No *.uplugin file was selected!"
        uplugin_dropdown.update()

    def uplugin_dropdown_changed(e):
        if uplugin_dropdown.value and uplugin_dropdown.value != "No *.uplugin file was selected!":
            add_to_cache(path_cache, "uplugin_paths", uplugin_dropdown.value)

    def delete_uplugin_cache(e):
        if uplugin_dropdown.value and uplugin_dropdown.value != "No *.uplugin file was selected!":
            remove_from_cache(path_cache, "uplugin_paths", uplugin_dropdown.value)
            uplugin_dropdown.options = [ft.dropdown.Option(path) for path in path_cache["uplugin_paths"]]
            uplugin_dropdown.value = None
            uplugin_dropdown.update()

    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    uplugin_dropdown = ft.Dropdown(
        label="Select .uplugin file",
        options=[ft.dropdown.Option(path) for path in path_cache["uplugin_paths"]],
        on_change=uplugin_dropdown_changed,
        width=400,
        expand=True
    )

    # Save directory dropdown and picker
    def save_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            save_dropdown.value = e.path
            add_to_cache(path_cache, "save_paths", e.path)
            save_dropdown.options = [ft.dropdown.Option(path) for path in path_cache["save_paths"]]
        else:
            save_dropdown.value = "No save directory was selected!"
        save_dropdown.update()

    def save_dropdown_changed(e):
        if save_dropdown.value and save_dropdown.value != "No save directory was selected!":
            add_to_cache(path_cache, "save_paths", save_dropdown.value)

    def delete_save_cache(e):
        if save_dropdown.value and save_dropdown.value != "No save directory was selected!":
            remove_from_cache(path_cache, "save_paths", save_dropdown.value)
            save_dropdown.options = [ft.dropdown.Option(path) for path in path_cache["save_paths"]]
            save_dropdown.value = None
            save_dropdown.update()

    save_directory_dialog = ft.FilePicker(on_result=save_directory_result)
    save_dropdown = ft.Dropdown(
        label="Plugin destination folder",
        options=[ft.dropdown.Option(path) for path in path_cache["save_paths"]],
        on_change=save_dropdown_changed,
        width=400,
        expand=True
    )

    # UE directory dropdown and picker
    def ue_get_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            ue_dropdown.value = e.path
            add_to_cache(path_cache, "ue_paths", e.path)
            ue_dropdown.options = [ft.dropdown.Option(path) for path in path_cache["ue_paths"]]
        else:
            ue_dropdown.value = 'No UE root folder was selected! (Example "C:\\Program Files\\Epic Games\\UE_5.3)"'
        ue_dropdown.update()

    def ue_dropdown_changed(e):
        if ue_dropdown.value and ue_dropdown.value != 'No UE root folder was selected! (Example "C:\\Program Files\\Epic Games\\UE_5.3)"':
            add_to_cache(path_cache, "ue_paths", ue_dropdown.value)

    def delete_ue_cache(e):
        if ue_dropdown.value and ue_dropdown.value != 'No UE root folder was selected! (Example "C:\\Program Files\\Epic Games\\UE_5.3)"':
            remove_from_cache(path_cache, "ue_paths", ue_dropdown.value)
            ue_dropdown.options = [ft.dropdown.Option(path) for path in path_cache["ue_paths"]]
            ue_dropdown.value = None
            ue_dropdown.update()

    get_directory_dialog = ft.FilePicker(on_result=ue_get_directory_result)
    ue_dropdown = ft.Dropdown(
        label="Select UE root folder",
        options=[ft.dropdown.Option(path) for path in path_cache["ue_paths"]],
        on_change=ue_dropdown_changed,
        width=400,
        expand=True
    )

    # Hide all dialogs in overlay
    page.overlay.extend(
        [pick_files_dialog, save_directory_dialog, get_directory_dialog]
    )

    # Plugin migration function
    def plugin_migration():
        engine = rf'"{ue_dropdown.value}"'
        plugin = rf'"{uplugin_dropdown.value}"'
        destination = rf'"{save_dropdown.value}"'
        command = rf"{engine}\Engine\Build\BatchFiles\RunUAT.bat BuildPlugin -plugin={plugin} -package={destination}\Migrated"
        try:
            result = subprocess.run(command, shell=True)
            if result.returncode == 0:
                fine = ft.AlertDialog(
                    title=ft.Text("Plugin migrated succesfully"),
                )
                page.dialog = fine
                fine.open = True
                page.update()
            else:
                wrong = ft.AlertDialog(
                    title=ft.Text("Something went wrong"),
                )
                page.dialog = wrong
                wrong.open = True
                page.update()

        except Exception as e:
            fail = ft.AlertDialog(
                title=ft.Text("An error has ocurred"),
                content=ft.Text(
                    "Please check the command promp to see what the error is"
                ),
            )
            page.dialog = fail
            fail.open = True
            page.update()

    # App layout
    page.add(
        ft.Row(
            [
                color_switch,
            ],
            alignment=ft.MainAxisAlignment.END,
        ),
        ft.Row(
            [
                ft.ElevatedButton(
                    "Browse .uplugin file",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: pick_files_dialog.pick_files(
                        allowed_extensions=["uplugin"]
                    ),
                ),
                uplugin_dropdown,
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    tooltip="Delete selected path from cache",
                    on_click=delete_uplugin_cache,
                ),
            ]
        ),
        ft.Row(
            [
                ft.ElevatedButton(
                    "Browse destination folder",
                    icon=ft.Icons.SAVE,
                    on_click=lambda _: save_directory_dialog.get_directory_path(),
                    disabled=page.web,
                ),
                save_dropdown,
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    tooltip="Delete selected path from cache",
                    on_click=delete_save_cache,
                ),
            ]
        ),
        ft.Row(
            [
                ft.ElevatedButton(
                    "Browse UE root folder",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _: get_directory_dialog.get_directory_path(),
                    disabled=page.web,
                ),
                ue_dropdown,
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    tooltip="Delete selected path from cache",
                    on_click=delete_ue_cache,
                ),
            ]
        ),
        ft.ElevatedButton(
            "Begin Migration",
            icon=ft.Icons.DEW_POINT,
            on_click=lambda _: plugin_migration(),
        ),
    )


ft.app(target=main)
