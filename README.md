Firefly
=======

![GitHub release (latest by date)](https://img.shields.io/github/v/release/nebulabroadcast/firefly?style=for-the-badge)
![Maintenance](https://img.shields.io/maintenance/yes/2022?style=for-the-badge)
![Last commit](https://img.shields.io/github/last-commit/immstudios/nebula?style=for-the-badge)
![Python version](https://img.shields.io/badge/python-3.8-blue?style=for-the-badge)

Firefly is a desktop client application for [Nebula](https://github.com/nebulabroadcast/nebula) broadcast automation system.

Installation
------------

### Linux

Install **python3** and **python3-pip** packages and then install requiered libraries using
following command:

```
sudo pip3 install PyQT5 websocket-client
```

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
        "site_name" : "nebula",
        "hub" : "https://nebula.example.com"
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
