import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

try:
    from pathlib import Path

    USE_PATHLIB = True
except ImportError:

    USE_PATHLIB = False

import atexit
import hashlib
import json
import locale
import random
import string
import subprocess

import folder_paths  # type: ignore
import ftfy  # type: ignore
import psutil  # type: ignore
import torch  # type: ignore
import torchvision.transforms as T  # type: ignore
from PyQt6 import QtCore, QtGui, QtWidgets  # type: ignore
from PyQt6.QtWidgets import QApplication, QMainWindow  # type: ignore

# Standardized Unicode mapping using escape sequences
UNICODE_CHR = {
    "error": "\u274c",  # ❌ Red Cross
    "warning": "\u26a0",  # ⚠️ Warning
    "success": "\u2705",  # Checkmark
    "info": "\U0001F535",  # 🔵 Blue Circle
    "cleanup": "\U0001f9f9",  # 🧹 Broom
    "update": "\U0001f504",  # 🔄 Refresh
    "image": "\U0001F5BC",  # 🖼️ Framed Picture
    "process": "\U0001f680",  # 🚀 Rocket
    "save": "\U0001f4be",  # 💾 Save
    "clipboard": "\U0001f4cb",  # 📋 Clipboard
    "pin": "\U0001f4cc",  # 📌 Push Pin
    "left_arrow": "\u276e",  # ❮ left arrow
    "right_arrow": "\u276f",  # ❯ right arrow
    "nbs": "\x0a",  # non-breaking space
}


def log_message(message, level="info"):
    """Print messages with color coding and proper Unicode handling."""
    colors = {
        "error": "\033[91m",  # 🔴 Red
        "warning": "\033[93m",  # 🟡 Yellow
        "success": "\033[92m",  # 🟢 Green
        "process": "\033[95m",  # 🟣 pink
        "info": "\033[94m",  # 🔵 Blue
        "reset": "\033[0m",  # Reset color
    }

    level_key = level.lower()

    icon = ftfy.fix_text(UNICODE_CHR.get(level_key, ""))
    safe_message = f"{colors.get(level_key, colors['reset'])}[{icon} {level.upper()}]: {ftfy.fix_text(message)}{colors['reset']}"

    try:
        print(
            safe_message.encode(sys.stdout.encoding, errors="replace").decode(
                sys.stdout.encoding
            )
        )

    except:
        # Fallback if Unicode fails (removes non-ASCII characters)
        print(f"[{level.upper()}]: {message.encode(errors='replace').decode()}")


def safe_path(*args):
    """Create a cross-platform path as a string, using pathlib if available."""
    if USE_PATHLIB:
        return str(Path(*map(str, args)).resolve())
    return os.path.normpath(os.path.join(*args))


def ensure_directory_exists(path):
    """Ensure a directory exists, using pathlib if available."""
    if USE_PATHLIB:
        Path(path).mkdir(parents=True, exist_ok=True)
    else:
        os.makedirs(path, exist_ok=True)


def safe_remove(file_path):
    """Safely remove a file using pathlib if available, otherwise use os.remove()."""
    if USE_PATHLIB:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
    else:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)


def safe_exists(file_path):
    """Check if a file exists using pathlib if available, otherwise use os.path.exists()."""
    if USE_PATHLIB:
        return Path(file_path).exists() and Path(file_path).is_file()
    return os.path.exists(file_path) and os.path.isfile(file_path)


def safe_is_dir(directory_path):
    """Check if a directory exists using pathlib if available, otherwise use os.path.isdir()."""
    if USE_PATHLIB:
        return Path(directory_path).is_dir()
    return os.path.isdir(directory_path)


def safe_read_file(file_path, default_data=""):
    """Safely read a file's contents, returning default_data if the file does not exist."""
    if not safe_exists(file_path):
        return default_data

    try:
        if USE_PATHLIB:
            return Path(file_path).read_text(encoding="utf-8")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log_message(f"Error reading {file_path}: {e}", "warning")
        return default_data


