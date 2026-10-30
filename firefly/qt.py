import os

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QGuiApplication,
    QPainter,
    QPixmap,
)

import firefly
from firefly.log import log

app_dir = os.getcwd()


class AppSettings:
    def __init__(self):
        self.data = {"name": "qtapp"}

    def get(self, key, default=False):
        return self.data.get(key, default)

    def update(self, data):
        return self.data.update(data)

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        if key == "title":
            return self.get(key, self.data["name"])
        return self.data[key]


app_settings = AppSettings()


def get_app_state(path):
    return QSettings(path, QSettings.Format.IniFormat)


#
# Skin
#

app_skin = ""
skin_path = os.path.join(app_dir, "skin.css")
if os.path.exists(skin_path):
    try:
        with open(skin_path) as f:
            app_skin = f.read()
    except Exception:
        log.error("Unable to read stylesheet")


def load_fonts():
    """Register bundled fonts. Requires a running QApplication."""
    fonts_dir = os.path.join(app_dir, "fonts")
    if not os.path.isdir(fonts_dir):
        return
    for fname in sorted(os.listdir(fonts_dir)):
        if not fname.endswith(".ttf"):
            continue
        if QFontDatabase.addApplicationFont(os.path.join(fonts_dir, fname)) == -1:
            log.warning(f"Unable to load font {fname}")


class FontLib:
    def __init__(self):
        self.data = {}

    def load(self):
        # SemiBold rather than Bold: Qt renders bold text on dark backgrounds
        # much heavier than browsers do
        normal, semibold = QFont.Weight.Normal, QFont.Weight.DemiBold
        # name: (weight, italic, underline, strikeout)
        styles = {
            "bold": (semibold, False, False, False),
            "italic": (normal, True, False, False),
            "bolditalic": (semibold, True, False, False),
            "underline": (normal, False, True, False),
            "boldunderline": (semibold, False, True, False),
            "strikeout": (normal, False, False, True),
        }
        for name, (weight, italic, underline, strikeout) in styles.items():
            font = QFont()
            font.setWeight(weight)
            font.setItalic(italic)
            font.setUnderline(underline)
            font.setStrikeOut(strikeout)
            self.data[name] = font

    def __getitem__(self, key):
        if not self.data:
            self.load()
        return self.data.get(key)


#
# Icons - Material Symbols, same as the Nebula web frontend.
# Names map to a symbol, or to (symbol, color) for icons carrying a meaning.
# Names not listed here fall back to images/<name>.png
#

ICON_FONT = "Material Symbols Outlined"
ICON_COLOR = "#d7d4d5"
ICON_SIZE = 20

SYMBOLS: dict[str, str | tuple[str, str]] = {
    "accept": "check",
    "archive": "archive",
    "calendar": "calendar_month",
    "cancel": "close",
    "clear-in": "line_start_circle",
    "clear-marks": "backspace",
    "clear-out": "line_end_circle",
    "create-subclip": "content_cut",
    "dropdown-arrow": "arrow_drop_down",
    "empty-event": "calendar_add_on",
    "fast-backward": "skip_previous",
    "fast-forward": "skip_next",
    "goto-in": "first_page",
    "goto-out": "last_page",
    "lead-in": "vertical_align_top",
    "lead-out": "vertical_align_bottom",
    "live": "live_tv",
    "manage-subclips": "list",
    "mark-in": "line_start",
    "mark-out": "line_end",
    "mcr": "tune",
    "next": "chevron_right",
    "next-more": "keyboard_double_arrow_right",
    "now": "my_location",
    "pause": "pause",
    "placeholder": "crop_free",
    "play": "play_arrow",
    "plugins": "extension",
    "previous": "chevron_left",
    "previous-more": "keyboard_double_arrow_left",
    "qc_new": ("radio_button_unchecked", "#9c9c9c"),
    "qc_failed": ("error", "#ff2404"),
    "qc_passed": ("check_circle", "#fcde00"),
    "qc_rejected": ("cancel", "#ff2404"),
    "qc_approved": ("verified", "#5fff5f"),
    "refresh": "refresh",
    "restore-marks": "undo",
    "save-marks": "save",
    "search": "search",
    "set-poster": "image",
    "show-runs": "history",
    "smallarrow-down": "arrow_drop_down",
    "smallarrow-up": "arrow_drop_up",
    "star": ("star", "#fcde00"),
    "trash": "delete",
    "unstar": ("star", "#6b6b6b"),
}


def get_symbol(name: str) -> QPixmap | None:
    base = name.removesuffix("-sm")
    spec = SYMBOLS.get(base)
    if spec is None:
        return None
    symbol, color = spec if isinstance(spec, tuple) else (spec, ICON_COLOR)
    size = 16 if name.endswith("-sm") else ICON_SIZE
    app = QGuiApplication.instance()
    dpr = app.devicePixelRatio() if app else 1.0

    pixmap = QPixmap(round(size * dpr), round(size * dpr))
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(Qt.GlobalColor.transparent)
    font = QFont(ICON_FONT)
    font.setPixelSize(size)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, symbol)
    painter.end()
    return pixmap


def get_pix(name):
    if not name:
        return None
    if (symbol := get_symbol(name)) is not None:
        return symbol
    if name.startswith("folder_"):
        id_folder = int(name.lstrip("folder_"))
        icn = QPixmap(12, 12)
        try:
            color: str | int = firefly.settings.get_folder(id_folder).color
        except KeyError:
            color = 0xAAAAAA
        icn.fill(QColor(color))
        return icn
    pixmap = QPixmap(f":/images/{name}.png")
    if not pixmap.width():
        pix_file = os.path.join(app_dir, "images", f"{name}.png")
        if os.path.exists(pix_file):
            return QPixmap(pix_file)
    return None


class PixLib(dict[str, QPixmap | None]):
    def __call__(self, key):
        return self[key]

    def __getitem__(self, key):
        if key not in self:
            self[key] = get_pix(key)
        return self.get(key, None)


fontlib = FontLib()
pixlib = PixLib()
