from firefly.qt import QMessageBox
from firefly.version import FIREFLY_VERSION

ABOUT_TEXT = """
<b>Firefly - Nebula broadcast automation system client application</b>
<br><br>
Named after American space Western drama television series which ran from 2002–2003,
created by writer and director Joss Whedon
<br><br>
Firefly is free software;
you can redistribute it and/or modify it under the terms of the GNU General Public
License as published by the Free Software Foundation;
either version 3 of the License, or (at your option) any later version.
<br><br>
For more information visit
<a href="https://nebulabroadcast.com" style="color: #009fbc;">
    https://nebulabroadcast.com
</a>
"""


def show_about_dialog(parent):
    QMessageBox.about(parent, f"Firefly {FIREFLY_VERSION}", ABOUT_TEXT)
