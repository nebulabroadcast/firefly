Firefly
=======

![GitHub release (latest by date)](https://img.shields.io/github/v/release/nebulabroadcast/firefly?style=for-the-badge)
![Maintenance](https://img.shields.io/maintenance/yes/2023?style=for-the-badge)
![Last commit](https://img.shields.io/github/last-commit/nebulabroadcast/firefly?style=for-the-badge)
![Python version](https://img.shields.io/badge/python-3.10-blue?style=for-the-badge)

Firefly is a desktop client application for [Nebula](https://github.com/nebulabroadcast/nebula) broadcast automation system.

Installation
------------

### Linux

 - Install Python 3.10+ and Poetry.
 - Clone this repository.
 - Run `poetry install` to install dependencies.
 - Run `poetry run python -m firefly` to start the application.

The following packages are also needed, in case you don't have them already installed,
run `sudo apt install libmpv1 libxcb-util1` on Ubuntu or `sudo apt install libmpv1 libxcb-util0` on Debian.

### Windows

Latest binary release is available on [nebulabroadcast/firefly](https://github.com/nebulabroadcast/firefly/releases)
GitHub releases page.

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

> Have you tried turning it off and on again?

In most cases, this helps. If the application worked and suddenly it is not possible
to start, try to delete `ffdata` files in its directory and start it again.
