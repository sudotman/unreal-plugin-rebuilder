import flet as ft
import subprocess
import json
import os
import threading
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
    page.title = "unreal plugin rebuilder"
    page.window_resizable = True
    page.window.width = 800
    page.window.height = 850
    page.window.frameless = True
    page.padding = 20
    page.spacing = 15
    page.update()

    # Load cached paths
    path_cache = load_path_cache()

    # Terminal output components
    terminal_text = ft.Text("Ready to rebuild plugin...", selectable=True, size=12, color=ft.Colors.WHITE)
    terminal_container = ft.Container(
        content=terminal_text,
        bgcolor=ft.Colors.BLACK,
        padding=10,
        border_radius=8,
        height=200,
        width=page.window.width - 40,
    )

    terminal_output = ft.Column(
        [
            ft.Text("Terminal Output:", size=16, weight=ft.FontWeight.BOLD),
            terminal_container,
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    # Progress indicator
    progress_bar = ft.ProgressBar(visible=False, width=400)
    progress_text = ft.Text("", size=12)
    
    # Migration process tracking
    migration_process = None
    
    # Create buttons
    migration_button = ft.ElevatedButton(
        "Begin Rebuild",
        icon=ft.Icons.PLAY_ARROW,
        on_click=lambda _: plugin_migration(),
        width=200,
    )
    
    stop_button = ft.ElevatedButton(
        "Stop Rebuild",
        icon=ft.Icons.STOP,
        on_click=lambda _: stop_migration(),
        width=200,
        visible=False,
    )

    # Function to update terminal output
    def update_terminal_output(text, append=True):
        current_text = f"{terminal_text.value}\n{text}" if append else text
        terminal_text.value = current_text
        terminal_text.update()

    # Function to clear terminal output
    def clear_terminal_output():
        terminal_text.value = ""
        terminal_text.update()
    
    # Function to stop migration
    def stop_migration():
        global migration_process
        if migration_process:
            try:
                # Try terminate first, then kill if needed
                migration_process.terminate()
                # Give it a moment to terminate gracefully
                import time
                time.sleep(0.5)
                if migration_process.poll() is None:  # Process still running
                    migration_process.kill()  # Force kill
                update_terminal_output("Rebuild stopped by user")
                progress_text.value = "Rebuild stopped"
            except Exception as e:
                update_terminal_output(f"Error stopping process: {str(e)}")
            finally:
                migration_process = None
                # Hide progress bar and show migration button
                progress_bar.visible = False
                progress_bar.update()
                if migration_button:
                    migration_button.visible = True
                    migration_button.update()
                if stop_button:
                    stop_button.visible = False
                    stop_button.update()

    # Theme selector
    def theme_changed(e):
        page.theme_mode = (
            ft.ThemeMode.LIGHT
            if page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        page.update()

    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(font_family="Arial")

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

    # Plugin migration function with real-time output
    def plugin_migration():
        # Validate inputs
        if not ue_dropdown.value or str(ue_dropdown.value).startswith("No UE"):
            update_terminal_output("Error: Please select a valid UE root folder", append=False)
            return
        if not uplugin_dropdown.value or str(uplugin_dropdown.value).startswith("No *.uplugin"):
            update_terminal_output("Error: Please select a valid .uplugin file", append=False)
            return
        if not save_dropdown.value or str(save_dropdown.value).startswith("No save"):
            update_terminal_output("Error: Please select a valid destination folder", append=False)
            return

        engine = rf'"{ue_dropdown.value}"'
        plugin = rf'"{uplugin_dropdown.value}"'
        destination = rf'"{save_dropdown.value}"'
        command = rf"{engine}\Engine\Build\BatchFiles\RunUAT.bat BuildPlugin -plugin={plugin} -package={destination}\Migrated"

        # Clear terminal and show progress
        clear_terminal_output()
        update_terminal_output("Starting plugin rebuild...")
        update_terminal_output(f"Command: {command}")
        update_terminal_output("=" * 50)

        # Show progress bar and update buttons
        progress_bar.visible = True
        progress_text.value = "Rebuilding plugin..."
        progress_bar.update()
        progress_text.update()
        
        # Hide migration button and show stop button
        if migration_button:
            migration_button.visible = False
            migration_button.update()
        if stop_button:
            stop_button.visible = True
            stop_button.update()

        def run_migration():
            global migration_process
            try:
                migration_process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                )

                for line in iter(migration_process.stdout.readline, ''):
                    if line.strip():
                        update_terminal_output(line.strip())

                migration_process.wait()

                update_terminal_output("=" * 50)
                if migration_process.returncode == 0:
                    update_terminal_output("Success: Plugin rebuilt successfully!")
                    progress_text.value = "Rebuild completed successfully"
                else:
                    update_terminal_output(f"Error: Rebuild failed with return code: {migration_process.returncode}")
                    progress_text.value = "Rebuild failed"
            except Exception as e:
                update_terminal_output("=" * 50)
                update_terminal_output(f"Error occurred: {str(e)}")
                progress_text.value = "Error occurred"
            finally:
                migration_process = None
                progress_bar.visible = False
                progress_bar.update()
                progress_text.update()
                # Show migration button and hide stop button
                if migration_button:
                    migration_button.visible = True
                    migration_button.update()
                if stop_button:
                    stop_button.visible = False
                    stop_button.update()

        # Run migration in a separate thread to keep UI responsive
        t = threading.Thread(target=run_migration, daemon=True)
        t.start()

    # Helper to create input sections with consistent styling
    def create_input_section(title, button_text, button_icon, dropdown, delete_func, browse_func):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.PRIMARY),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                button_text,
                                icon=button_icon,
                                on_click=browse_func,
                                disabled=page.web,
                            ),
                            ft.Container(dropdown, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Delete selected path from cache",
                                on_click=delete_func,
                            ),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=5,
            ),
            padding=15,
            border_radius=0,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.PRIMARY_CONTAINER),
            border=ft.border.all(0, ft.Colors.OUTLINE),
        )

    # Build input sections
    uplugin_section = create_input_section(
        "Plugin File (.uplugin)",
        "Browse",
        ft.Icons.UPLOAD_FILE,
        uplugin_dropdown,
        delete_uplugin_cache,
        lambda _: pick_files_dialog.pick_files(allowed_extensions=["uplugin"]),
    )

    save_section = create_input_section(
        "Destination Folder",
        "Browse",
        ft.Icons.SAVE,
        save_dropdown,
        delete_save_cache,
        lambda _: save_directory_dialog.get_directory_path(),
    )

    ue_section = create_input_section(
        "Unreal Engine Root",
        "Browse",
        ft.Icons.FOLDER_OPEN,
        ue_dropdown,
        delete_ue_cache,
        lambda _: get_directory_dialog.get_directory_path(),
    )

    # App layout
    page.add(
        # Header
        ft.WindowDragArea(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Container(expand=True),  # Add an expandable container to center the content
                        ft.GestureDetector(
                            content=ft.Text(
                                "unreal plugin rebuilder",
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                font_family="Arial",
                                color=ft.Colors.PRIMARY,
                            ),
                            on_tap=theme_changed,
                        ),
                        ft.Container(expand=True),  # Add an expandable container to center the content
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            tooltip="Close",
                            on_click=lambda _: page.window.close(),
                            style=ft.ButtonStyle(
                                color=ft.Colors.ON_ERROR_CONTAINER,
                            ),
                        ),
                    ]
                ),
                padding=ft.Padding(0, 0, 0, 20),
            ),
        ),

        # Inputs
        ft.Container(
            content=ft.Column(
                [
                    uplugin_section,
                    save_section,
                    ue_section,
                ],
                spacing=15,
            ),
            padding=ft.Padding(0, 0, 0, 20),
        ),

        # Action + progress
        ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=migration_button,
                                alignment=ft.alignment.center,
                            ),
                            ft.Container(
                                content=stop_button,
                                alignment=ft.alignment.center,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    ft.Container(
                        content=ft.Column(
                            [progress_bar, progress_text],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=10,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.Padding(0, 0, 0, 20),
        ),

        # Terminal output
        ft.Container(
            content=terminal_output,
            padding=ft.Padding(0, 0, 0, 0),
        ),
    )


ft.app(target=main)
