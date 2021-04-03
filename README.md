Firefly
=======

Firefly is a desktop client application for [Nebula](https://github.com/nebulabroadcast/nebula) broadcast automation system.


Installation
------------

### Linux

Install **python3** and **python3-pip** packages and then install requiered libraries using
following command:

```
sudo pip3 install PyQT5 websocket-client
```

For video playback, you will also need **libmpv1** package.

### Windows

Latest binary release is available on [nebulabroadcast/firefly](https://github.com/nebulabroadcast/firefly/releases)
GitHub releases page.

[Microsoft Visual C++ 2015 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=52685)
is required to run this application.

Configuration
-------------

Edit **settings.json** file to set your server address and site name.

```json
{
    "sites"  : [{
        "site_name" : "nebulatv",
        "hub" : "https://nebulatv.example.com"
    }]
}
```

It is possible to specify more than one site in the `settings.json` file.
In that case, a dialog window pops up when the application is started and a site may be selected for this session.

`site_name` argument can be used as an identifier for different configurations of the same site and its value
is updated when server settings are loaded.

Usage
-----

[Introduction to Firefly](https://nebulabroadcast.com/doc/nebula/firefly-intro.html)

### Troubleshooting

> Have you tried turning it off and on again?

In most cases, this helps. If the application worked and suddenly it is not possible
to start, try to delete `ffdata` files in its directory and start it again.
