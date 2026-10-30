__all__ = ["VideoPlayer"]

import os

# Qt Multimedia (FFmpeg backend bundled with PySide6) by default.
# FIREFLY_PLAYER=mpv switches back to the libmpv based player.
if os.environ.get("FIREFLY_PLAYER") == "mpv":
    from firefly.proxyplayer.videoplayer import VideoPlayer
else:
    from firefly.proxyplayer.qtplayer import VideoPlayer