def safe_write_file(file_path, content):
    """Safely write content to a file using pathlib if available, otherwise use open()."""
    try:
        if USE_PATHLIB:
            Path(file_path).write_text(content, encoding="utf-8")
        else:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
    except Exception as e:
        log_message(f"Error writing to {file_path}: {e}", "error")


def safe_append_file(file_path, content):
    """Safely append content to a file, creating it if it does not exist."""
    try:
        if USE_PATHLIB:
            with Path(file_path).open("a", encoding="utf-8") as f:
                f.write(content + "\n")
        else:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(content + "\n")
    except Exception as e:
        log_message(f"Error appending to {file_path}: {e}", "error")


def safe_rename(old_path, new_path):
    """Safely rename a file, checking if it exists first."""
    if safe_exists(old_path):
        try:
            if USE_PATHLIB:
                Path(old_path).rename(new_path)
            else:
                os.rename(old_path, new_path)
        except Exception as e:
            log_message(f"Error renaming {old_path} to {new_path}: {e}", "error")


def safe_list_dir(directory_path):
    """Safely list the contents of a directory, returning an empty list if the directory does not exist."""
    if not safe_is_dir(directory_path):
        return []
    return (
        os.listdir(directory_path)
        if not USE_PATHLIB
        else [str(p) for p in Path(directory_path).iterdir()]
    )


def get_comfyui_temp_folder():
    """Get ComfyUI's temp folder path using safe_path() and ensure_directory_exists()."""
    comfy_temp_dir = safe_path(folder_paths.get_temp_directory())  # Base temp directory
    ensure_directory_exists(comfy_temp_dir)
    return comfy_temp_dir


def get_float_preview_temp_folder():
    """Get the Float Preview temp folder inside ComfyUI's temp directory."""
    float_preview_temp_dir = safe_path(
        get_comfyui_temp_folder(), "float_preview"
    )  # Uses base temp dir
    ensure_directory_exists(float_preview_temp_dir)
    return float_preview_temp_dir


def get_mohseni_kit_dir():
    """Get Mohseni Kit custom node folder path inside ComfyUI."""
    mohseni_custom_nodes_dir = safe_path(
        folder_paths.get_folder_paths("custom_nodes")[0], "ComfyUI-Mohseni-Kit"
    )
    ensure_directory_exists(mohseni_custom_nodes_dir)
    return mohseni_custom_nodes_dir


def get_script_path():
    """Return the absolute path of the current script using safe_path()."""
    return safe_path(__file__)


def safe_get_name(file_path):
    """Return the name of the current script file using pathlib if available, otherwise fallback to os.path."""
    if USE_PATHLIB:
        return Path(file_path).name
    return os.path.basename(file_path)


def get_window_icon():
    """Set a custom icon for the Float Preview window."""
    return safe_path(get_mohseni_kit_dir(), "assets", "mohseni_float_preview.ico")


def calculate_image_hash(image_path):
    """Generate a quick hash for the first image file."""
    if not safe_exists(image_path):
        return None

    try:
        with open(image_path, "rb") as f:
            return hashlib.sha256(f.read(1024)).hexdigest()
    except Exception as e:
        log_message(f"Error reading {image_path}: {e}", "warning")
        return None


def generate_image_hash(image):
    """Generate a SHA256 hash for an image tensor."""
    try:
        image_bytes = image.cpu().numpy().tobytes()
        return hashlib.sha256(image_bytes).hexdigest()
    except Exception:
        return None


# Precompute the characters string
CHARACTERS = string.ascii_letters + string.digits  # Letters (a-z, A-Z) and digits (0-9)
# Create a SystemRandom instance
_sysrand = random.SystemRandom()


def generate_random_string(length=6):
    """Generate a random string using the SystemRandom class."""
    return "".join(_sysrand.choices(CHARACTERS, k=length))


# --- Globals ---
FLOAT_PREVIEW_TEMP_DIR = get_float_preview_temp_folder()
MOHSENI_KIT_DIR = get_mohseni_kit_dir()
JSON_FILE_PATH = safe_path(FLOAT_PREVIEW_TEMP_DIR, "image_paths.json")
SETTINGS_FILE_PATH = safe_path(MOHSENI_KIT_DIR, "float_preview_settings.json")


