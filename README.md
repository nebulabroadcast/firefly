Firefly
=======

![GitHub release (latest by date)](https://img.shields.io/github/v/release/nebulabroadcast/firefly?style=for-the-badge)
![Maintenance](https://img.shields.io/maintenance/yes/2024?style=for-the-badge)
![Last commit](https://img.shields.io/github/last-commit/nebulabroadcast/firefly?style=for-the-badge)
![Python version](https://img.shields.io/badge/python-3.10--3.14-blue?style=for-the-badge)

Firefly is a desktop client application for [Nebula](https://github.com/nebulabroadcast/nebula) broadcast automation system.

Installation
------------

### Running from source (all platforms)

 - Install [uv](https://docs.astral.sh/uv/) (it installs a suitable Python 3.10 - 3.14 if needed).
 - Clone this repository.
 - Run `make run` (or `uv run python -m firefly`) to start the application.

Video preview uses the FFmpeg backend bundled with PySide6, no extra media libraries are needed.
On Linux under X11, Qt may need `libxcb-cursor0` (`sudo apt install libxcb-cursor0`).

### Binaries (Windows, Linux)

Latest binary releases are available on [nebulabroadcast/firefly](https://github.com/nebulabroadcast/firefly/releases)
GitHub releases page.

### Building binaries

Run `make build` to create a single-file executable with PyInstaller in `dist/`,
together with the `images`, `fonts` and `skin.css` it needs next to it.
`make build_windows` / `make build_linux` also pack it into a zip / tarball.

Configuration
-------------

Edit **settings.json** file to set your server address and site name.

```json
{
    "sites"  : [{
        "name" : "nebula",
        "host" : "https://nebula.example.com"
    }]
}
```

It is possible to specify more than one site in the `settings.json` file.
In that case, a dialog window pops up when the application starts and a you may select the site for this session.

Usage
-----

[Introduction to Firefly](https://nebulabroadcast.com/doc/nebula/firefly-intro.html)

### Troubleshooting

*Have you tried turning it off and on again?*

In most cases, this helps. If the application worked and suddenly it is not possible
to start, try to delete `ffdata` files in its directory and start it again.