# --- Float Window Implementation ---
class FloatWindow(QMainWindow):
    """Floating preview window for displaying generated images."""

    def __init__(self, temp_image_paths):
        super().__init__()
        self.temp_image_paths = temp_image_paths
        self.current_index = 0
        self.pixmap_cache = {}
        self.scaled_image_cache = {}
        self.current_label_size = None
        self.max_cache_size = 50
        safe_space = ftfy.fix_text(UNICODE_CHR.get("nsb", " ") * 2)

        self.setWindowTitle("Float Preview - Mohseni Kit")

        icon_path = get_window_icon()
        if safe_exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            log_message("Window icon file not found. Skipping icon setting.", "warning")

        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        self.label.setMinimumSize(100, 100)
        self.setCentralWidget(self.label)

        self.load_settings()
        self.resize(max(300, self.width()), max(300, self.height()))

        self.indicator_label = QtWidgets.QLabel(self)
        self.indicator_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.indicator_label.setStyleSheet(
            "background-color: rgba(0, 0, 0, 128); color: white; font-size: 16px; padding: 3px; border-radius: 5px;"
        )
        self.indicator_label.setFixedSize(100, 30)
        self.update_indicator_position()

        # Prevent reopening on close
        self.closing = False

        # Enable dragging support
        self.dragging = False
        self.offset = None

        # Load previous "Always on Top" state
        self.update_always_on_top()
        self.check_for_existing_images()

        self.context_menu = QtWidgets.QMenu(self)
        self.always_on_top_action = self.context_menu.addAction(
            f"{ftfy.fix_text(UNICODE_CHR.get('pin', ''))}{safe_space}Always on Top{safe_space}(Ctrl+T)"
        )
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.setChecked(self.always_on_top)
        self.always_on_top_action.triggered.connect(self.toggle_always_on_top)

        self.context_menu.addSeparator()

        self.copy_image_action = self.context_menu.addAction(
            f"{ftfy.fix_text(UNICODE_CHR.get('clipboard', ''))}{safe_space}Copy to Clipboard{safe_space}(Ctrl+C)"
        )
        self.copy_image_action.triggered.connect(self.copy_to_clipboard)

        self.context_menu.addSeparator()

        self.save_image_action = self.context_menu.addAction(
            f"{ftfy.fix_text(UNICODE_CHR.get('save', ''))}{safe_space}Save Image{safe_space}(Ctrl+S)"
        )
        self.save_image_action.triggered.connect(self.save_image)

        self.context_menu.addSeparator()

        self.exit_action = self.context_menu.addAction(
            f"{ftfy.fix_text(UNICODE_CHR.get('error', ''))}{safe_space}Close Window{safe_space}(Esc)"
        )
        self.exit_action.triggered.connect(self.close)

        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.check_for_updates)
        self.timer.start(200)

        self.update_image()

    def load_settings(self):
        """Load the window's persistent settings using safe_read_file()."""
        settings_data = safe_read_file(SETTINGS_FILE_PATH, default_data="{}")

        try:
            settings = json.loads(settings_data)  # Ensure settings is a dictionary
            self.always_on_top = settings.get("always_on_top", False)
            self.resize(settings.get("width", 600), settings.get("height", 600))
            self.move(settings.get("x", 100), settings.get("y", 100))
        except json.JSONDecodeError:
            log_message(
                "Failed to load settings file. Using default settings.", "warning"
            )
            self.always_on_top = False
            self.resize(600, 600)
            self.move(100, 100)

    def save_settings(self):
        """Save the window's settings persistently using safe_write_file()."""
        first_image_hash = (
            calculate_image_hash(self.temp_image_paths[0])
            if self.temp_image_paths
            else None
        )

        settings = {
            "always_on_top": self.always_on_top,
            "x": self.x(),
            "y": self.y(),
            "width": self.width(),
            "height": self.height(),
            "first_image_hash": first_image_hash,
        }

        try:
            safe_write_file(SETTINGS_FILE_PATH, json.dumps(settings, indent=2))
        except Exception as e:
            pass

    def check_for_existing_images(self):
        """Load previous images if they exist, match the stored hash, and no new images were created."""
        stored_hash = None
        image_existence = True

        # Load stored hash from settings
        settings_data = safe_read_file(SETTINGS_FILE_PATH, default_data="{}")
        try:
            settings = json.loads(settings_data)
            stored_hash = settings.get("first_image_hash")
        except json.JSONDecodeError:
            log_message(
                "Failed to load settings.json. Continuing without hash check.",
                "warning",
            )

        # Load previous image paths
        temp_image_paths_data = safe_read_file(JSON_FILE_PATH, default_data="[]")
        try:
            temp_image_paths = json.loads(temp_image_paths_data)
        except json.JSONDecodeError:
            log_message("Failed to parse image_paths.json. Resetting paths.", "warning")
            return

        # Ensure all image paths exist
        if temp_image_paths:
            for temp_image in temp_image_paths:
                if not safe_exists(temp_image):
                    image_existence = False
                    break
                try:
                    pixmap = QtGui.QPixmap(temp_image)
                    if pixmap.isNull():
                        image_existence = False
                        break
                except Exception:
                    image_existence = False
                    break

            # Compare stored hash with first image hash if available
            if image_existence and stored_hash:
                current_hash = calculate_image_hash(temp_image_paths[0])
                if current_hash and current_hash != stored_hash:
                    return  # If hash mismatch, do nothing (new image detected)

            # If images exist and match, use them
            if image_existence:
                self.temp_image_paths = temp_image_paths
                self.current_index = 0

    def clear_cache(self):
        """Clear the image cache to free up memory."""
        self.pixmap_cache.clear()
        self.scaled_image_cache.clear()

    def load_pixmap(self, path):
        """Load and cache the QPixmap for a given image path."""
        if path in self.pixmap_cache:
            return self.pixmap_cache[path]

        pixmap = QtGui.QPixmap(path)
        if pixmap.isNull():
            log_message(f"Failed to load image: {path}", "warning")
            return None

        if len(self.pixmap_cache) >= self.max_cache_size:
            self.pixmap_cache.popitem(last=False)

        self.pixmap_cache[path] = pixmap
        return pixmap

    def check_for_updates(self):
        """Check for new image paths and reload if necessary."""
        # Ensure JSON file exists
        if not safe_exists(JSON_FILE_PATH):
            return

        # Load image paths safely
        image_paths_data = safe_read_file(JSON_FILE_PATH, default_data="[]")

        try:
            new_image_paths = json.loads(image_paths_data)
        except json.JSONDecodeError:
            log_message("Invalid JSON content", "error")
            return

        # Only update if paths have changed
        if new_image_paths != self.temp_image_paths:
            self.scaled_image_cache.clear()
            self.clear_cache()
            self.temp_image_paths = new_image_paths
            self.current_index = 0
            self.update_image()

    def update_image(self):
        """Load and display the current image, scaling it based on window size."""
        if self.closing or not self.temp_image_paths:
            return

        self.current_index %= len(self.temp_image_paths)

        path = self.temp_image_paths[self.current_index]

        if (
            path in self.scaled_image_cache
            and self.current_label_size == self.label.size()
        ):
            scaled_pixmap = self.scaled_image_cache[path]
        else:
            pixmap = QtGui.QPixmap(path)
            if pixmap.isNull():
                log_message(f"Failed to load image: {path}", "warning")
                return

            # Cache the newly scaled image
            scaled_pixmap = pixmap.scaled(
                self.width(),
                self.height(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )

            self.scaled_image_cache[path] = scaled_pixmap
            self.current_label_size = self.label.size()

        self.label.setPixmap(scaled_pixmap)
        self.label.adjustSize()

        # Hide or update the navigation indicator
        if len(self.temp_image_paths) > 1:
            self.indicator_label.show()
            self.indicator_label.setText(
                f"{ftfy.fix_text(UNICODE_CHR.get('left_arrow', ''))}  {self.current_index + 1} / {len(self.temp_image_paths)}  {ftfy.fix_text(UNICODE_CHR.get('right_arrow', ''))}"
            )
            self.update_indicator_position()
        else:
            self.indicator_label.hide()

    def update_indicator_position(self):
        """Ensure the indicator stays centered when the window is resized."""
        if hasattr(self, "indicator_label"):
            text_length = len(self.indicator_label.text())
            new_width = max(100, text_length * 10)
            self.indicator_label.setFixedSize(new_width, 30)
            self.indicator_label.move(self.width() // 2 - new_width // 2, 10)
            self.indicator_label.raise_()

    def show_context_menu(self, position):
        """Show the right-click menu at the given position."""
        self.always_on_top_action.setChecked(self.always_on_top)
        self.context_menu.popup(self.mapToGlobal(position))

    def toggle_always_on_top(self):
        """Toggle the 'Always on Top' mode."""
        self.always_on_top = not self.always_on_top
        self.always_on_top_action.setChecked(self.always_on_top)
        self.update_always_on_top()
        self.save_always_on_top_state()

    def update_always_on_top(self):
        """Update the window's 'Always on Top' state."""
        self.setWindowFlag(
            QtCore.Qt.WindowType.WindowStaysOnTopHint, self.always_on_top
        )
        self.show()  # Refresh window state

    def save_always_on_top_state(self):
        """Save the 'Always on Top' state to the settings file using safe_read_file() and safe_write_file()."""
        # Load existing settings safely
        settings_data = safe_read_file(SETTINGS_FILE_PATH, default_data="{}")
        try:
            settings = json.loads(settings_data)
        except json.JSONDecodeError:
            log_message("Failed to read settings.json. Creating a new one.", "warning")
            settings = {}

        # Update 'always_on_top' value
        settings["always_on_top"] = self.always_on_top

        # Save updated settings
        try:
            safe_write_file(SETTINGS_FILE_PATH, json.dumps(settings, indent=2))
            log_message(
                f"'Always on Top' set to {ftfy.fix_text(UNICODE_CHR.get('left_arrow', ''))} {str(self.always_on_top)} {ftfy.fix_text(UNICODE_CHR.get('right_arrow', ''))} and saved successfully.",
                "success",
            )
        except Exception as e:
            log_message(f"Failed to save 'Always on Top' state: {e}", "error")

    def closeEvent(self, event):
        """Ensure the window fully closes on the first attempt."""
        self.closing = True
        self.save_settings()

        if hasattr(self, "timer"):
            self.timer.stop()
        if hasattr(self, "update_check_timer"):
            self.update_check_timer.stop()

        self.clear_cache()

        log_message("Float window closed. Settings saved.", "info")

        super().closeEvent(event)

    def resizeEvent(self, event):
        """Ensure the indicator stays centered when the window is resized."""
        self.scaled_image_cache.clear()
        self.label.adjustSize()
        self.update_image()
        self.update_indicator_position()
        super().resizeEvent(event)

    # --- 🖱️ Dragging Support ---
    def mousePressEvent(self, event):
        """Start dragging when the mouse is pressed."""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        """Move the window while dragging."""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        """Stop dragging when the mouse is released."""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.dragging = False

    # --- ⌨️ Keyboard Shortcuts ---
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()  # Close window on ESC
        elif (
            event.key() == QtCore.Qt.Key.Key_S
            and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
        ):
            self.save_image()  # Save on CTRL+S
        elif (
            event.key() == QtCore.Qt.Key.Key_C
            and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
        ):
            self.copy_to_clipboard()  # Copy on CTRL+C
        elif (
            event.key() == QtCore.Qt.Key.Key_T
            and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
        ):
            self.toggle_always_on_top()  # Toggle Always on Top with CTRL+T
        elif (
            event.key() == QtCore.Qt.Key.Key_Right
            or event.key() == QtCore.Qt.Key.Key_Down
        ):
            self.current_index = (self.current_index + 1) % len(self.temp_image_paths)
            self.update_image()
        elif (
            event.key() == QtCore.Qt.Key.Key_Left or event.key() == QtCore.Qt.Key.Key_Up
        ):
            self.current_index = (self.current_index - 1) % len(self.temp_image_paths)
            self.update_image()

    def save_image(self):
        """Save the currently displayed image."""
        if 0 <= self.current_index < len(self.temp_image_paths):
            current_image_path = self.temp_image_paths[self.current_index]
            save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Image",
                "",
                "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
            )

            if not save_path:
                log_message("Save operation canceled.", "info")
                return

            if save_path:
                QtGui.QPixmap(current_image_path).save(save_path)
                log_message(f"Image saved to {save_path}", "success")

            return

    def copy_to_clipboard(self):
        """Copy the image to the clipboard."""
        if 0 <= self.current_index < len(self.temp_image_paths):
            current_image_path = self.temp_image_paths[self.current_index]
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setPixmap(QtGui.QPixmap(current_image_path))
            log_message("Image copied to clipboard.", "success")
            return


def get_qt_app():
    """Ensure a single QApplication instance is created."""
    app = QApplication.instance()
    if app is None:
        QtWidgets.QApplication.setHighDpiScaleFactorRoundingPolicy(
            QtCore.Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(sys.argv)
        app.setApplicationName("Float Preview")

    return app


def open_float_window(temp_image_paths):
    """Start or update the Float Preview window as a separate process."""

    # Ensure input is valid
    if not isinstance(temp_image_paths, list):
        log_message("Invalid image paths provided. Expected a list.", "error")
        return

    # Write image paths safely to JSON
    try:
        safe_write_file(
            JSON_FILE_PATH, json.dumps(temp_image_paths, indent=2, ensure_ascii=False)
        )
    except Exception as e:
        log_message(f"Failed to write image paths to JSON: {e}", "error")
        return

    # Check if Float Window is already running
    if is_window_running():
        log_message("Updating existing float window...", "info")
    else:
        log_message("Starting new float window process...", "process")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["LC_ALL"] = (
            "C.UTF-8" if "UTF-8" in locale.getdefaultlocale() else "en_US.UTF-8"
        )

        try:
            script_path = get_script_path()
            python_exec = sys.executable

            subprocess.Popen(
                [python_exec, script_path, "float_window"],
                stdout=sys.stdout,
                stderr=sys.stderr,
                env=env,
                start_new_session=True,
            )

        except Exception as e:
            log_message(f"Failed to start float window: {e}", "error")


def run_float_window():
    """Ensures a single QApplication instance and launches the float window."""
    try:
        log_message("Float Window subprocess started...", "process")

        app = get_qt_app()

        # Ensure JSON file exists
        if not safe_exists(JSON_FILE_PATH):
            log_message("No JSON file found for image paths.", "error")
            return

        # Load image paths safely
        image_paths_data = safe_read_file(JSON_FILE_PATH, default_data="[]")

        try:
            temp_image_paths = json.loads(image_paths_data)
        except json.JSONDecodeError:
            log_message("Invalid JSON content in float_window_update.json.", "error")
            return

        # Close existing FloatWindow instances
        for widget in app.allWidgets():
            if isinstance(widget, FloatWindow):
                log_message("Closing existing FloatWindow...", "warning")
                widget.close()

        window = FloatWindow(temp_image_paths)
        window.show()
        app.exec()
    except Exception as e:
        log_message(f"ERROR in running float window {e}", "error")


def is_window_running():
    """Check if the Float Preview process is already running."""
    script_name = safe_get_name(get_script_path())
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"]) if proc.info["cmdline"] else ""
            if script_name in cmdline or "float_window" in cmdline:
                return True
        except (psutil.NoSuchProcess, TypeError):
            continue
    return False


def cleanup_json_file():
    """Safely delete JSON_FILE_PATH on exit using safe_remove()."""
    if safe_exists(JSON_FILE_PATH):
        try:
            safe_remove(JSON_FILE_PATH)
        except Exception as e:
            log_message(f"Failed to delete {JSON_FILE_PATH}: {e}", "warning")


# --- Preview Logic ---
def render_float_preview(image, always_show_preview=False):
    if image is None:
        log_message("Received None as input image. Skipping execution.", "warning")
        return

    try:
        if safe_is_dir(FLOAT_PREVIEW_TEMP_DIR):
            for filename in safe_list_dir(FLOAT_PREVIEW_TEMP_DIR):
                if filename.startswith("temp_float_preview_"):
                    file_path = safe_path(FLOAT_PREVIEW_TEMP_DIR, filename)
                    safe_remove(file_path)
    except Exception as e:
        log_message(f"Cleanup failed: {e}", "error")

    if image.ndim == 4:
        batch_size = image.shape[0]
        images = [image[i] for i in range(batch_size)]
    else:
        images = [image]

    temp_paths = []
    num_images = len(images)
    max_digits = max(len(str(num_images)), 2)

    transform = T.ToPILImage()
    for i, img in enumerate(images):
        if img.ndim != 3 or img.shape[2] != 3:
            raise ValueError(
                f"Invalid input shape {img.shape}. Expected (H, W, 3) image tensor."
            )

        img = img.permute(2, 0, 1).clamp(0, 1)
        pil_img = transform(img)

        formatted_index = str(i + 1).zfill(max_digits)

        temp_path = safe_path(
            FLOAT_PREVIEW_TEMP_DIR,
            f"temp_float_preview_{formatted_index}_{generate_random_string(6)}.png",
        )

        pil_img.save(temp_path, format="PNG", optimize=False, compress_level=1)
        temp_paths.append(temp_path)

    open_float_window(temp_paths)


def fingerprint_float_preview(image, always_show_preview=False):
    if always_show_preview or image is None:
        return generate_random_string(12)

    try:
        if image.ndim == 4:
            image = image[0]

        max_size = min(768, max(image.shape[0], image.shape[1]) // 4)

        if max(image.shape[0], image.shape[1]) > max_size:
            scale_transform = T.Resize(max_size, antialias=True)
            image = scale_transform(image.permute(2, 0, 1)).permute(1, 2, 0)

        return generate_image_hash(image)
    except Exception:
        pass

    return generate_random_string(12)


# --- Custom Node Definition ---
try:
    from comfy_api.latest import io  # type: ignore

    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False


if V3_AVAILABLE:

    class FloatPreviewNode(io.ComfyNode):
        @classmethod
        def define_schema(cls):
            return io.Schema(
                node_id="FloatPreview",
                display_name="🖼️ Float Preview",
                category="⚡ Mohseni Kit/Image",
                is_output_node=True,
                inputs=[
                    io.Image.Input("Image"),
                    io.Boolean.Input(
                        "Always_Show_Preview", default=False, optional=True
                    ),
                ],
                outputs=[],
            )

        @classmethod
        def fingerprint_inputs(cls, Image, Always_Show_Preview=False):
            return fingerprint_float_preview(Image, Always_Show_Preview)

        @classmethod
        def execute(cls, Image: torch.Tensor, Always_Show_Preview: bool = False):
            render_float_preview(Image, Always_Show_Preview)
            return io.NodeOutput()

else:

    class FloatPreviewNode:
        @classmethod
        def INPUT_TYPES(cls):
            return {
                "required": {
                    "Image": ("IMAGE",),
                },
                "optional": {
                    "Always_Show_Preview": (
                        "BOOLEAN",
                        {"default": False},
                    ),
                },
            }

        RETURN_TYPES = ()
        FUNCTION = "execute"
        OUTPUT_NODE = True
        CATEGORY = "⚡ Mohseni Kit/Image"

        def execute(self, Image: torch.Tensor, Always_Show_Preview: bool = False):
            render_float_preview(Image, Always_Show_Preview)
            return ()

        @classmethod
        def IS_CHANGED(cls, Image, Always_Show_Preview=False):
            return fingerprint_float_preview(Image, Always_Show_Preview)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "float_window":
        run_float_window()
    else:
        log_message("Running Float Preview normally.", "success")

# --- Register Custom Node ---
if V3_AVAILABLE:
    FP_CLASS_MAPPINGS = {}
    FP_DISPLAY_NAME_MAPPINGS = {}
else:
    FP_CLASS_MAPPINGS = {"FloatPreview": FloatPreviewNode}
    FP_DISPLAY_NAME_MAPPINGS = {"FloatPreview": "🖼️ Float Preview"}

# --- Cleanup ---
atexit.register(cleanup_json_file)
